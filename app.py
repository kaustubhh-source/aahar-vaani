"""
AAHAR-VAANI (आहार-वाणी) // ENTERPRISE VOICE INTELLIGENCE CONSOLE
Sovereign Indic Voice Platform & ICMR-NIN Metabolic Health Architecture
Powered by Gnani AI (Prisma v3.0 STT & Timbre v3.0 TTS) & ICMR-NIN IFCT-2017 Standards
"""

import os
import io
import time
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Import Core Sovereign Indic Backend
from core.gnani_stt import GnaniSTTClient
from core.gnani_tts import GnaniTTSClient
from core.nutrition_engine import NutritionEngine, MetabolicReport

# Optional Mic Recorder
try:
    from streamlit_mic_recorder import mic_recorder
    HAS_MIC_RECORDER = True
except ImportError:
    HAS_MIC_RECORDER = False

load_dotenv()

# --- Page Setup & Full Viewport Enforcement ---
st.set_page_config(
    page_title="AAHAR-VAANI // आहार-वाणी Console",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- CSS Injection: Enterprise Dark Obsidian & Glassmorphic System ---
DARK_CONSOLE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* 1. Obliterate Streamlit Default Elements */
#MainMenu { visibility: hidden !important; display: none !important; }
footer { visibility: hidden !important; display: none !important; }
header { visibility: hidden !important; display: none !important; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
.stDeployButton { display: none !important; }

/* 2. Deep Obsidian Root Viewport (#07080B) */
html, body, .stApp {
    background-color: #07080B !important;
    background-image: 
        radial-gradient(at 0% 0%, rgba(5, 46, 22, 0.5) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(69, 26, 3, 0.45) 0px, transparent 50%),
        radial-gradient(at 50% 50%, rgba(18, 20, 29, 0.7) 0px, transparent 100%) !important;
    background-attachment: fixed !important;
    color: #F3F4F6 !important;
    font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif !important;
}

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1440px !important;
}

/* 3. Typography & Mono Telemetry */
.font-mono {
    font-family: 'JetBrains Mono', monospace !important;
}

/* 4. Top Navigation Bar */
.top-nav-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 20px;
    background: rgba(18, 20, 29, 0.75);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    margin-bottom: 20px;
}

.brand-cluster {
    display: flex;
    align-items: center;
    gap: 14px;
}

.brand-symbol {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: linear-gradient(135deg, #059669, #d97706);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    font-weight: 800;
    color: #ffffff;
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.35);
}

.brand-title-text {
    font-size: 1.25rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #ffffff;
}

.brand-divider {
    color: #10b981;
    font-weight: 800;
}

.brand-sub-badge {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #9ca3af;
    margin-top: 2px;
}

.telemetry-cluster {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}

.telemetry-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 5px 12px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    background: rgba(16, 185, 129, 0.12);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.live-pulse {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 10px #10b981;
    animation: live-blink 1.8s infinite;
}

@keyframes live-blink {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(1.3); }
}

.telemetry-chip {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.07);
    padding: 5px 10px;
    border-radius: 8px;
    font-size: 0.72rem;
    display: flex;
    gap: 6px;
    font-family: 'JetBrains Mono', monospace;
}

.chip-label { color: #6b7280; font-weight: 600; }
.chip-val { color: #e5e7eb; font-weight: 700; }

/* 5. Glassmorphic Surface Cards */
.glass-panel {
    background: rgba(18, 20, 29, 0.7);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 22px;
    box-shadow: 0 12px 36px 0 rgba(0, 0, 0, 0.45);
    margin-bottom: 20px;
    transition: border-color 0.25s ease;
}

.glass-panel:hover {
    border-color: rgba(255, 255, 255, 0.16);
}

/* 6. Mode Switcher (Futuristic Segmented Control) */
.mode-segmented-bar {
    display: flex;
    background: rgba(10, 11, 16, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 4px;
    gap: 6px;
    margin-bottom: 20px;
}

.mode-pill {
    flex: 1;
    padding: 10px 16px;
    border-radius: 9px;
    font-size: 0.82rem;
    font-weight: 700;
    text-align: center;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    color: #9ca3af;
    background: transparent;
}

.mode-pill.active-youth {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(217, 119, 6, 0.35));
    border-color: rgba(245, 158, 11, 0.5);
    color: #fef3c7;
    box-shadow: 0 0 20px rgba(245, 158, 11, 0.2);
}

.mode-pill.active-elder {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.35));
    border-color: rgba(16, 185, 129, 0.5);
    color: #d1fae5;
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.2);
}

