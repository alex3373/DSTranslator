import re


def contiene_japones(texto: str) -> bool:
    return any(
        '\u3040' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9faf'
        for c in texto
    )


def es_dialogo_trivial(dialogo: str) -> bool:
    t = dialogo.strip("「」『』 ")

    if len(t) <= 1:
        return True

    if re.fullmatch(r"[…。・]+", t):
        return True

    if re.fullmatch(r"[！？!?]+", t):
        return True

    if re.fullmatch(r"[っッ]+", t):
        return True

    return False


def detectar_speaker_inline(dialogo: str, known_names=None):
    """
    Detecta speaker pegado al inicio:
    奈緒子「...」
    奈緒子…うん
    """
    if not dialogo:
        return None, dialogo

    t = dialogo.strip("「」『』")

    m = re.match(r'^([ぁ-んァ-ヶー一-龯]{2,10})([…。！？、])(.+)?', t)
    if not m:
        return None, dialogo

    name = m.group(1)
    if known_names and name not in known_names:
        return None, dialogo

    resto = t[len(name):].lstrip("…。！？、")
    return name, resto.strip()
