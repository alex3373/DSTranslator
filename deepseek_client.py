# Versión SIN streaming (multi-idioma)

import os
import re
import aiohttp
from dotenv import load_dotenv

from names import KNOWN_NAMES

load_dotenv()

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


class DeepSeekClient:
    def __init__(self, target_language: str = "English"):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY no definida")

        self.target_language = target_language

        # Separador neutro
        known_list = ", ".join(sorted(KNOWN_NAMES))

        self.system_prompt = (
            "You are a translation engine for narration and dialogue.\n\n"

            "TASK:\n"
            "- Automatically detect the source language.\n"
            f"- Translate the text into {self.target_language}.\n\n"

            "RULES:\n"
            "- A character name at the START of a line is the SPEAKER.\n"
            "- Never guess or invent the speaker.\n"
            "- If [SPEAKER: Name] is provided, use it to understand who is speaking.\n"
            "- If no speaker is given, treat the line as narration.\n"
            "- Character names are never sounds or interjections.\n"
            "- Known character names:\n"
            f"{known_list}\n\n"

            "OUTPUT:\n"
            "- Translate ONLY the dialogue or narration.\n"
            "- Do NOT include the speaker name in the output.\n"
            "- Preserve honorifics (san, chan, kun, senpai, sama).\n"
            "- Preserve emotion and punctuation (…, !, ?, hesitation).\n"
            "- Output ONLY the translation. No comments."
        )

    # ==========================
    # SPEAKER DETECTION 
    # ==========================
    def _extract_speaker(self, text: str):
        text = text.strip()
        if not text:
            return None, text

        # 1️⃣ Name: text (latino)
        m = re.match(r"^([A-Z][a-z]{1,20})[：:]\s*(.+)?", text)
        if m and m.group(1) in KNOWN_NAMES:
            return m.group(1), (m.group(2) or "").strip()

        # Limpieza básica de comillas
        t = text.strip("「」『』\"'")

        # 2️⃣ Nombre en línea separada
        lines = t.split("\n")
        if len(lines) >= 2:
            name = lines[0].strip()
            if name in KNOWN_NAMES:
                return name, "\n".join(lines[1:]).strip()

        # 3️⃣ / 4️⃣ Nombre pegado o con separador
        for name in KNOWN_NAMES:
            if t.startswith(name):
                rest = t[len(name):].lstrip(" :：,")
                if rest:
                    return name, rest.strip()

        return None, text

    # ==========================
    # INTERNAL REQUEST (NO STREAM)
    # ==========================
    async def _request_once(self, payload, headers):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                DEEPSEEK_API_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:

                if resp.status != 200:
                    raise RuntimeError(await resp.text())

                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    # ==========================
    # PUBLIC TRANSLATE (NO STREAM)
    # ==========================
    def translate_stream(self, text: str, context: str = ""):
        async def _gen():
            speaker, dialogue = self._extract_speaker(text)

            use_context = bool(context and dialogue and len(dialogue) > 15)

            messages = []

            messages.append({
                "role": "system",
                "content": self.system_prompt,
                "cache_control": {"type": "ephemeral"}
            })

            if use_context:
                messages.append({
                    "role": "user",
                    "content": f"Previous lines:\n{context}"
                })

            content = dialogue
            if speaker:
                content = f"[SPEAKER: {speaker}]\n{content}"

            messages.append({
                "role": "user",
                "content": content
            })

            payload = {
                "model": "deepseek-chat",
                "stream": False,
                "temperature": 0.25,
                "messages": messages
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            result = await self._request_once(payload, headers)

            if speaker:
                yield f"{speaker}: {result}"
            else:
                yield result

        return _gen()