/* 7. Central Voice Station & Radar Animation */
.voice-station-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 24px 16px;
    background: radial-gradient(circle, rgba(16, 185, 129, 0.08) 0%, rgba(18, 20, 29, 0) 70%);
    border-radius: 14px;
    position: relative;
    overflow: hidden;
}

.radar-wrapper {
    position: relative;
    width: 96px;
    height: 96px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 12px;
}

.radar-core {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #10b981, #047857);
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    box-shadow: 0 0 30px rgba(16, 185, 129, 0.5);
    z-index: 5;
    transition: transform 0.2s ease;
}

.radar-ring {
    position: absolute;
    border-radius: 50%;
    border: 1px solid rgba(16, 185, 129, 0.35);
    animation: radar-pulse 3s infinite cubic-bezier(0.2, 0.8, 0.2, 1);
}

.radar-ring.r1 { width: 80px; height: 80px; animation-delay: 0s; }
.radar-ring.r2 { width: 96px; height: 96px; animation-delay: 1s; }

@keyframes radar-pulse {
    0% { transform: scale(0.7); opacity: 0.8; }
    50% { transform: scale(1.15); opacity: 0.2; }
    100% { transform: scale(1.3); opacity: 0; }
}

/* 8. Quick Terminal Chips */
.terminal-chips-group {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 14px;
}

.scenario-terminal-chip {
    background: rgba(10, 11, 16, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #d1d5db;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 0.76rem;
    font-family: 'JetBrains Mono', monospace;
    cursor: pointer;
    transition: all 0.2s ease;
}

.scenario-terminal-chip:hover {
    border-color: #10b981;
    color: #ffffff;
    background: rgba(16, 185, 129, 0.1);
    transform: translateY(-1px);
}

/* 9. Macro Bento Grid */
.bento-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 20px;
}

@media (max-width: 900px) {
    .bento-grid { grid-template-columns: repeat(2, 1fr); }
}

.bento-tile {
    background: rgba(14, 16, 24, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 16px;
    position: relative;
    overflow: hidden;
}

.bento-label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #9ca3af;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.bento-number {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.85rem;
    font-weight: 800;
    margin-top: 6px;
    color: #ffffff;
}

.bento-sub {
    font-size: 0.72rem;
    color: #6b7280;
    margin-top: 4px;
    display: flex;
    align-items: center;
    gap: 4px;
}

/* 10. ICMR Reality Radar Card */
.icmr-radar-card {
    background: rgba(18, 20, 29, 0.85);
    border-radius: 14px;
    padding: 18px 20px;
    border: 1px solid rgba(244, 63, 94, 0.35);
    box-shadow: 0 0 25px rgba(244, 63, 94, 0.15);
    margin-bottom: 20px;
}

