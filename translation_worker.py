import asyncio
import threading
import time
from telemetry import tracer, cache_hits, cache_misses, translations_total, queue_size

from utils_text import (
    es_dialogo_trivial,
    detectar_speaker_inline
)


class TranslationWorker:
    """
    Maneja:
    - busy + cola (pending_texts)
    - cache RAM + sqlite
    - mini_context
    - llamada DeepSeek
    - current_translation (para API Flask / overlay)

    NUEVO:
    - context_active: True/False cuando se usó mini-context en la última traducción
      (para mostrar indicador en el logo/overlay)
    """

    def __init__(
        self,
        deepseek,
        cache,
        sqlite_cache,
        KNOWN_NAMES,
        pending_max=20
    ):
        self.deepseek = deepseek
        self.cache = cache
        self.sqlite_cache = sqlite_cache
        self.KNOWN_NAMES = KNOWN_NAMES
        self.pending_max = pending_max

        self.translation_lock = threading.Lock()
        self.current_translation = {
            "text": "",
            "id": 0,
            "busy": False,
            "context_active": False,
        }

        self.pending_texts = []
        self.mini_context = []

    # ==========================
    # ESTADO ACTUAL (API)
    # ==========================
    def get_current_translation(self):
        with self.translation_lock:
            return dict(self.current_translation)

    def reset_state(self):
        with self.translation_lock:
            self.current_translation.update({
                "text": "",
                "id": 0,
                "busy": False,
                "context_active": False,
            })
        self.pending_texts.clear()
        self.mini_context.clear()

    # ==========================
    # CACHE DIRECTO (para watcher)
    # ==========================
    def get_cached_translation(self, texto: str):
        cached = self.cache.get(texto)
        if cached:
            return cached

        cached = self.sqlite_cache.get(texto)
        if cached:
            self.cache.set(texto, cached)
            return cached

        return None

    def set_current_translation(self, translated: str):
        with self.translation_lock:
            self.current_translation["text"] = translated
            self.current_translation["id"] += 1
            self.current_translation["context_active"] = False

    # ==========================
    # WORKER ASYNC
    # ==========================
    async def traducir_texto(self, texto: str):
        # ==========================
        # BUSY + COLA
        # ==========================
        with self.translation_lock:
            if self.current_translation["busy"]:
                self.pending_texts.append(texto)
                if len(self.pending_texts) > self.pending_max:
                    self.pending_texts.pop(0)
                queue_size.add(1)
                print(f"[Queue] Busy → encolado ({len(self.pending_texts)}): {texto[:60]}")
                return

            self.current_translation["busy"] = True

        with tracer.start_as_current_span("traducir_texto") as span:
            span.set_attribute("texto.length", len(texto))

            try:
                # ======================
                # SPEAKER (informativo)
                # ======================
                speaker, dialogo = detectar_speaker_inline(
                    texto,
                    known_names=self.KNOWN_NAMES
                )

                if not speaker:
                    speaker, dialogo = self.deepseek._extract_speaker(texto)

                print(f"[Speaker] {speaker if speaker else '(narración)'}")
                if speaker:
                    span.set_attribute("speaker", speaker)

                # ======================
                # FILTRO GLOBAL
                # ======================
                lineas = [l for l in texto.split("\n") if l.strip()]
                if len(lineas) == 1 and es_dialogo_trivial(dialogo):
                    print(f"[Skip] Trivial: {dialogo}")
                    span.set_attribute("resultado", "trivial_skip")
                    with self.translation_lock:
                        self.current_translation["context_active"] = False
                    return

                # ======================
                # CACHE RAM
                # ======================
                cached = self.cache.get(texto)
                if cached:
                    print("[Cache] 💾 RAM HIT")
                    cache_hits.add(1, {"type": "ram"})
                    span.set_attribute("resultado", "cache_ram")
                    with self.translation_lock:
                        self.current_translation["text"] = cached
                        self.current_translation["id"] += 1
                        self.current_translation["context_active"] = False
                    return

                # ======================
                # CACHE SQLITE
                # ======================
                cached = self.sqlite_cache.get(texto)
                if cached:
                    print("[Cache] 💿 SQLITE HIT")
                    cache_hits.add(1, {"type": "sqlite"})
                    span.set_attribute("resultado", "cache_sqlite")
                    self.cache.set(texto, cached)
                    with self.translation_lock:
                        self.current_translation["text"] = cached
                        self.current_translation["id"] += 1
                        self.current_translation["context_active"] = False
                    return

                # ======================
                # CACHE MISS → API
                # ======================
                cache_misses.add(1)
                span.set_attribute("resultado", "api_call")

                # ======================
                # CONTEXTO (mini-context)
                # ======================
                use_context = len(texto) > 25 and len(self.mini_context) > 0
                context_text = "\n".join(self.mini_context[-5:]) if use_context else ""

                with self.translation_lock:
                    self.current_translation["context_active"] = use_context

                if use_context:
                    print(f"[Context] ✅ ON | mini_context={len(self.mini_context)} | send_lines={min(5, len(self.mini_context))}")
                else:
                    print(f"[Context] ⛔ OFF | mini_context={len(self.mini_context)}")

                span.set_attribute("context_active", use_context)

                # ======================
                # API DeepSeek
                # ======================
                t_start = time.time()
                resultado = ""
                async for chunk in self.deepseek.translate_stream(
                    text=texto,
                    context=context_text
                ):
                    resultado += chunk

                t_elapsed = time.time() - t_start
                span.set_attribute("translation.duration_ms", round(t_elapsed * 1000))

                resultado_final = resultado.strip()

                with self.translation_lock:
                    self.current_translation["text"] = resultado_final
                    self.current_translation["id"] += 1

                self.cache.set(texto, resultado_final)
                self.sqlite_cache.set(texto, resultado_final)

                translations_total.add(1)
                print(f"[API] 🌐 NEW ({round(t_elapsed*1000)}ms):\n{texto}\n→\n{resultado_final}\n")

                # ======================
                # MINI CONTEXTO (guardar)
                # ======================
                if not es_dialogo_trivial(dialogo):
                    self.mini_context.append(resultado_final)
                    if len(self.mini_context) > 8:
                        self.mini_context.pop(0)

            except Exception as e:
                print(f"[Worker] Error: {e}")
                span.record_exception(e)
                with self.translation_lock:
                    self.current_translation["text"] = f"[Error: {e}]"
                    self.current_translation["id"] += 1
                    self.current_translation["context_active"] = False

            finally:
                with self.translation_lock:
                    self.current_translation["busy"] = False

                queue_size.add(-1) if self.pending_texts else None

                next_text = None
                with self.translation_lock:
                    if self.pending_texts:
                        next_text = self.pending_texts.pop(0)

                if next_text:
                    print(f"[Queue] Dequeue → traduciendo: {next_text[:60]}")
                    asyncio.create_task(self.traducir_texto(next_text))