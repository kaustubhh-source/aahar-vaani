# आहार-वाणी (Aahar-Vaani)
> **Voice-First Indian Food, Mess, and Metabolic Health Companion**  
> Powered by **FastAPI**, **Gnani AI** Sovereign Indic Speech Models (*Prisma v3.0 STT* & *Timbre v3.0 TTS*), and **ICMR-NIN** (National Institute of Nutrition) Nutritional Standards.

---

## 🌟 Overview

**Aahar-Vaani** (आहार-वाणी) addresses the unique nutritional realities of Indian diets—from hostel and college messes to street food and homestyle thalis. Most global nutrition trackers fail to recognize colloquial Indian food terms, portion units (*katori*, *waati*, *cutting*, *chammach*, *dona*, *thali*), and the physiological impact of high-carbohydrate meals on metabolic health.

Aahar-Vaani provides:
1. **Sovereign Indic Voice Recognition (Prisma v3.0 STT)**: Domain-boosted with 450+ Indian food terms and colloquial units to recognize Hindi, Hinglish, and Marathi speech natively at 16kHz.
2. **Expressive Indic Speech Synthesis (Timbre v3.0 TTS)**: Personalized vocal coaching with expressive tags (`<excited>`, `<laugh>`, `<sigh>`) across two distinct personas: **Devansh** (Youth/Hostel Dost) and **Shivani** (Family/Elder Care).
3. **Clinical Metabolic Health Audit (ICMR-NIN IFCT-2017)**: Context-aware analysis (home vs mess vs canteen_thela), Carb-to-Protein ratio auditing, Glycemic Spike Risk assessment, hidden sugar alerts (~9g per cutting chai), and actionable budget Indian protein swaps.
4. **Venture-Grade Glassmorphic Dashboard**: Deep zinc dark interface (`#09090b`), circular SVG macro rings, glowing Web Audio 16kHz WAV recorder, and 1-tap demo scenario presets.

---

## 📂 Architecture & Directory Structure

```
aahar-vaani/
├── main.py                    # Production FastAPI Application (Serving API + Static SPA)
├── test_pipeline.py           # End-to-end backend pipeline smoke test
├── .env.example               # Template for Gnani AI API credentials & endpoints
├── .gitignore                 # Strict ignores for venv, secrets, cache & audio scratchpad
├── requirements.txt           # Pinned production dependencies (fastapi, uvicorn, pydantic, etc.)
├── README.md                  # Comprehensive architectural & setup documentation
├── core/
│   ├── __init__.py            # Modular exports
│   ├── gnani_stt.py           # Prisma v3.0 connector with 470+ culinary keyterms boosting
│   ├── gnani_tts.py           # Timbre v3.0 connector with expressive SSML & coach personas
│   └── nutrition_engine.py    # ICMR-NIN parser, Indian portion units & metabolic audit
├── data/
│   ├── food_lexicon.json      # 60 validated Indian foods with glycemic index & ICMR codes
│   └── temp_audio/            # Scratchpad for audio processing (.gitkeep preserved)
├── static/                    # Dedicated Tailwind CSS Single-Page Application (SPA)
│   ├── index.html             # Deep Obsidian (#08090D), Bento grid, Lucide icons, HTML5 canvas
│   ├── style.css              # Custom radar waveforms, glassmorphic panels, and expressive tags
│   └── app.js                 # 16kHz WAV recorder, live canvas visualizer, Timbre v3.0 player
└── app.py                     # Streamlit console (alternative reference)
```

---

## 🌐 Production API Endpoints (`main.py`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/transcribe` | Ingests 16kHz Mono WAV or audio file; transcribes via Prisma v3.0 with 450+ keyterms. |
| `POST` | `/api/analyze` | Executes ICMR-NIN audit, context multipliers, glycemic spike risks, and budget swaps. |
| `POST` | `/api/coach` | Synthesizes expressive voice response using Timbre v3.0 (`Devansh` / `Shivani`). |
| `GET` | `/api/audio/{filename}` | Streams generated WAV audio for instant in-browser playback. |
| `GET` | `/api/health` | Returns system status, keyterm counts, and clinical lexicon parameters. |
| `GET` | `/` | Serves the production glassmorphic single-page application. |

---

## 🚀 Setup & Launch (Windows)

### 1. Launch Production Full-Stack Application (Recommended)

```powershell
# 1. Navigate to standalone directory
cd C:\Users\Admin\Documents\aahar-vaani

# 2. Activate virtual environment (if created)
.\venv\Scripts\Activate.ps1

# 3. Launch the FastAPI Full-Stack Server
python -m uvicorn main:app --reload --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser to experience the sleek glassmorphic dashboard!

---

### 2. Run End-to-End Core Backend Smoke Test

```powershell
python test_pipeline.py
```

---

### 3. Run Streamlit Dashboard (Alternative)

```powershell
streamlit run app.py
```

---

## 🩺 ICMR-NIN Metabolic Audit Standards

Aahar-Vaani incorporates metabolic guidelines established by the **Indian Council of Medical Research (ICMR)** and the **National Institute of Nutrition (NIN)**:

| Metric | Target / Benchmark | Clinical Significance |
| :--- | :--- | :--- |
| **Carb:Protein Ratio** | $\le 2.5 : 1$ | Typical Indian meals exceed 5:1 (canteen poha + chai reaches 14.8:1). Maintaining $\le 2.5:1$ promotes satiety and prevents muscle wasting. |
| **Glycemic Spike Risk** | Low / Moderate / Severe | Predicts the magnitude of blood glucose excursions 45-60 minutes post meal. |
| **Preparation Context** | Home (1.0x) / Mess (1.25x) / Canteen (1.5x) | Adjusts fat and carb density based on street frying oil re-heating and diluted hostel dal. |
| **Hidden Sugar Flags** | $\le 10\text{g}$ / meal | Flags tapri cutting chai (~9g sugar per cup) and sweet lassi loads. |
| **Meal Sequencing** | Fiber $\rightarrow$ Protein $\rightarrow$ Carbs | Clinical trials show sequencing reduces glucose spikes by up to 35%. |
