import re


# Interjecciones universales (cortas, no semánticas)
INTERJECTIONS = {
    # inglés / general
    "uh", "um", "eh", "oh", "ah", "hmm", "hm",
    # español
    "ah", "oh", "mmm",
    # francés
    "euh",
    # alemán
    "äh",
}


def es_dialogo_trivial(dialogo: str) -> bool:
    t = dialogo.strip()

    if not t:
        return True

    # 1️⃣ Muy corto
    if len(t) <= 1:
        return True

    # 2️⃣ Solo puntuación / pausas
    if re.fullmatch(r"[.!?…·,;:¡¿\-–—]+", t):
        return True

    # 3️⃣ Repetición del mismo carácter (mmm, aaa, ???)
    if len(set(t.lower())) == 1:
        return True

    # 4️⃣ Interjecciones conocidas
    if t.lower() in INTERJECTIONS:
        return True

    return False


def detectar_speaker_inline(texto: str, known_names=None):
    """
    Detecta speaker pegado al inicio del texto.
    Ejemplos válidos:
    - AlexHello
    - Alex: Hello
    - Alex, hello
    - Alex… hi
    """
    if not texto or not known_names:
        return None, texto

    t = texto.strip()

    for name in known_names:
        if t.startswith(name) and len(t) > len(name):
            resto = t[len(name):].lstrip(" .,:;!?…")
            if resto:
                return name, resto.strip()

    return None, texto
