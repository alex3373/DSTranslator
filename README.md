# DSTranslator

Backend pipeline for **LLM-assisted sequential text processing**, designed to handle structured or fragmented text reliably while preserving order, reducing redundant API calls, and minimizing information loss.

This repository contains the **backend engine** of the system.  
For the desktop overlay and local UI, see **[overlay-multideep](https://github.com/alex3373/overlay-multideep)**.

---

## Overview

DSTranslator is a backend-oriented text processing pipeline built to support continuous or fragmented text flows when interacting with language models.

Instead of sending raw text directly to an LLM, the system introduces a controlled processing layer that:

- classifies incoming text
- batches short fragments when appropriate
- avoids duplicate processing
- preserves logical order
- reuses cached results
- applies lightweight contextual assistance only when useful

The goal is to make LLM-based translation or text transformation **more reliable, cost-aware, and resilient** for sequential content.

---

## Key Features

- **Sequential text processing pipeline**
- **Input classification** for trivial, short, and long text
- **Buffering and batching** for fragmented input
- **RAM cache + persistent SQLite cache**
- **Deduplication and text normalization**
- **Mini-context support** for better continuity across lines
- **Speaker detection support** for dialogue-oriented content
- **Async task handling** with controlled pending queue
- **Local HTTP API** for real-time integration with external interfaces

---

## Architecture

DSTranslator is designed as a modular backend composed of several responsibilities:

- **Clipboard/input watcher**
- **Speech/text buffer**
- **Translation worker**
- **LLM client integration**
- **In-memory cache**
- **Persistent SQLite store**
- **Configuration manager**
- **HTTP API layer (Flask)**

This design allows the backend to remain decoupled from the UI, making it reusable for overlays, desktop tools, or other local clients.

---

## Tech Stack

- **Python**
- **AsyncIO**
- **Flask**
- **SQLite**
- **aiohttp**
- **Regex / text normalization utilities**

LLM integrations currently include:
- **DeepSeek**
- **ChatGPT-compatible workflows**

---

## Use Cases

Although originally developed around real-time text processing, the architecture is applicable to broader scenarios such as:

- translation pipelines
- localization workflows
- dialogue/narrative processing
- log or text stream analysis
- sequential content transformation

---

## Related Repository

Desktop overlay and local UI for this backend:  
➡ **[overlay-multideep](https://github.com/alex3373/overlay-multideep)**

---

## Current Status

The backend is functional and modular.  
Packaging/distribution improvements and additional interface layers may be expanded further.

---

## Author

**Alexis Córdova Díaz**  
Full Stack Developer (Backend-oriented)  

- GitHub: [alex3373](https://github.com/alex3373)
- LinkedIn: [alexis-andres-cordova](https://www.linkedin.com/in/alexis-andres-cordova)
