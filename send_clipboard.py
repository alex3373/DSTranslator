import asyncio
import threading
import logging
from flask import Flask, jsonify

from deepseek_client import DeepSeekClient
from translation_cache import TranslationCache
from sqlite_store import SQLiteTranslationStore
from speech_buffer import SpeechBuffer
from characters import KNOWN_CHARACTERS

from translation_worker import TranslationWorker
from clipboard_watcher import ClipboardWatcher

# ==========================
# CONFIG
# ==========================
CLIPBOARD_POLL = 0.1
PORT = 5000
PENDING_MAX = 20

# ==========================
# Flask
# ==========================
app = Flask(__name__)
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

# ==========================
# Componentes
# ==========================
deepseek = DeepSeekClient()
cache = TranslationCache(max_size=500)
sqlite_cache = SQLiteTranslationStore()

# ✅ BATCHING FINAL:
# - cortas (<10) se juntan hasta 3
# - timeout MÁS ALTO para que alcance a agrupar cuando el clipboard llega con delay
speech_buffer = SpeechBuffer(timeout=4.5, short_threshold=10, short_max_lines=3)

worker = TranslationWorker(
    deepseek=deepseek,
    cache=cache,
    sqlite_cache=sqlite_cache,
    known_characters=KNOWN_CHARACTERS,
    pending_max=PENDING_MAX
)

# ==========================
# Async loop dedicado
# ==========================
loop = asyncio.new_event_loop()

def start_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=start_loop, daemon=True).start()

# ==========================
# Clipboard watcher
# ==========================
watcher = ClipboardWatcher(
    speech_buffer=speech_buffer,
    worker=worker,
    loop=loop,
    poll=CLIPBOARD_POLL
)

# ==========================
# API
# ==========================
@app.route("/api/translation", methods=["GET"])
def get_translation():
    return jsonify(worker.get_current_translation())

@app.route("/api/reset", methods=["POST"])
def reset():
    worker.reset_state()
    speech_buffer.force_flush()
    return jsonify({"status": "reset"})

@app.route("/api/cache/stats", methods=["GET"])
def get_cache_stats():
    return jsonify(cache.get_stats())


@app.route("/api/history", methods=["GET"])
def get_history():
    return jsonify(sqlite_cache.get_last(limit=30))

# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    threading.Thread(target=watcher.start, daemon=True).start()
    print(f"[Server] http://127.0.0.1:{PORT}")
    app.run(host="0.0.0.0", port=PORT, threaded=True, debug=False)

