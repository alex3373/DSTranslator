import time
import pyperclip
import asyncio
import re


class ClipboardWatcher:
    def __init__(self, speech_buffer, worker, loop, poll=0.1, max_len=500):
        self.speech_buffer = speech_buffer
        self.worker = worker
        self.loop = loop
        self.poll = poll
        self.max_len = max_len

        self.last_clipboard = None
        self.last_text = None  # ← antes last_japanese

    # ==========================
    # CLASIFICADOR TRIVIAL (multi-idioma)
    # ==========================
    def is_trivial(self, text: str) -> bool:
        t = text.strip()
        if not t:
            return True
        if len(t) <= 1:
            return True
        if re.fullmatch(r"[.!?…·,;:¡¿\-–—]+", t):
            return True
        return False

    # ==========================
    # MAIN LOOP
    # ==========================
    def start(self):
        print("[Clipboard] escuchando...")

        while True:
            try:
                texto = pyperclip.paste()

                if not texto or texto == self.last_clipboard or len(texto) > self.max_len:
                    self.try_force_flush()
                    time.sleep(self.poll)
                    continue

                self.last_clipboard = texto
                texto_limpio = texto.strip()

                # evita spam exacto
                if texto_limpio == self.last_text:
                    self.try_force_flush()
                    time.sleep(self.poll)
                    continue

                self.last_text = texto_limpio

                # 🔴 TRIVIAL → NO TRADUCIR
                if self.is_trivial(texto_limpio):
                    self.speech_buffer.force_flush()
                    time.sleep(self.poll)
                    continue

                # 🟢 CACHE HIT → inmediato
                cached = self.worker.get_cached_translation(texto_limpio)
                if cached:
                    print("[Cache] HIT → inmediato")
                    self.speech_buffer.force_flush()
                    self.worker.set_current_translation(cached)
                    time.sleep(self.poll)
                    continue

                # 🔵 LARGA
                if not self.speech_buffer.is_short(texto_limpio):
                    pending = self.speech_buffer.get_current()

                    if pending:
                        combined = pending + "\n" + texto_limpio
                        self.speech_buffer.force_flush()
                        asyncio.run_coroutine_threadsafe(
                            self.worker.traducir_texto(combined),
                            self.loop
                        )
                    else:
                        asyncio.run_coroutine_threadsafe(
                            self.worker.traducir_texto(texto_limpio),
                            self.loop
                        )

                # 🟡 CORTA
                else:
                    flushed = self.speech_buffer.push(texto_limpio)
                    if flushed:
                        asyncio.run_coroutine_threadsafe(
                            self.worker.traducir_texto(flushed),
                            self.loop
                        )

            except Exception as e:
                print(f"[Clipboard] Error: {e}")

            self.try_force_flush()
            time.sleep(self.poll)

    # ==========================
    # FORCE FLUSH
    # ==========================
    def try_force_flush(self):
        pending = self.speech_buffer.get_current()
        if not pending:
            return

        now = time.time()
        if (now - self.speech_buffer.last_time) > (self.speech_buffer.timeout + 0.15):
            flushed = self.speech_buffer.force_flush()
            if flushed:
                asyncio.run_coroutine_threadsafe(
                    self.worker.traducir_texto(flushed),
                    self.loop
                )