.icmr-radar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.status-badge-severe {
    background: rgba(244, 63, 94, 0.2);
    border: 1px solid #f43f5e;
    color: #fecdd3;
    padding: 5px 12px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    box-shadow: 0 0 14px rgba(244, 63, 94, 0.4);
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.ratio-telemetry-bar {
    height: 8px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    overflow: hidden;
    display: flex;
    margin: 10px 0 6px 0;
}

/* 11. Voice Coach Playback Console */
.coach-playback-console {
    background: linear-gradient(135deg, rgba(20, 24, 36, 0.95), rgba(12, 14, 20, 0.9));
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 20px;
}

.coach-tag-badge {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    margin: 0 2px;
}

.tag-excited { background: rgba(6, 182, 212, 0.25); color: #67e8f9; border: 1px solid rgba(6, 182, 212, 0.4); }
.tag-laugh { background: rgba(245, 158, 11, 0.25); color: #fde68a; border: 1px solid rgba(245, 158, 11, 0.4); }
.tag-sigh { background: rgba(139, 92, 246, 0.25); color: #ddd6fe; border: 1px solid rgba(139, 92, 246, 0.4); }

.audio-bars-container {
    display: flex;
    align-items: center;
    gap: 3px;
    height: 22px;
}

.wave-line {
    width: 3px;
    background: #10b981;
    border-radius: 2px;
    animation: wave-bounce 1.2s infinite ease-in-out;
}

@keyframes wave-bounce {
    0%, 100% { height: 4px; opacity: 0.4; }
    50% { height: 20px; opacity: 1; }
}

/* 12. Desi Precision Swaps */
.swap-telemetry-row {
    background: rgba(10, 12, 18, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 0.82rem;
}

/* Streamlit Native Widget Overrides */
div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
    background-color: rgba(10, 12, 18, 0.8) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus {
    border-color: #10b981 !important;
    box-shadow: 0 0 15px rgba(16, 185, 129, 0.3) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #10b981, #059669) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 18px rgba(16, 185, 129, 0.35) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 25px rgba(16, 185, 129, 0.5) !important;
}

/* Audio Player */
audio {
    width: 100% !important;
    border-radius: 8px !important;
    filter: invert(0.9) hue-rotate(180deg);
}
</style>
"""

st.markdown(DARK_CONSOLE_CSS, unsafe_allow_html=True)

# --- Backend Singletons ---
@st.cache_resource
def get_nutrition_engine():
    return NutritionEngine()

@st.cache_resource
def get_stt_client():
    return GnaniSTTClient()

@st.cache_resource
def get_tts_client():
    return GnaniTTSClient()

engine = get_nutrition_engine()
stt_client = get_stt_client()
tts_client = get_tts_client()

# --- Session State Initialization ---
if "active_persona" not in st.session_state:
    st.session_state.active_persona = "Devansh"  # "Devansh" (Youth) or "Shivani" (Elder/Family)

if "current_transcript" not in st.session_state:
    st.session_state.current_transcript = "Subah do plate poha aur ek cutting chai li canteen mein"

if "last_report" not in st.session_state:
    # Run initial baseline report
    st.session_state.last_report = engine.parse_transcript(st.session_state.current_transcript)

if "coach_audio_path" not in st.session_state:
    st.session_state.coach_audio_path = None


# --- 1. Top Navigation & Live Telemetry Header ---
st.markdown(
    """
    <div class="top-nav-bar">
      <div class="brand-cluster">
        <div class="brand-symbol">आ</div>
        <div>
          <div class="brand-title-text">AAHAR-VAANI <span class="brand-divider">//</span> आहार-वाणी</div>
          <div class="brand-sub-badge">ENTERPRISE VOICE INTELLIGENCE CONSOLE • ICMR-NIN 2024 GROUNDED</div>
        </div>
      </div>
      <div class="telemetry-cluster">
        <div class="telemetry-pill">
          <span class="live-pulse"></span> PRISMA v3.0 ACTIVE
        </div>
        <div class="telemetry-chip">
          <span class="chip-label">LATENCY</span>
          <span class="chip-val">168ms</span>
        </div>
        <div class="telemetry-chip">
          <span class="chip-label">VOICE</span>
          <span class="chip-val">TIMBRE v3.0</span>
        </div>
        <div class="telemetry-chip">
          <span class="chip-label">KEYTERMS</span>
          <span class="chip-val">458 HINTS</span>
        </div>
        <div class="telemetry-chip">
          <span class="chip-label">SECURITY</span>
          <span class="chip-val">SOVEREIGN INDIC</span>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# --- 2. Futuristic Segmented Mode Switcher ---
mode_col1, mode_col2 = st.columns(2)

with mode_col1:
    youth_active = (st.session_state.active_persona == "Devansh")
    youth_label = "⚡ YOUTH & CANTEEN INTELLIGENCE (Devansh Persona • Street/Mess Multiplier)"
    if st.button(
        youth_label,
        use_container_width=True,
        type="primary" if youth_active else "secondary",
        key="btn_mode_youth"
    ):
        st.session_state.active_persona = "Devansh"
        st.session_state.coach_audio_path = None
        st.rerun()

with mode_col2:
    family_active = (st.session_state.active_persona == "Shivani")
    family_label = "🩺 METABOLIC & FAMILY CARE (Shivani Persona • Glycemic & BP Sentinel)"
    if st.button(
        family_label,
        use_container_width=True,
        type="primary" if family_active else "secondary",
        key="btn_mode_family"
    ):
        st.session_state.active_persona = "Shivani"
        st.session_state.coach_audio_path = None
        st.rerun()


# --- Main 2-Column Console Layout ---
left_col, right_col = st.columns([1.05, 1.35], gap="large")

# =========================================================================
# LEFT COLUMN: Central High-Tech Voice Station & Quick Terminal Scenarios
# =========================================================================
with left_col:
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    
    st.markdown(
        """
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <div style="font-size:0.95rem; font-weight:700; color:#10b981; letter-spacing:0.04em; text-transform:uppercase;">
            🎙️ Central Voice Intelligence Hub
          </div>
          <span style="font-size:0.72rem; color:#6b7280; font-family:'JetBrains Mono';">16kHz Native Mono</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Pulsing Voice Station Radar
    st.markdown(
        """
        <div class="voice-station-box">
          <div class="radar-wrapper">
            <div class="radar-ring r1"></div>
            <div class="radar-ring r2"></div>
            <div class="radar-core">🎙️</div>
          </div>
          <div style="font-size:0.82rem; font-weight:700; color:#e5e7eb;">Sovereign Indic Audio Uplink</div>
          <div style="font-size:0.72rem; color:#9ca3af; margin-top:2px;">Prisma v3.0 Automatic Speech Recognition</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Native Mic Recorder integration if available
    recorded_audio_bytes = None
    if HAS_MIC_RECORDER:
        mic_output = mic_recorder(
            start_prompt="🔴 Start Recording (16kHz)",
            stop_prompt="⏹️ Transcribe Spoken Meal",
            key="console_mic",
        )
        if mic_output and "bytes" in mic_output:
            recorded_audio_bytes = mic_output["bytes"]
            with st.spinner("Prisma v3.0 recognizing sovereign Indic speech..."):
                stt_res = stt_client.transcribe_audio(recorded_audio_bytes, language_code="hi-IN")
                if stt_res.get("transcript"):
                    st.session_state.current_transcript = stt_res["transcript"]
                    st.session_state.last_report = engine.parse_transcript(st.session_state.current_transcript)
                    st.session_state.coach_audio_path = None
                    st.rerun()

    # Enterprise Audio File Upload Dock
    uploaded_audio = st.file_uploader(
        "Drop audio file (WAV / MP3 / M4A):",
        type=["wav", "mp3", "m4a"],
        label_visibility="collapsed"
    )
    if uploaded_audio is not None:
        file_bytes = uploaded_audio.read()
        if st.button("Transcribe Uploaded Audio", use_container_width=True):
            with st.spinner("Transcribing via Prisma v3.0..."):
                res = stt_client.transcribe_audio(file_bytes, language_code="hi-IN")
                if res.get("transcript"):
                    st.session_state.current_transcript = res["transcript"]
                    st.session_state.last_report = engine.parse_transcript(st.session_state.current_transcript)
                    st.session_state.coach_audio_path = None
                    st.rerun()

    # Spoken Transcript Input Terminal
    transcript_text = st.text_area(
        "Spoken Meal Transcript (Hindi / Hinglish / Marathi):",
        value=st.session_state.current_transcript,
        height=75,
        placeholder="e.g. Subah do plate poha aur ek cutting chai li canteen mein...",
    )
    st.session_state.current_transcript = transcript_text

    # Execution Action Button
    if st.button("⚡ EXECUTE METABOLIC TELEMETRY", use_container_width=True):
        st.session_state.last_report = engine.parse_transcript(st.session_state.current_transcript)
        st.session_state.coach_audio_path = None
        st.rerun()

    # Quick Scenario Terminal Tags (1-Tap Demos)
    st.markdown(
        """
        <div style="font-size:0.75rem; font-weight:700; text-transform:uppercase; color:#f59e0b; margin-top:16px; margin-bottom:8px; letter-spacing:0.06em;">
          ⚡ 1-Tap Showcase Scenarios
        </div>
        """,
        unsafe_allow_html=True,
    )

    t_col1, t_col2 = st.columns(2)
    with t_col1:
        if st.button("2 Plate Poha + Kadak Chai (Canteen)", use_container_width=True, key="scen_canteen"):
            st.session_state.current_transcript = "Subah do plate poha aur ek kadak chai li canteen mein"
            st.session_state.last_report = engine.parse_transcript(st.session_state.current_transcript)
            st.session_state.coach_audio_path = None
            st.rerun()

    with t_col2:
        if st.button("2 Jowar Bhakri + Methi Bhaji (Ghar)", use_container_width=True, key="scen_ghar"):
            st.session_state.current_transcript = "Ghar par do jowar bhakri aur ek katori methi bhaji khayi"
            st.session_state.last_report = engine.parse_transcript(st.session_state.current_transcript)
            st.session_state.coach_audio_path = None
            st.rerun()

    if st.button("3 Samosa + Cold Drink (Street Thela)", use_container_width=True, key="scen_thela"):
        st.session_state.current_transcript = "Thele par teen samosa aur ek cold drink li"
        st.session_state.last_report = engine.parse_transcript(st.session_state.current_transcript)
        st.session_state.coach_audio_path = None
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================================
# RIGHT COLUMN: Visual Analytics, Bento Grid, ICMR Radar & Voice Coach Dock
# =========================================================================
report: MetabolicReport = st.session_state.last_report
rc = report.reality_check

with right_col:
    # Preparation Context Header Bar
    context_color = "#f59e0b" if report.detected_context == "canteen_thela" else ("#f43f5e" if report.detected_context == "mess" else "#10b981")
    context_label = report.detected_context.upper().replace("_", " / ")

    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:0.75rem; font-weight:800; padding:4px 10px; border-radius:6px; background:rgba(255,255,255,0.06); color:{context_color}; border:1px solid {context_color}; font-family:'JetBrains Mono';">
              CONTEXT: {context_label}
            </span>
            <span style="font-size:0.75rem; color:#9ca3af;">{report.context_description}</span>
          </div>
          <span style="font-size:0.72rem; color:#6b7280; font-family:'JetBrains Mono';">
            OIL MULT: {report.context_multipliers['oil_fat']}x | CARB MULT: {report.context_multipliers['carbs']}x
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Macro Bento Grid (4 dark glass tiles)
    prot_color = "#10b981" if report.total_protein_g >= 20 else "#f43f5e"
    carb_color = "#f43f5e" if rc.carb_to_protein_ratio > 5.0 else "#06b6d4"

    st.markdown(
        f"""
        <div class="bento-grid">
          <div class="bento-tile">
            <div class="bento-label">
              <span>Total Energy</span>
              <span style="color:#f59e0b;">kcal</span>
            </div>
            <div class="bento-number" style="color:#f59e0b;">{int(report.total_calories)}</div>
            <div class="bento-sub">vs 650 kcal target</div>
          </div>

          <div class="bento-tile">
            <div class="bento-label">
              <span>Protein Level</span>
              <span style="color:{prot_color};">g</span>
            </div>
            <div class="bento-number" style="color:{prot_color};">{report.total_protein_g}</div>
            <div class="bento-sub">{'⚠️ Protein Deficit' if report.total_protein_g < 18 else '✅ Target Met'}</div>
          </div>

          <div class="bento-tile">
            <div class="bento-label">
              <span>Carb Exposure</span>
              <span style="color:{carb_color};">g</span>
            </div>
            <div class="bento-number" style="color:{carb_color};">{report.total_carbs_g}</div>
            <div class="bento-sub">{rc.carb_to_protein_ratio}:1 C:P Ratio</div>
          </div>

          <div class="bento-tile">
            <div class="bento-label">
              <span>Grease & Fat</span>
              <span style="color:#fb7185;">g</span>
            </div>
            <div class="bento-number" style="color:#fb7185;">{report.total_fat_g}</div>
            <div class="bento-sub">{report.context_multipliers['oil_fat']}x Grease Factor</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. ICMR Metabolic Risk Radar
    spike_badge_html = ""
    if rc.glycemic_spike_risk == "Severe":
        spike_badge_html = '<span class="status-badge-severe">🔥 SEVERE GLYCEMIC SPIKE RISK</span>'
    elif rc.glycemic_spike_risk == "Moderate":
        spike_badge_html = '<span class="status-badge-severe" style="border-color:#f59e0b; color:#fde68a; box-shadow:0 0 14px rgba(245,158,11,0.4); background:rgba(245,158,11,0.2);">⚠️ MODERATE SPIKE RISK</span>'
    else:
        spike_badge_html = '<span class="status-badge-severe" style="border-color:#10b981; color:#a7f3d0; box-shadow:0 0 14px rgba(16,185,129,0.4); background:rgba(16,185,129,0.2);">✅ LOW BALANCED RISK</span>'

    # Ratio breakdown calculation
    prot_pct = max(6, min(50, int((1 / (rc.carb_to_protein_ratio + 1)) * 100))) if rc.carb_to_protein_ratio > 0 else 10
    carb_pct = 100 - prot_pct

    flags_html = "".join([f'<div style="font-size:0.8rem; color:#fecdd3; margin-top:4px;">{f}</div>' for f in rc.hidden_sugar_flags + rc.acidity_flags])

    st.markdown(
        f"""
        <div class="icmr-radar-card">
          <div class="icmr-radar-header">
            <div>
              <div style="font-size:0.95rem; font-weight:800; color:#ffffff;">⚖️ ICMR-NIN Reality Check: Indian Carbohydrate Overload</div>
              <div style="font-size:0.75rem; color:#9ca3af; margin-top:2px;">{rc.ratio_status}</div>
            </div>
            {spike_badge_html}
          </div>
          <div class="ratio-telemetry-bar">
            <div style="width:{prot_pct}%; background:#10b981;" title="Protein Share"></div>
            <div style="width:{carb_pct}%; background:#f43f5e;" title="Carb Share"></div>
          </div>
          <div style="display:flex; justify-content:space-between; font-size:0.7rem; font-family:'JetBrains Mono'; font-weight:600;">
            <span style="color:#10b981;">PROTEIN ({prot_pct}%)</span>
            <span style="color:#f43f5e;">CARBOHYDRATES ({carb_pct}%)</span>
          </div>
          {flags_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. Synthesized Voice Coach Dock
    active_persona_name = st.session_state.active_persona
    active_script = (
        report.spoken_summary_devansh
        if active_persona_name == "Devansh"
        else report.spoken_summary_shivani
    )

    # Expressive tags visualizer
    highlighted_script = (
        active_script
        .replace("<excited>", '<span class="coach-tag-badge tag-excited">&lt;excited&gt;</span>')
        .replace("</excited>", '<span class="coach-tag-badge tag-excited">&lt;/excited&gt;</span>')
        .replace("<laugh>", '<span class="coach-tag-badge tag-laugh">&lt;laugh&gt;</span>')
        .replace("</laugh>", '<span class="coach-tag-badge tag-laugh">&lt;/laugh&gt;</span>')
        .replace("<sigh>", '<span class="coach-tag-badge tag-sigh">&lt;sigh&gt;</span>')
        .replace("</sigh>", '<span class="coach-tag-badge tag-sigh">&lt;/sigh&gt;</span>')
    )

    st.markdown(
        f"""
        <div class="coach-playback-console">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:0.9rem;">🔊</span>
              <span style="font-size:0.85rem; font-weight:800; color:#10b981; letter-spacing:0.04em;">
                TIMBRE v3.0 // {active_persona_name.upper()} ({'YOUTH DOST' if active_persona_name == 'Devansh' else 'FAMILY CARE'})
              </span>
            </div>
            <div class="audio-bars-container">
              <div class="wave-line" style="animation-delay:0.1s;"></div>
              <div class="wave-line" style="animation-delay:0.3s;"></div>
              <div class="wave-line" style="animation-delay:0.5s;"></div>
              <div class="wave-line" style="animation-delay:0.2s;"></div>
              <div class="wave-line" style="animation-delay:0.4s;"></div>
              <div class="wave-line" style="animation-delay:0.6s;"></div>
            </div>
          </div>
          <div style="font-size:0.88rem; color:#e5e7eb; line-height:1.6; font-style:italic; margin-bottom:12px; background:rgba(0,0,0,0.3); padding:12px 14px; border-radius:8px; border:1px solid rgba(255,255,255,0.06);">
            "{highlighted_script}"
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Synthesize Audio on-demand or use cached
    if not st.session_state.coach_audio_path or not os.path.exists(st.session_state.coach_audio_path):
        filename = f"reply_{active_persona_name.lower()}_{int(time.time()*1000)}.wav"
        out_path = os.path.join("data", "temp_audio", filename)
        st.session_state.coach_audio_path = tts_client.synthesize_speech(
            text=active_script,
            persona=active_persona_name,
            language="hi-IN",
            output_path=out_path
        )

    if st.session_state.coach_audio_path and os.path.exists(st.session_state.coach_audio_path):
        st.audio(st.session_state.coach_audio_path, format="audio/wav")

    # 4. Precision Desi Swaps
    st.markdown(
        """
        <div style="font-size:0.75rem; font-weight:800; text-transform:uppercase; color:#34d399; letter-spacing:0.06em; margin-top:14px; margin-bottom:8px;">
          💡 Precision Desi Swaps (Hyper-Local Student & Family Budget)
        </div>
        """,
        unsafe_allow_html=True,
    )

    for swap in rc.budget_protein_swaps:
        st.markdown(
            f"""
            <div class="swap-telemetry-row">
              <span style="font-size:1rem;">⚡</span>
              <span style="color:#d1fae5; font-weight:500;">{swap}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# --- Full Width Itemized Breakdown Grid ---
st.markdown('<div class="glass-panel" style="margin-top:10px;">', unsafe_allow_html=True)
st.markdown(
    """
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
      <div style="font-size:0.95rem; font-weight:800; color:#ffffff;">
        📋 Itemized Food & Macro Telemetry (ICMR-NIN IFCT-2017 Grounded)
      </div>
      <span style="font-size:0.72rem; color:#9ca3af; font-family:'JetBrains Mono';">60 Calibrated Items</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if report.items:
    table_rows = []
    for item in report.items:
        table_rows.append({
            "Food Entity": f"{item.name_en} ({item.name_mr or item.name_hi})",
            "Portion Unit": f"{item.quantity} {item.unit} ({int(item.total_grams)}g)",
            "Calories": f"{item.scaled_calories:.1f} kcal",
            "Protein": f"{item.scaled_protein_g:.1f}g",
            "Carbs": f"{item.scaled_carbs_g:.1f}g",
            "Fat": f"{item.scaled_fat_g:.1f}g",
            "Fiber": f"{item.scaled_fiber_g:.1f}g",
            "GI / Risk": f"{item.glycemic_index} ({item.glycemic_spike_risk})",
            "ICMR Ref": item.icmr_source,
        })
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True)
else:
    st.info("No recognized Indian food entities. Type or record meal items.")

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown(
    """
    <div style="text-align:center; font-size:0.72rem; color:#6b7280; padding:18px 0; font-family:'JetBrains Mono';">
      AAHAR-VAANI // आहार-वाणी • SOVEREIGN INDIC VOICE INTELLIGENCE PLATFORM • GNANI AI PRISMA & TIMBRE v3.0
    </div>
    """,
    unsafe_allow_html=True,
)
