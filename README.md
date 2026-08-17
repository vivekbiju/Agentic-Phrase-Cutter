# Stateful Phrase Cutter Agent 🎬🤖

An intelligent, auditable, and stateful multi-source alignment agent designed to reconcile discrepancies between speech-to-text transcripts and word-level timing data, producing precise video clip isolations. Built for rigorous AI engineering evaluation.

<img width="1452" height="826" alt="Screenshot_17-8-2026_18922_localhost" src="https://github.com/user-attachments/assets/aa3082fc-045c-4436-9d5d-c8c59f14d36d" />

---

## 🚀 Overview & Architecture

Standard video-cutting pipelines rely on naive string matching against timestamps, which frequently fails due to audio drift, punctuation handling, conversational filler words, and token fragmentation (such as contractions splitting across timing boundaries).

This agent treats **alignment conflict as a first-class citizen** by implementing a robust multi-layer architecture:

1. **Ingestion & Normalization Layer:** Automatically ingests video files, transcripts, and word-level timing streams via OpenAI Whisper with timestamp outputs, normalizing token structures and handling sub-token fragmentation.
2. **Conflict Arbitration & Drift Detection Engine:** Detects discrepancies between semantic text sources and granular timing edges, applying dynamic confidence scoring, empty slice protection, and defensive fallback policies.
3. **Auditable Reasoning Logger:** Automatically records structured decisions (e.g., *"timing data trusted for precise word edges; transcript semantic match validated"*) into persistent JSON logs with robust filesystem-safe sanitization.
4. **Developer-First CLI & Interactive Web UI:** Renders an ASCII timeline and execution summary in the terminal, alongside a **Streamlit Web Interface** for visual phrase cutting and playback.

---

## 🛠️ Project Structure

```text
Agentic_Phrase_Cutter/
├── app/
│   ├── __init__.py      # Package initializer
│   ├── agent.py         # Core agent decision engine & workflow orchestration
│   ├── align.py         # Transcript and timing multi-source alignment logic
│   ├── cutter.py        # Video frame extraction and cutting engine
│   ├── main.py          # CLI interface and command router
│   ├── memory.py        # Stateful persistence & agent learning memory
│   ├── normalize.py     # Token normalization & fuzzy anchoring logic
│   ├── schemas.py       # Pydantic data models & structured log definitions
│   ├── streamlit_app.py # Interactive Streamlit web user interface
│   ├── transcribe.py    # Whisper integration for word-level timings
│   ├── utils.py         # Helper utilities and logging configuration
│   └── visualization.py # Terminal ASCII timeline & execution summary tables
├── data/
│   ├── sample_case_1/   # Filler word / conversational test case
│   │   ├── filler.mp4   # Source video containing filler utterances ("um...")
│   │   ├── timings.json # Word-level timestamp data from Whisper
│   │   └── transcript.json # Clean text transcript
│   └── sample_case_2/   # Split contraction edge case ("can't stop")
│       ├── contraction.mp4 # Source video featuring contraction boundaries
│       ├── timings.json # Token-split timing metadata ([ca], [n't])
│       └── transcript.json # Semantic transcript text
├── logs/                # Auditable structured JSON decision logs
├── outputs/             # Generated isolated MP4 clips
├── state/               # Persistent state and memory storage (memory.json)
├── requirements.txt     # Project dependencies
└── README.md            # Comprehensive documentation

```

---

## ⚙️ Installation & Setup

1. **Clone the Repository:**

```bash
git clone [https://github.com/vivekbiju/Agentic-Phrase-Cutter.git](https://github.com/vivekbiju/Agentic-Phrase-Cutter.git)
cd Agentic-Phrase-Cutter

```

2. **Create and Activate a Virtual Environment:**

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

```

3. **Install Dependencies:**

```bash
pip install -r requirements.txt

```
### Prerequisites

This project relies on **FFmpeg** for video extraction and rendering. Ensure FFmpeg is installed on your system path before running the CLI:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install -y ffmpeg

# Windows (via winget)
winget install ffmpeg
```
---

## 🚀 Running the Agent & Web UI

You can interact with the agent via the command line or launch the interactive Streamlit web application.

### Option A: Launch Streamlit Web UI

```bash
streamlit run app/streamlit_app.py

```

### Option B: Command Line Interface (CLI)

```bash
python -m app.main cut --video data/sample_case_1/filler.mp4 --phrase "I think we should wait here"

```

---

## 🧪 Handling Hard Edge Cases

This agent was specifically engineered to solve the most difficult alignment failure modes:

* **Contraction Splitting Across Timing Boundaries:** When Whisper splits a word like `"can't"` into separate tokens (`[ ca ]` and `[ n't ]`), the normalization module bridges sub-token intervals securely.
* **Conversational Filler Words:** Dynamically filters out filler utterances (e.g., `"um..."`) present in timing data but omitted from clean transcripts.
* **Speech Rate Drift & Empty Slices:** Detects duration anomalies across variable tempos and protects against empty timing boundary states through fallback arbitration policies.

---

## 📋 Auditing & Transparency

Every execution automatically generates a structured JSON log inside the `logs/` directory using robust filesystem-safe name slugification. These logs capture:

* Source conflict types and arbitration outcomes.
* Granular confidence scores and timestamp bounds.
* Auditable human-readable reasoning strings.

---

## 🔮 Future Improvements (With More Time)

If given more time to scale this system into a full production microservice, I would implement:

1. **Active Learning Feedback Loop:** Allow user corrections on clipped boundaries to dynamically fine-tune the agent's confidence weights and fuzzy-matching thresholds over time.
2. **Multi-Model Ensemble Support:** Integrate parallel STT engines (such as Whisper variants alongside local LLM speech models) to cross-verify timing confidence via consensus voting.

