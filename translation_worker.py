import asyncio
import threading

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
            "context_active": False,  # ✅ NUEVO: indicador para overlay/logo
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
                "context_active": False,  # ✅ NUEVO
            })
        self.pending_texts.clear()
        self.mini_context.clear()

    # ==========================
    # CACHE DIRECTO (para watcher)
    # ==========================
    def get_cached_translation(self, texto: str):
        """
        Devuelve traducción si está en cache (RAM o SQLite).
        NO dispara requests.
        """
        cached = self.cache.get(texto)
        if cached:
            return cached

        cached = self.sqlite_cache.get(texto)
        if cached:
            self.cache.set(texto, cached)
            return cached

        return None

    def set_current_translation(self, translated: str):
        """
        Actualiza inmediatamente el texto mostrado (sin async).
        Usado solo en cache-hit inmediato desde el watcher.
        """
        with self.translation_lock:
            self.current_translation["text"] = translated
            self.current_translation["id"] += 1
            self.current_translation["context_active"] = False  # cache-hit no usa contexto

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

                print(f"[Queue] Busy → encolado ({len(self.pending_texts)}): {texto[:60]}")
                return

            self.current_translation["busy"] = True

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

            # ======================
            # FILTRO GLOBAL
            # ======================
            lineas = [l for l in texto.split("\n") if l.strip()]
            if len(lineas) == 1 and es_dialogo_trivial(dialogo):
                print(f"[Skip] Trivial: {dialogo}")
                with self.translation_lock:
                    self.current_translation["context_active"] = False
                return

            # ======================
            # CACHE RAM
            # ======================
            cached = self.cache.get(texto)
            if cached:
                print("[Cache] 💾 RAM HIT")
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
                self.cache.set(texto, cached)
                with self.translation_lock:
                    self.current_translation["text"] = cached
                    self.current_translation["id"] += 1
                    self.current_translation["context_active"] = False
                return

            # ======================
            # CONTEXTO (mini-context)
            # ======================
            use_context = len(texto) > 25 and len(self.mini_context) > 0
            context_text = "\n".join(self.mini_context[-5:]) if use_context else ""

            # ✅ NUEVO: flag + log para overlay/logo
            with self.translation_lock:
                self.current_translation["context_active"] = use_context

            if use_context:
                print(f"[Context] ✅ ON | mini_context={len(self.mini_context)} | send_lines={min(5, len(self.mini_context))}")
            else:
                print(f"[Context] ⛔ OFF | mini_context={len(self.mini_context)}")

            # ======================
            # API DeepSeek (NO stream)
            # ======================
            resultado = ""
            async for chunk in self.deepseek.translate_stream(
                text=texto,
                context=context_text
            ):
                resultado += chunk

            resultado_final = resultado.strip()

            with self.translation_lock:
                self.current_translation["text"] = resultado_final
                self.current_translation["id"] += 1
                # context_active ya quedó seteado arriba (y se mantiene para overlay)

            self.cache.set(texto, resultado_final)
            self.sqlite_cache.set(texto, resultado_final)

            print(f"[API] 🌐 NEW:\n{texto}\n→\n{resultado_final}\n")

            # ======================
            # MINI CONTEXTO (guardar)
            # ======================
            if not es_dialogo_trivial(dialogo):
                self.mini_context.append(resultado_final)
                if len(self.mini_context) > 8:
                    self.mini_context.pop(0)

        except Exception as e:
            print(f"[Worker] Error: {e}")
            with self.translation_lock:
                self.current_translation["text"] = f"[Error: {e}]"
                self.current_translation["id"] += 1
                self.current_translation["context_active"] = False

        finally:
            # ======================
            # LIBERAR BUSY
            # ======================
            with self.translation_lock:
                self.current_translation["busy"] = False

            # ======================
            # PROCESAR COLA
            # ======================
            next_text = None
            with self.translation_lock:
                if self.pending_texts:
                    next_text = self.pending_texts.pop(0)

            if next_text:
                print(f"[Queue] Dequeue → traduciendo: {next_text[:60]}")
                asyncio.create_task(self.traducir_texto(next_text))
