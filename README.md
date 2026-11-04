# आहार-वाणी (Aahar-Vaani)
> **Voice-First Indian Food, Mess, and Metabolic Health Companion**  
> Powered by **Streamlit**, **Gnani AI** Sovereign Indic Speech Models (*Prisma v3.0 STT* & *Timbre v3.0 TTS*), and **ICMR-NIN** (National Institute of Nutrition) Nutritional Standards.

---

## 🌟 Overview

**Aahar-Vaani** (आहार-वाणी) addresses the unique nutritional realities of Indian diets—from hostel and college messes to street food and homestyle thalis. Most global nutrition trackers fail to recognize colloquial Indian food terms, portion units (*katori*, *chammach*, *thali*, *tukda*), and the physiological impact of high-carbohydrate meals on metabolic health.

Aahar-Vaani provides:
1. **Sovereign Indic Voice Recognition (Prisma v3.0 STT)**: Domain-boosted with 650+ Indian food terms and units to understand Hindi, Hinglish, and regional speech effortlessly.
2. **Expressive Indic Speech Synthesis (Timbre v3.0 TTS)**: Personalized vocal coaching and nutritional feedback delivered in natural Indian voices with empathetic prosody.
3. **Clinical Metabolic Health Audit (ICMR-NIN IFCT-2017)**: Real-time analysis of Glycemic Load (GL), Carbohydrate-to-Protein ratios, dietary fiber sufficiency, and meal sequencing strategies to blunt postprandial glucose spikes.
4. **Curated Indian Food Lexicon**: 168+ authentic Indian dishes with validated macronutrients, glycemic indices, and street portion benchmarks.

---

## 📂 Architecture & Directory Structure

```
aahar-vaani/
├── .env.example              # Template for Gnani AI API credentials & endpoints
├── .gitignore                 # Strict ignores for venv, secrets, cache & audio scratchpad
├── requirements.txt           # Pinned dependencies (streamlit, pydantic, scipy, etc.)
├── README.md                  # Comprehensive architectural and setup documentation
├── core/
│   ├── __init__.py            # Clean exports for STT, TTS, and NutritionEngine
│   ├── gnani_stt.py           # Prisma v3.0 connector with 650+ culinary keyterms boosting
│   ├── gnani_tts.py           # Timbre v3.0 connector with expressive SSML & coaching tags
│   └── nutrition_engine.py    # ICMR-NIN parser, Indian portion units & metabolic audit
├── data/
│   ├── food_lexicon.json      # 168+ Indian foods with glycemic index, load & ICMR codes
│   └── temp_audio/            # Scratchpad for audio processing (.gitkeep preserved)
└── app.py                     # Main interactive Streamlit dashboard
```

---

## ⚙️ Environment Variables (`.env`)

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Configure your credentials:
```env
# Gnani AI Sovereign Indic Speech Model Credentials
GNANI_API_KEY=your_gnani_api_key_here
STT_ENDPOINT=https://api.vachana.ai/stt/v3
TTS_ENDPOINT=https://api.vachana.ai/api/v1/tts/inference

# Speech & Local Settings
GNANI_LANG_CODE=hi-IN
AUDIO_TEMP_DIR=data/temp_audio
STREAMLIT_SERVER_PORT=8501
```

> **Note:** If `GNANI_API_KEY` is not provided or set to the placeholder, the application automatically runs in **Developer Simulation Mode**, utilizing local audio synthesis and simulated Indic recognition so you can test features offline immediately.

---

## 🚀 Setup & Installation (Windows)

### Option A: Using PowerShell (Recommended)

1. **Navigate to the project root**:
   ```powershell
   cd c:\Users\Admin\Documents\air-quality-cep\aahar-vaani
   ```

2. **Create a Python Virtual Environment**:
   ```powershell
   python -m venv venv
   ```

3. **Activate the Virtual Environment**:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   *(If script execution is disabled on your system, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then re-run the activation script)*

4. **Upgrade Pip & Install Dependencies**:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Run the Streamlit Dashboard**:
   ```powershell
   streamlit run app.py
   ```

---

### Option B: Using Windows Command Prompt (CMD)

1. **Navigate to the directory**:
   ```cmd
   cd c:\Users\Admin\Documents\air-quality-cep\aahar-vaani
   ```

2. **Create & activate virtual environment**:
   ```cmd
   python -m venv venv
   venv\Scripts\activate.bat
   ```

3. **Install pinned requirements**:
   ```cmd
   pip install -r requirements.txt
   ```

4. **Launch Application**:
   ```cmd
   streamlit run app.py
   ```

---

## 🩺 ICMR-NIN Metabolic Audit Standards

Aahar-Vaani incorporates metabolic guidelines established by the **Indian Council of Medical Research (ICMR)** and the **National Institute of Nutrition (NIN)**:

| Metric | Target / Benchmark | Clinical Significance |
| :--- | :--- | :--- |
| **Carb:Protein Ratio** | $\le 2.5 : 1$ | Typical Indian meals exceed 5:1. Maintaining $\le 2.5:1$ promotes satiety and prevents muscle wasting. |
| **Glycemic Load (GL)** | Low ($\le 10$), Mod ($11-19$), High ($\ge 20$) | Predicts the magnitude of blood glucose excursions 45-60 minutes post meal. |
| **Dietary Fiber** | $\ge 8-10\text{g}$ / main meal | Slows gastric emptying, blunting rapid amylase breakdown of refined starches. |
| **Meal Sequencing** | Fiber/Curd $\rightarrow$ Protein $\rightarrow$ Carbs | Clinical trials show sequencing reduces glucose spikes by up to 35%. |

---

## 🔁 Git Automation & Workflow

In accordance with project engineering rules:
- All sensitive credentials (`.env`) and generated audio binaries (`*.wav`, `data/temp_audio/*`) are excluded from version control.
- Every completed milestone and feature is tracked via standard **Conventional Commits** (`feat:`, `fix:`, `chore:`, `docs:`).
- Continuous synchronization is enforced via `git push origin <active-branch>` upon remote setup.
