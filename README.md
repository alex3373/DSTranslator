# DSTranslator

**English**  
Backend pipeline for **LLM-assisted sequential text processing**, designed to translate and process fragmented or context-sensitive text reliably while preserving order, reducing redundant API calls, and improving consistency.

This repository contains the **backend engine** of the system.  
For the desktop overlay and local UI, see **[overlay-multideep](https://github.com/alex3373/overlay-multideep)**.

**Español**  
Pipeline backend para **procesamiento secuencial de texto asistido por LLM**, diseñado para traducir y procesar texto fragmentado o sensible al contexto de forma confiable, preservando el orden, reduciendo llamadas redundantes a la API y mejorando la consistencia.

Este repositorio contiene el **motor backend** del sistema.  
Para el overlay de escritorio y la interfaz local, revisa **[overlay-multideep](https://github.com/alex3373/overlay-multideep)**.

---

## Overview / Descripción general

**English**  
DSTranslator was built to improve translation quality and reduce cost when working with text that does not arrive as clean, complete paragraphs.

Instead of sending raw text directly to an LLM, the system introduces a controlled processing layer that can classify inputs, batch short fragments, preserve logical order, reuse cached results, and provide lightweight contextual assistance when needed.

This makes it useful for workflows where text is fragmented, sequential, dialogue-heavy, or ambiguous.

**Español**  
DSTranslator fue creado para mejorar la calidad de traducción y reducir costos cuando se trabaja con texto que no llega como párrafos limpios y completos.

En lugar de enviar texto crudo directamente a un LLM, el sistema agrega una capa de procesamiento controlada que puede clasificar entradas, agrupar fragmentos cortos, preservar el orden lógico, reutilizar resultados en caché y aportar contexto ligero cuando hace falta.

Esto lo vuelve útil para flujos donde el texto llega fragmentado, de forma secuencial, con mucho diálogo o con ambigüedad contextual.

---

## Purpose / Propósito

**English**  
The project focuses on making LLM-based text translation and transformation more practical in real-world conditions, especially when:

- text arrives in short fragments
- the input contains dialogue or narration
- names should not be translated incorrectly
- repeated requests would increase API cost unnecessarily
- order and continuity matter

DSTranslator supports known-name lists to help distinguish speakers from narration, improving translation consistency and avoiding incorrect translation of proper names.

**Español**  
El proyecto se enfoca en hacer más práctico el uso de LLMs para traducción y transformación de texto en condiciones reales, especialmente cuando:

- el texto llega en fragmentos cortos
- la entrada contiene diálogo o narración
- los nombres no deben traducirse incorrectamente
- repetir solicitudes aumentaría el costo de API innecesariamente
- el orden y la continuidad importan

DSTranslator permite registrar listas de nombres conocidos para ayudar a distinguir hablantes de narración, mejorando la consistencia de la traducción y evitando traducir mal nombres propios.

---

## Key Features / Características principales

**English**
- Sequential text processing pipeline
- Input classification for trivial, short, and long text
- Buffering and batching for fragmented input
- RAM cache + persistent SQLite cache
- Deduplication and text normalization
- Mini-context support for continuity across lines
- Speaker-aware prompt assistance
- Known-name registry to preserve proper names
- Async task handling with controlled pending queue
- Local HTTP API for integration with desktop tools or overlays

**Español**
- Pipeline de procesamiento secuencial de texto
- Clasificación de entradas triviales, cortas y largas
- Buffering y batching para entradas fragmentadas
- Caché en RAM + caché persistente en SQLite
- Deduplicación y normalización de texto
- Soporte de mini-contexto para continuidad entre líneas
- Asistencia de prompts sensible al hablante
- Registro de nombres conocidos para preservar nombres propios
- Manejo asíncrono de tareas con cola controlada
- API HTTP local para integración con herramientas de escritorio u overlays

---

## Possible Use Cases / Casos de uso posibles

**English**
- Translation of fragmented dialogue or narrative text
- OCR-assisted translation workflows
- Localization of dialogue-heavy or story-driven content
- Clipboard-based text capture and processing
- Subtitle or caption pre-processing
- Translation support for emails, chat logs, or message drafts
- Cost-aware LLM workflows for repetitive text streams

**Español**
- Traducción de diálogo o texto narrativo fragmentado
- Flujos de traducción asistidos por OCR
- Localización de contenido con mucho diálogo o narrativa
- Captura y procesamiento de texto desde clipboard
- Preprocesamiento de subtítulos o captions
- Soporte de traducción para correos, logs de chat o borradores de mensajes
- Flujos con LLM sensibles a costos para texto repetitivo o secuencial

---

## Architecture / Arquitectura

**English**  
DSTranslator is designed as a modular backend composed of several responsibilities:

- input/clipboard watcher
- speech/text buffer
- translation worker
- LLM client integration
- in-memory cache
- persistent SQLite store
- configuration manager
- local HTTP API layer

This allows the backend to stay decoupled from the UI and be reused by different local interfaces.

**Español**  
DSTranslator está diseñado como un backend modular compuesto por varias responsabilidades:

- watcher de entrada/clipboard
- buffer de texto
- worker de traducción
- integración con cliente LLM
- caché en memoria
- persistencia en SQLite
- administrador de configuración
- capa de API HTTP local

Esto permite que el backend permanezca desacoplado de la UI y pueda reutilizarse desde distintas interfaces locales.

---

## Tech Stack / Tecnologías

**English**
- Python
- AsyncIO
- Flask
- SQLite
- aiohttp
- Regex / text normalization utilities

LLM integrations currently include:
- DeepSeek
- ChatGPT-compatible workflows

**Español**
- Python
- AsyncIO
- Flask
- SQLite
- aiohttp
- Regex / utilidades de normalización de texto

Las integraciones LLM actuales incluyen:
- DeepSeek
- flujos compatibles con ChatGPT

---

## Related Repository / Repositorio relacionado

**English**  
Desktop overlay and local UI for this backend:  
➡ **[overlay-multideep](https://github.com/alex3373/overlay-multideep)**

**Español**  
Overlay de escritorio e interfaz local para este backend:  
➡ **[overlay-multideep](https://github.com/alex3373/overlay-multideep)**

---

## Current Status / Estado actual

**English**  
The backend is functional and modular. It already supports real-time local workflows and can be integrated with desktop interfaces. Packaging and additional UI layers may continue to evolve.

**Español**  
El backend es funcional y modular. Ya soporta flujos locales en tiempo real y puede integrarse con interfaces de escritorio. El empaquetado y capas adicionales de UI pueden seguir evolucionando.

---

## Author / Autor

**Alexis Córdova Díaz**  
Full Stack Developer (Backend-oriented)

- GitHub: [alex3373](https://github.com/alex3373)
- LinkedIn: [alexis-andres-cordova](https://www.linkedin.com/in/alexis-andres-cordova)
Full Stack Developer (Backend-oriented)  

- GitHub: [alex3373](https://github.com/alex3373)
- LinkedIn: [alexis-andres-cordova](https://www.linkedin.com/in/alexis-andres-cordova)
