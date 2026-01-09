import time


class SpeechBuffer:
    """
    Buffer SOLO para líneas cortas.
    No decide traducción, solo acumula.
    """

    def __init__(self, timeout=1.3, short_threshold=10, short_max_lines=3):
        self.timeout = timeout
        self.short_threshold = short_threshold
        self.short_max_lines = short_max_lines

        self.buffer = []
        self.last_time = 0.0

    def is_short(self, text: str) -> bool:
        return len(text.strip()) < self.short_threshold

    def push(self, text: str):
        now = time.time()
        text = text.strip()

        if not text:
            return None

        if not self.is_short(text):
            return None

        if not self.buffer:
            self.buffer.append(text)
            self.last_time = now
            return None

        self.buffer.append(text)
        self.last_time = now

        if len(self.buffer) >= self.short_max_lines:
            return self.flush()

        return None

    def flush(self):
        if not self.buffer:
            return None

        combined = self._smart_join(self.buffer)
        self.buffer.clear()
        self.last_time = 0.0
        return combined

    def force_flush(self):
        return self.flush()

    def get_current(self):
        if not self.buffer:
            return None
        return self._smart_join(self.buffer)

    def _smart_join(self, parts):
        clean = [p.strip() for p in parts if p and p.strip()]
        return "\n".join(clean)
