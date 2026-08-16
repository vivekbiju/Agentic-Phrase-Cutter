# Stateful Phrase Cutter Agent

An intelligent, stateful video editing agent that ingests video files, transcripts, and word-level speech-to-text timing data (via Whisper), reconciles discrepancies between them, and cuts precise video clips based on a requested phrase.

## Features

* **Multi-Source Reconciliation:** Reconciles disagreements between transcript tokens and STT timing data (handling contractions, punctuation, filler words, and speech rate variations).
* **Auditable Structured Logging:** Records conflict detection, boundary decisions, confidence scores, and reasoning into structured JSON logs.
* **Stateful Learning:** Maintains agent memory across queries (`memory.json`) to learn from user corrections and adjust boundary padding dynamically.
* **CLI Interface:** Simple, robust command-line interface for running cuts and applying corrections.

---

## Project Structure

```text
phrase_cutter_agent/
│
├── app/
│   ├── __init__.py      # Package initializer
│   ├── agent.py         # Core agent orchestration & state management
│   ├── align.py         # Subsequence alignment & conflict resolution logic
│   ├── cutter.py        # Video cutting & FFmpeg processing module
│   ├── main.py          # CLI entry point
│   ├── memory.py        # Persistent state & memory management
│   ├── normalize.py     # Tokenization, contraction & punctuation normalization
│   ├── schemas.py       # Data models and structures
│   ├── transcribe.py    # Whisper transcription & word-level timing wrapper
│   └── utils.py         # Helper utilities
│
├── data/                # Sample input data and test cases
├── outputs/             # Generated video clips (.mp4)
├── logs/                # Structured JSON audit logs
├── state/               # Agent memory and correction history
├── requirements.txt     # Project dependencies
└── README.md
```
---
## Setup & Installation
1. **Clone the repository:**

```Bash
git clone [https://github.com/Aswathi846/phrase-cutter-agent.git](https://github.com/Aswathi846/phrase-cutter-agent.git)
cd phrase-cutter-agent
```
2. **Create and activate a virtual environment:**

```Bash
python -m venv venv
## On Windows:
venv\Scripts\activate
## On macOS/Linux:
source venv/bin/activate
```
3. **Install dependencies:**

```Bash
pip install -r requirements.txt
```
---
## How to Run
To cut a specific phrase from a video file:

```Bash
python -m app.main cut --video data/sample_case_2/contraction.mp4 --phrase "can't stop"
```
To apply a correction adjustment based on boundary performance:
```Bash
python -m app.main correct --phrase "can't stop" --issue "start too late" --adjustment-ms 150
```
---
## What I Would Do Next With More Time
1. **Web UI Integration:** Build a Streamlit or FastAPI web interface allowing users to upload videos, view aligned transcripts interactively, and preview cuts in real time.

2. **Multi-Model STT Support:** Expand ingestion to support alternative speech-to-text providers (such as OpenAI API, Deepgram, or local Vosk models) with pluggable adapters.

3. **Advanced Visual Boundary Detection:** Incorporate visual silence or shot-change detection alongside audio word boundaries to make transition cuts look even cleaner.
