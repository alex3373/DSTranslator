import asyncio
import threading
import logging
from flask import Flask, jsonify, request

from config_manager import ConfigManager
from deepseek_client import DeepSeekClient
from translation_cache import TranslationCache
from sqlite_store import SQLiteTranslationStore
from speech_buffer import SpeechBuffer
from names import KNOWN_NAMES

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
# Configuración usuario
# ==========================
config = ConfigManager()

api_key = config.get_api_key()
target_language = config.get_target_language()

deepseek = None
if api_key:
    deepseek = DeepSeekClient(
        api_key=api_key,
        target_language=target_language
    )
else:
    print("[Config] ⚠ No API key configurada. Esperando configuración del usuario.")


cache = TranslationCache(max_size=500)
sqlite_cache = SQLiteTranslationStore()

# ✅ BATCHING FINAL:
# - cortas (<10) se juntan hasta 3
# - timeout MÁS ALTO para que alcance a agrupar cuando el clipboard llega con delay
speech_buffer = SpeechBuffer(
    timeout=4.5,
    short_threshold=10,
    short_max_lines=3
)

worker = TranslationWorker(
    deepseek=deepseek,
    cache=cache,
    sqlite_cache=sqlite_cache,
    KNOWN_NAMES=KNOWN_NAMES,
    pending_max=PENDING_MAX
)

# ==========================
# Async loop dedicado
# ==========================
loop = asyncio.new_event_loop()

def start_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(
    target=start_loop,
    daemon=True
).start()

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

@app.route("/api/config", methods=["POST"])
def save_config():
    data = request.json or {}

    # ==========================
    # Leer datos
    # ==========================
    api_key = (data.get("deepseek_api_key") or "").strip()
    target_language = (data.get("target_language") or "English").strip()

    # ==========================
    # Validación básica
    # ==========================
    if not api_key:
        return jsonify({"error": "API key vacía"}), 400

    # 🔒 Blindaje: si viene como VAR=sk-..., extraer solo el valor
    if "=" in api_key:
        api_key = api_key.split("=", 1)[1].strip()

    if not api_key:
        return jsonify({"error": "API key inválida"}), 400

    # ==========================
    # Guardar configuración
    # ==========================
    config.save({
        "deepseek_api_key": api_key,
        "target_language": target_language
    })

    # ==========================
    # 🔥 HOT RELOAD DEL CLIENTE
    # ==========================
    global deepseek
    global worker

    try:
        deepseek = DeepSeekClient(
            api_key=api_key,
            target_language=target_language
        )

        worker.deepseek = deepseek

        print("[Config] ✅ API key cargada en caliente")

    except Exception as e:
        print("[Config] ❌ Error creando DeepSeekClient:", e)
        return jsonify({
            "error": "API key inválida o error al inicializar cliente"
        }), 400

    return jsonify({"status": "ok"})



# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    threading.Thread(
        target=watcher.start,
        daemon=True
    ).start()

    print(f"[Server] http://127.0.0.1:{PORT}")
    app.run(
        host="0.0.0.0",
        port=PORT,
        threaded=True,
        debug=False
    )
