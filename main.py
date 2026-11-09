"""
Aahar-Vaani (आहार-वाणी) Production FastAPI Backend
Venture-backed, production-grade Indic speech & metabolic health server.
Wraps Gnani AI Prisma v3.0 STT, ICMR-NIN Metabolic Engine, and Timbre v3.0 TTS.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import Core Sovereign Indic Modules
from core.gnani_stt import GnaniSTTClient
from core.gnani_tts import GnaniTTSClient
from core.nutrition_engine import NutritionEngine, MetabolicReport

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AaharVaani.API")

# Initialize FastAPI App
app = FastAPI(
    title="Aahar-Vaani (आहार-वाणी) API",
    description="Production-grade Sovereign Indic Speech & ICMR-NIN Metabolic Nutrition Engine",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core Instances
stt_client = GnaniSTTClient()
tts_client = GnaniTTSClient()
engine = NutritionEngine()

TEMP_AUDIO_DIR = os.path.join(os.path.dirname(__file__), "data", "temp_audio")
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)


# --- Pydantic Request Models ---
class AnalyzeRequest(BaseModel):
    text: Optional[str] = None
    meal_text: Optional[str] = None
    persona: Optional[str] = "Devansh"
    language: Optional[str] = "hi-IN"


class CoachRequest(BaseModel):
    text: Optional[str] = None
    persona: Optional[str] = "Devansh"
    language: Optional[str] = "hi-IN"
    meal_text: Optional[str] = None


# --- API Routes ---

@app.get("/api/health")
async def health_check():
    """Returns system status, model parameters, and Indian food lexicon metrics."""
    return {
        "status": "healthy",
        "service": "Aahar-Vaani Production API",
        "version": "2.1.0",
        "stt_engine": "Gnani Prisma v3.0 (Indic Sovereign)",
        "tts_engine": "Gnani Timbre v3.0 (Indic Sovereign)",
        "clinical_standard": "ICMR-NIN IFCT-2017",
        "lexicon_items_count": len(engine.items_by_id),
        "boosted_keyterms_count": len(stt_client.get_custom_keyterms()),
        "gnani_configured": stt_client.is_configured(),
        "timestamp": time.time(),
    }


@app.post("/api/transcribe")
async def transcribe_audio_endpoint(
    request: Request,
    file: Optional[UploadFile] = File(None),
    language_code: str = Form("hi-IN"),
):
    """
    Accepts an uploaded audio file (WAV/PCM/MP3) or raw binary audio body,
    routes to Gnani Prisma v3.0 with 440+ Indian culinary keyterms, and returns transcription.
    """
    audio_bytes: bytes = b""

    if file is not None:
        audio_bytes = await file.read()
    else:
        # Check raw body stream
        body = await request.body()
        if body:
            audio_bytes = body

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="No audio payload provided. Upload a file or send raw 16kHz WAV bytes."
        )

    logger.info(f"Received audio payload for transcription ({len(audio_bytes)} bytes, lang={language_code})")
    stt_res = stt_client.transcribe_audio(audio_bytes, language_code=language_code)

    if stt_res.get("status") == "error":
        raise HTTPException(
            status_code=stt_res.get("status_code", 500),
            detail=stt_res.get("message", "Transcription failed.")
        )

    return {
        "status": "success",
        "transcript": stt_res.get("transcript", ""),
        "language": language_code,
        "confidence": stt_res.get("raw", {}).get("confidence", 0.95),
        "keyterms_boosted": len(stt_client.get_custom_keyterms()),
        "raw": stt_res.get("raw", {}),
    }


@app.post("/api/analyze")
async def analyze_meal_endpoint(payload: AnalyzeRequest):
    """
    Executes the ICMR-NIN metabolic engine on the meal description.
    Applies context multipliers (home vs mess vs canteen), computes macros,
    evaluates carb-to-protein ratio and glycemic spike risks, and suggests budget swaps.
    """
    input_text = payload.text or payload.meal_text or ""
    if not input_text.strip():
        raise HTTPException(status_code=400, detail="Meal text cannot be empty.")

    logger.info(f"Analyzing meal: \"{input_text}\"")
    report: MetabolicReport = engine.parse_transcript(input_text)

    # Format Itemized List
    items_data = []
    for item in report.items:
        items_data.append({
            "id": item.id,
            "name_en": item.name_en,
            "name_hi": item.name_hi,
            "name_mr": item.name_mr,
            "category": item.category,
            "quantity": item.quantity,
            "unit": item.unit,
            "total_grams": item.total_grams,
            "calories": item.scaled_calories,
            "protein_g": item.scaled_protein_g,
            "carbs_g": item.scaled_carbs_g,
            "fat_g": item.scaled_fat_g,
            "fiber_g": item.scaled_fiber_g,
            "glycemic_index": item.glycemic_index,
            "glycemic_spike_risk": item.glycemic_spike_risk,
            "sugar_content_g": round(item.sugar_content_g, 1),
            "is_fried": item.is_fried,
            "is_refined_carb": item.is_refined_carb,
            "icmr_source": item.icmr_source,
            "metabolic_notes": item.metabolic_notes,
        })

    return {
        "status": "success",
        "input_text": report.input_text,
        "detected_context": report.detected_context,
        "context_description": report.context_description,
        "context_multipliers": report.context_multipliers,
        "items": items_data,
        "totals": {
            "calories": report.total_calories,
            "protein_g": report.total_protein_g,
            "carbs_g": report.total_carbs_g,
            "fat_g": report.total_fat_g,
            "fiber_g": report.total_fiber_g,
        },
        "reality_check": {
            "protein_to_carb_ratio": report.reality_check.protein_to_carb_ratio,
            "carb_to_protein_ratio": report.reality_check.carb_to_protein_ratio,
            "ratio_status": report.reality_check.ratio_status,
            "glycemic_spike_risk": report.reality_check.glycemic_spike_risk,
            "hidden_sugar_flags": report.reality_check.hidden_sugar_flags,
            "acidity_flags": report.reality_check.acidity_flags,
            "budget_protein_swaps": report.reality_check.budget_protein_swaps,
        },
        "spoken_summaries": {
            "devansh": report.spoken_summary_devansh,
            "shivani": report.spoken_summary_shivani,
        },
    }


@app.post("/api/coach")
async def coach_speech_endpoint(payload: CoachRequest):
    """
    Synthesizes conversational Indic voice coaching using Gnani Timbre v3.0
    with expressive vocal tags (<excited>, <laugh>) for Devansh or Shivani.
    Returns audio URL for instant browser playback.
    """
    persona = payload.persona or "Devansh"
    language = payload.language or "hi-IN"
    text_to_speak = payload.text

    # If text not explicitly supplied, extract from meal_text
    if not text_to_speak:
        if payload.meal_text:
            rep = engine.parse_transcript(payload.meal_text)
            text_to_speak = (
                rep.spoken_summary_devansh
                if persona.lower() == "devansh"
                else rep.spoken_summary_shivani
            )
        else:
            text_to_speak = "Namaste. Aahar-Vaani mein aapka swagat hai."

    filename = f"reply_{persona.lower()}_{int(time.time() * 1000)}.wav"
    out_path = os.path.join(TEMP_AUDIO_DIR, filename)

    audio_file = tts_client.synthesize_speech(
        text=text_to_speak,
        persona=persona,
        language=language,
        output_path=out_path,
    )

    file_size = os.path.getsize(audio_file) if os.path.exists(audio_file) else 0

    return {
        "status": "success",
        "persona": persona,
        "language": language,
        "script": text_to_speak,
        "audio_url": f"/api/audio/{filename}",
        "file_size": file_size,
    }


@app.get("/api/audio/{filename}")
async def get_audio_file(filename: str):
    """Serves synthesized WAV audio files for instant playback."""
    file_path = os.path.join(TEMP_AUDIO_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found or expired.")
    return FileResponse(file_path, media_type="audio/wav")


# --- Static Files & Single-Page Dashboard Mount ---
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount static/ directory directly at root with html=True
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Launching Aahar-Vaani Production Server on http://localhost:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
