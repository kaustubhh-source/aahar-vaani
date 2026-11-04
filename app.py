"""
Aahar-Vaani (आहार-वाणी)
Sovereign Indic Voice-First Indian Food, Mess, and Metabolic Health Companion
Powered by Gnani AI (Prisma v3.0 STT & Timbre v3.0 TTS) and ICMR-NIN Standards.
"""

import os
import io
import time
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Import Core Modules
from core.gnani_stt import GnaniSTTClient
from core.gnani_tts import GnaniTTSClient
from core.nutrition_engine import NutritionEngine

# Optional Mic Recorder
try:
    from streamlit_mic_recorder import mic_recorder
    HAS_MIC_RECORDER = True
except ImportError:
    HAS_MIC_RECORDER = False

load_dotenv()

# --- Page Setup & Styling ---
st.set_page_config(
    page_title="Aahar-Vaani | आहार-वाणी",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Theme CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(120deg, #d97706, #059669);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4b5563;
        margin-bottom: 1.2rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border-radius: 10px;
        padding: 14px 16px;
        border: 1px solid #e2e8f0;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-title {
        font-size: 0.82rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 4px;
    }
    .badge-low {
        background-color: #dcfce7;
        color: #15803d;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-moderate {
        background-color: #fef9c3;
        color: #a16207;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-high {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .indic-tag {
        background-color: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_nutrition_engine():
    return NutritionEngine()


@st.cache_resource
def get_stt_client(api_key: str, endpoint: str):
    return GnaniSTTClient(api_key=api_key, endpoint=endpoint)


@st.cache_resource
def get_tts_client(api_key: str, endpoint: str):
    return GnaniTTSClient(api_key=api_key, endpoint=endpoint)


# --- Session State Initialization ---
if "meal_history" not in st.session_state:
    st.session_state.meal_history = []

if "current_transcript" not in st.session_state:
    st.session_state.current_transcript = "2 katori dal tadka, 3 roti aur 1 plate kachumber salad"

if "last_audit_result" not in st.session_state:
    st.session_state.last_audit_result = None

if "last_tts_audio" not in st.session_state:
    st.session_state.last_tts_audio = None


# --- Sidebar: Configuration & Sovereign Models Status ---
with st.sidebar:
    st.markdown("### 🎙️ Gnani AI Sovereign Indic Engine")
    st.caption("Powered by Prisma v3.0 STT & Timbre v3.0 TTS")

    api_key_input = st.text_input(
        "GNANI_API_KEY",
        value=os.getenv("GNANI_API_KEY", ""),
        type="password",
        help="Enter your Gnani AI API key. Leave blank to run in simulated preview mode.",
    )

    stt_endpoint = st.text_input(
        "STT Endpoint",
        value=os.getenv("STT_ENDPOINT", "https://api.vachana.ai/stt/v3"),
    )

    tts_endpoint = st.text_input(
        "TTS Endpoint",
        value=os.getenv("TTS_ENDPOINT", "https://api.vachana.ai/api/v1/tts/inference"),
    )

    selected_lang = st.selectbox(
        "Indic Language / बोली",
        options=["hi-IN", "en-IN", "ta-IN", "te-IN", "mr-IN", "gu-IN", "bn-IN"],
        index=0,
        format_func=lambda x: {
            "hi-IN": "Hindi (हिन्दी)",
            "en-IN": "Indian English (Hinglish)",
            "ta-IN": "Tamil (தமிழ்)",
            "te-IN": "Telugu (తెలుగు)",
            "mr-IN": "Marathi (मराठी)",
            "gu-IN": "Gujarati (ગુજરાતી)",
            "bn-IN": "Bengali (বাংলা)",
        }.get(x, x),
    )

    voice_gender = st.radio("Timbre Voice Gender", options=["Female", "Male"], index=0, horizontal=True)

    st.divider()

    # Engine Status Indicators
    is_live = bool(api_key_input and not api_key_input.startswith("your_gnani"))
    if is_live:
        st.success("🟢 Connected: Live Gnani AI API")
    else:
        st.info("🟡 Dev Preview Mode (Simulated Audio & Keyterms)")

    engine = get_nutrition_engine()
    stt_client = get_stt_client(api_key_input, stt_endpoint)
    tts_client = get_tts_client(api_key_input, tts_endpoint)

    st.markdown("#### 📚 Database Status")
    st.write(f"• **Food Lexicon Items:** {len(engine.items_by_id)}")
    st.write(f"• **Prisma Keyterms Boosted:** {len(stt_client.get_custom_keyterms())}")
    st.write(f"• **Clinical Standard:** ICMR-NIN IFCT-2017")

    st.divider()
    if st.button("🗑️ Clear Meal History", use_container_width=True):
        st.session_state.meal_history = []
        st.session_state.last_audit_result = None
        st.session_state.last_tts_audio = None
        st.rerun()


# --- Main Dashboard Header ---
st.markdown('<div class="main-header">आहार-वाणी | Aahar-Vaani</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Voice-First Indian Food, Mess & Metabolic Health Companion '
    '• ICMR-NIN Standards • Sovereign Indic Speech AI</div>',
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs([
    "🎙️ Voice Meal Logging",
    "📊 Metabolic Health Audit",
    "🔍 Indian Food Lexicon",
    "📜 Mess & Daily History",
])


# ==========================================
# TAB 1: Voice Meal Logging
# ==========================================
with tab1:
    col_input, col_tips = st.columns([1.6, 1.0])

    with col_input:
        st.markdown("#### 1. Speak Your Meal (अपनी आवाज़ में भोजन बताएं)")
        st.caption("Tell us what you ate using everyday Indian units like 'katori', 'chammach', 'plate', 'roti'.")

        audio_bytes = None

        if HAS_MIC_RECORDER:
            audio_record = mic_recorder(
                start_prompt="🔴 Click to Record (रिकॉर्डिंग शुरू करें)",
                stop_prompt="⏹️ Stop Recording (रिकॉर्डिंग रोकें)",
                key="audio_recorder",
            )
            if audio_record:
                audio_bytes = audio_record["bytes"]
                st.audio(audio_bytes, format="audio/wav")
        else:
            st.warning("`streamlit-mic-recorder` not available in this environment. Use file upload or test presets.")

        uploaded_audio = st.file_uploader(
            "Or upload an audio file (WAV / MP3 / M4A):",
            type=["wav", "mp3", "m4a"],
            help="Upload raw audio recording of your meal description.",
        )
        if uploaded_audio is not None:
            audio_bytes = uploaded_audio.read()
            st.audio(audio_bytes)

        if audio_bytes:
            if st.button("✨ Transcribe Voice with Prisma v3.0", use_container_width=True, type="primary"):
                with st.spinner("Prisma v3.0 recognizing sovereign Indic speech with culinary keyterms..."):
                    stt_res = stt_client.transcribe_audio(audio_bytes, lang_code=selected_lang)
                    if stt_res.get("transcript"):
                        st.session_state.current_transcript = stt_res["transcript"]
                        st.success(f"Recognized ({stt_res.get('confidence', 0.9)*100:.0f}% confidence): {stt_res['transcript']}")
                    else:
                        st.error(f"STT Error: {stt_res.get('message', 'Could not transcribe.')}")

        st.markdown("#### 2. Review or Edit Transcript (आहार विवरण)")
        transcript_input = st.text_area(
            "Spoken Transcript / Type Meal Directly:",
            value=st.session_state.current_transcript,
            height=90,
            help="Example: 'Maine 2 katori dal tadka, 3 roti aur 1 plate salad khaya'",
        )
        st.session_state.current_transcript = transcript_input

        btn_analyze = st.button("🚀 Analyze Nutrition & Metabolic Health", use_container_width=True, type="primary")

    with col_tips:
        st.markdown("#### 💡 Quick Indic Voice Prompts")
        st.caption("Click any preset to test the parser & metabolic engine instantly:")

        presets = [
            ("🥗 Balanced Student Thali", "2 katori dal tadka, 2 roti, 1 katori curd aur 1 plate kachumber salad"),
            ("🥔 High Carb Mess Breakfast", "2 piece aloo paratha aur 1 glass sweet lassi"),
            ("🫓 High Spike Street Craving", "1 plate chhole bhature aur 1 cup masala chai"),
            ("🍗 High Protein Non-Veg", "1 piece tandoori chicken, 1 plate boiled egg aur 1 glass chaas"),
            ("🍲 Light Restorative Khichdi", "2 katori moong dal khichdi aur 1 katori dahi"),
        ]

        for label, prompt_text in presets:
            if st.button(label, use_container_width=True):
                st.session_state.current_transcript = prompt_text
                st.rerun()

    if btn_analyze or (st.session_state.last_audit_result is None and st.session_state.current_transcript):
        with st.spinner("Conducting ICMR-NIN metabolic audit..."):
            matched_items = engine.parse_transcript(st.session_state.current_transcript)
            audit_result = engine.audit_meal(matched_items)
            st.session_state.last_audit_result = audit_result

            # Synthesize Timbre v3.0 voice response
            speech_text = (
                audit_result.spoken_summary_hi
                if selected_lang.startswith("hi")
                else audit_result.spoken_summary_en
            )
            emotion = "encouraging" if audit_result.icmr_compliance_score >= 80 else "cautionary"
            tts_res = tts_client.synthesize_speech(
                speech_text,
                lang_code=selected_lang,
                voice_gender=voice_gender.lower(),
                emotion=emotion,
            )
            st.session_state.last_tts_audio = tts_res.get("audio_bytes")

            # Add to history if unique
            if audit_result.items:
                meal_record = {
                    "time": time.strftime("%H:%M:%S"),
                    "transcript": st.session_state.current_transcript,
                    "calories": audit_result.total_calories_kcal,
                    "protein": audit_result.total_protein_g,
                    "carbs": audit_result.total_carbs_g,
                    "fat": audit_result.total_fat_g,
                    "fiber": audit_result.total_fiber_g,
                    "glycemic_load": audit_result.total_glycemic_load,
                    "score": audit_result.icmr_compliance_score,
                }
                st.session_state.meal_history.append(meal_record)

        st.success("Analysis complete! Open Tab 2 to view clinical metabolic insights.")


# ==========================================
# TAB 2: Metabolic Health Audit
# ==========================================
with tab2:
    audit = st.session_state.last_audit_result

    if audit is None or not audit.items:
        st.info("Log a meal in Tab 1 to see the ICMR-NIN Metabolic Audit.")
    else:
        st.markdown(f"### 📋 Meal Audit: *\"{st.session_state.current_transcript}\"*")

        # Top Macro KPI Cards
        kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
        with kpi1:
            st.markdown(f'<div class="metric-card"><div class="metric-title">🔥 Energy</div><div class="metric-value">{int(audit.total_calories_kcal)}<span style="font-size:0.9rem"> kcal</span></div></div>', unsafe_allow_html=True)
        with kpi2:
            st.markdown(f'<div class="metric-card"><div class="metric-title">🍞 Carbs</div><div class="metric-value">{audit.total_carbs_g}<span style="font-size:0.9rem"> g</span></div></div>', unsafe_allow_html=True)
        with kpi3:
            st.markdown(f'<div class="metric-card"><div class="metric-title">💪 Protein</div><div class="metric-value">{audit.total_protein_g}<span style="font-size:0.9rem"> g</span></div></div>', unsafe_allow_html=True)
        with kpi4:
            st.markdown(f'<div class="metric-card"><div class="metric-title">🧈 Fat</div><div class="metric-value">{audit.total_fat_g}<span style="font-size:0.9rem"> g</span></div></div>', unsafe_allow_html=True)
        with kpi5:
            st.markdown(f'<div class="metric-card"><div class="metric-title">🌾 Fiber</div><div class="metric-value">{audit.total_fiber_g}<span style="font-size:0.9rem"> g</span></div></div>', unsafe_allow_html=True)
        with kpi6:
            st.markdown(f'<div class="metric-card"><div class="metric-title">⚖️ C:P Ratio</div><div class="metric-value">{audit.carb_protein_ratio}:1</div></div>', unsafe_allow_html=True)

        st.write("")

        col_left, col_right = st.columns([1.2, 1.0])

        with col_left:
            st.markdown("#### 🩺 ICMR-NIN Metabolic Assessment")

            # Compliance Score & Glycemic Tier
            badge_class = {
                "Low": "badge-low",
                "Moderate": "badge-moderate",
                "High": "badge-high",
                "Severe Spike Risk": "badge-high",
            }.get(audit.glycemic_tier, "badge-low")

            score_color = "#10b981" if audit.icmr_compliance_score >= 80 else ("#f59e0b" if audit.icmr_compliance_score >= 60 else "#ef4444")

            st.markdown(
                f"""
                <div style="display:flex; align-items:center; justify-content:space-between; background:#ffffff; padding:16px; border-radius:10px; border:1px solid #e2e8f0; margin-bottom:12px;">
                    <div>
                        <div style="font-size:0.85rem; color:#64748b; font-weight:600;">ICMR-NIN COMPLIANCE SCORE</div>
                        <div style="font-size:2.2rem; font-weight:800; color:{score_color};">{audit.icmr_compliance_score} / 100</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:0.85rem; color:#64748b; font-weight:600;">GLYCEMIC LOAD</div>
                        <div style="margin-top:4px;"><span class="{badge_class}">{audit.glycemic_tier} ({audit.total_glycemic_load} GL)</span></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Warnings & Recommendations
            if audit.metabolic_warnings:
                st.markdown("##### ⚠️ Metabolic Observations")
                for w in audit.metabolic_warnings:
                    st.warning(w)

            st.markdown("##### 💡 Clinical Indic Coaching & Sequencing")
            for r in audit.coaching_recommendations:
                st.info(f"✨ **{r}**")

        with col_right:
            st.markdown("#### 🔊 Timbre v3.0 Sovereign Voice Companion")
            st.caption("AI Nutritionist audio summary with expressive Indic cadence:")

            if st.session_state.last_tts_audio:
                st.audio(st.session_state.last_tts_audio, format="audio/wav")

            st.markdown(f"**Hindi Summary:**\n> *\"{audit.spoken_summary_hi}\"*")
            st.markdown(f"**English Summary:**\n> *\"{audit.spoken_summary_en}\"*")

            st.divider()

            st.markdown("#### 📊 Macronutrient Distribution")
            macro_df = pd.DataFrame({
                "Nutrient": ["Carbs (g)", "Protein (g)", "Fat (g)", "Fiber (g)"],
                "Amount": [audit.total_carbs_g, audit.total_protein_g, audit.total_fat_g, audit.total_fiber_g],
            })
            st.bar_chart(macro_df.set_index("Nutrient"))

        st.markdown("#### 🥗 Itemized Food Breakdown")
        table_rows = []
        for i in audit.items:
            table_rows.append({
                "Item": f"{i.name_en} ({i.name_hi})",
                "Portion": f"{i.quantity} {i.unit} ({int(i.grams)}g)",
                "Calories": f"{int(i.calories_kcal)} kcal",
                "Carbs": f"{i.carbs_g}g",
                "Protein": f"{i.protein_g}g",
                "Fat": f"{i.fat_g}g",
                "Fiber": f"{i.fiber_g}g",
                "GI": i.glycemic_index,
                "GL": i.glycemic_load,
                "ICMR Code": i.icmr_source,
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True)


# ==========================================
# TAB 3: Indian Food Lexicon Explorer
# ==========================================
with tab3:
    st.markdown("### 🔍 Indian Food, Street & Mess Lexicon (आहार शब्दकोश)")
    st.caption("168+ curated Indian foods with ICMR-NIN IFCT-2017 nutritional benchmarks & glycemic markers.")

    search_query = st.text_input("Search food item by name or alias (e.g., 'dal', 'paratha', 'samosa', 'roti'):", value="")

    category_filter = st.selectbox(
        "Filter by Category:",
        options=["All", "bread_grain", "dal_curry", "breakfast", "street_food", "snack", "sweet", "beverage"],
        index=0,
    )

    lexicon_items = list(engine.items_by_id.values())

    if category_filter != "All":
        lexicon_items = [i for i in lexicon_items if i.get("category") == category_filter]

    if search_query:
        sq = search_query.lower()
        lexicon_items = [
            i for i in lexicon_items
            if sq in i["name_en"].lower()
            or sq in i["name_hi"].lower()
            or any(sq in a.lower() for a in i.get("aliases", []))
        ]

    st.write(f"Showing **{len(lexicon_items)}** items matching criteria:")

    display_data = []
    for item in lexicon_items:
        display_data.append({
            "Food Name": f"{item['name_en']} ({item['name_hi']})",
            "Category": item["category"],
            "Serving Unit": f"{item['serving_grams']}g ({item['default_unit']})",
            "Calories": item["calories_kcal"],
            "Carbs (g)": item["carbs_g"],
            "Protein (g)": item["protein_g"],
            "Fat (g)": item["fat_g"],
            "Fiber (g)": item["fiber_g"],
            "GI": item["glycemic_index"],
            "GL": item["glycemic_load"],
            "Metabolic Insights": item.get("metabolic_notes", ""),
        })

    st.dataframe(pd.DataFrame(display_data), use_container_width=True)


# ==========================================
# TAB 4: Mess & Daily History
# ==========================================
with tab4:
    st.markdown("### 📜 Mess & Daily Meal Log (दैनिक भोजन इतिहास)")
    st.caption("Cumulative daily tracking against ICMR-NIN Recommended Dietary Allowances (RDA).")

    if not st.session_state.meal_history:
        st.info("No meals recorded yet in this session. Log meals from Tab 1 to track daily metrics.")
    else:
        history_df = pd.DataFrame(st.session_state.meal_history)
        st.dataframe(history_df, use_container_width=True)

        tot_cal = history_df["calories"].sum()
        tot_prot = history_df["protein"].sum()
        tot_carbs = history_df["carbs"].sum()
        tot_fiber = history_df["fiber"].sum()

        st.markdown("#### 🎯 Daily RDA Progress (ICMR-NIN Adult Reference)")
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.metric("Total Calories", f"{int(tot_cal)} kcal", delta=f"{int(2000 - tot_cal)} kcal left", delta_color="inverse")
        with r2:
            st.metric("Total Protein", f"{tot_prot:.1f} g", delta=f"{tot_prot - 60.0:.1f} g vs 60g RDA")
        with r3:
            st.metric("Total Fiber", f"{tot_fiber:.1f} g", delta=f"{tot_fiber - 30.0:.1f} g vs 30g RDA")
        with r4:
            st.metric("Avg ICMR Score", f"{history_df['score'].mean():.0f} / 100")
