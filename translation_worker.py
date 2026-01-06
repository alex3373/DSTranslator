import asyncio
import threading

from utils_text import (
    contiene_japones,
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
    - current_translation (para API Flask)

    El ClipboardWatcher:
    - decide batching / directo / trivial
    - puede consultar cache inmediato (get_cached_translation)
    """

    def __init__(
        self,
        deepseek,
        cache,
        sqlite_cache,
        known_characters,
        pending_max=20
    ):
        self.deepseek = deepseek
        self.cache = cache
        self.sqlite_cache = sqlite_cache
        self.known_characters = known_characters
        self.pending_max = pending_max

        self.translation_lock = threading.Lock()
        self.current_translation = {
            "text": "",
            "id": 0,
            "busy": False
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
                "busy": False
            })
        self.pending_texts.clear()
        self.mini_context.clear()

    # ==========================
    # CACHE DIRECTO (para watcher)
    # ==========================
    def get_cached_translation(self, texto_jp: str):
        """
        Devuelve traducción si está en cache (RAM o SQLite).
        NO dispara requests.
        """
        # RAM primero
        cached = self.cache.get(texto_jp)
        if cached:
            return cached

        # SQLite después
        cached = self.sqlite_cache.get(texto_jp)
        if cached:
            # reinyectar en RAM
            self.cache.set(texto_jp, cached)
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

    # ==========================
    # WORKER ASYNC
    # ==========================
    async def traducir_texto(self, texto_jp: str):
        # ==========================
        # BUSY + COLA
        # ==========================
        with self.translation_lock:
            if self.current_translation["busy"]:
                self.pending_texts.append(texto_jp)
                if len(self.pending_texts) > self.pending_max:
                    self.pending_texts.pop(0)

                print(f"[Queue] Busy → encolado ({len(self.pending_texts)}): {texto_jp[:60]}")
                return

            self.current_translation["busy"] = True

        try:
            # ======================
            # SPEAKER (informativo)
            # ======================
            speaker, dialogo = detectar_speaker_inline(
                texto_jp,
                known_names=self.known_characters
            )

            if not speaker:
                speaker, dialogo = self.deepseek._extract_speaker(texto_jp)

            print(f"[Speaker] {speaker if speaker else '(narración)'}")

            # ======================
            # FILTRO GLOBAL
            # (no skipear si bloque tiene >1 línea)
            # ======================
            lineas = [l for l in texto_jp.split("\n") if l.strip()]
            if len(lineas) == 1:
                if es_dialogo_trivial(dialogo):
                    print(f"[Skip] Trivial: {dialogo}")
                    return

                if not contiene_japones(dialogo):
                    print(f"[Skip] Sin japonés: {dialogo}")
                    return

            # ======================
            # CACHE RAM
            # ======================
            cached = self.cache.get(texto_jp)
            if cached:
                print("[Cache] 💾 RAM HIT")
                with self.translation_lock:
                    self.current_translation["text"] = cached
                    self.current_translation["id"] += 1
                return

            # ======================
            # CACHE SQLITE
            # ======================
            cached = self.sqlite_cache.get(texto_jp)
            if cached:
                print("[Cache] 💿 SQLITE HIT")
                self.cache.set(texto_jp, cached)
                with self.translation_lock:
                    self.current_translation["text"] = cached
                    self.current_translation["id"] += 1
                return

            # ======================
            # CONTEXTO
            # ======================
            use_context = len(texto_jp) > 25 and len(self.mini_context) > 0
            context_text = "\n".join(self.mini_context[-5:]) if use_context else ""

            # ======================
            # API DeepSeek
            # ======================
            resultado = ""
            async for chunk in self.deepseek.translate_stream(
                text_jp=texto_jp,
                context=context_text
            ):
                resultado += chunk

            resultado_final = resultado.strip()

            with self.translation_lock:
                self.current_translation["text"] = resultado_final
                self.current_translation["id"] += 1

            self.cache.set(texto_jp, resultado_final)
            self.sqlite_cache.set(texto_jp, resultado_final)

            print(f"[API] 🌐 NEW:\n{texto_jp}\n→\n{resultado_final}\n")

            # ======================
            # MINI CONTEXTO
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
