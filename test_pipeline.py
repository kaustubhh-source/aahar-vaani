"""
Aahar-Vaani (आहार-वाणी) End-to-End Core Backend Smoke Test
Demonstrates the full pipeline:
1. Food Lexicon & Keyterm generation
2. Prisma v3.0 STT Connector
3. ICMR-NIN Metabolic & Clinical Nutrition Engine
4. Context Multiplier Application (Home vs Mess vs Canteen/Thela)
5. Timbre v3.0 Voice Synthesis (Personas: Devansh & Shivani)
"""

import os
import sys

# Ensure UTF-8 output encoding for Windows terminals
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from core.gnani_stt import GnaniSTTClient
from core.gnani_tts import GnaniTTSClient
from core.nutrition_engine import NutritionEngine


def run_smoke_test():
    print("=" * 75)
    print("🥗 AAHAR-VAANI (आहार-वाणी) — CORE BACKEND SMOKE TEST")
    print("=" * 75)

    # 1. Initialize Clients
    stt_client = GnaniSTTClient()
    tts_client = GnaniTTSClient()
    engine = NutritionEngine()

    print(f"\n[+] Lexicon Loaded: {len(engine.items_by_id)} Indian Food Items")
    keyterms = stt_client.get_custom_keyterms()
    print(f"[+] Prisma v3.0 Keyterms Generated: {len(keyterms)} domain accuracy hints")
    print(f"    Sample Keyterms: {keyterms[:8]}...")

    # 2. Simulated Speech-to-Text Input
    sample_speech_text = "Subah do plate poha aur ek cutting chai li canteen mein"
    print(f"\n[+] Input Meal Transcript (Simulated Voice/Text):")
    print(f"    \"{sample_speech_text}\"")

    # 3. Metabolic Nutrition Engine Analysis
    report = engine.parse_transcript(sample_speech_text)

    print("\n" + "-" * 75)
    print("📊 1. PREPARATION CONTEXT & MACRO REPORT")
    print("-" * 75)
    print(f"Detected Context:       {report.detected_context.upper()}")
    print(f"Context Description:    {report.context_description}")
    print(f"Multipliers Applied:    Oil/Fat={report.context_multipliers['oil_fat']}x, "
          f"Carbs={report.context_multipliers['carbs']}x, Protein={report.context_multipliers['protein']}x")

    print("\n[Itemized Breakdown]:")
    for idx, item in enumerate(report.items, start=1):
        print(f"  {idx}. {item.name_en} ({item.name_mr})")
        print(f"     Portion:    {item.quantity} {item.unit} ({int(item.total_grams)}g)")
        print(f"     Macros:     {item.scaled_calories:.1f} kcal | "
              f"P: {item.scaled_protein_g:.1f}g | C: {item.scaled_carbs_g:.1f}g | "
              f"F: {item.scaled_fat_g:.1f}g | Fib: {item.scaled_fiber_g:.1f}g")
        print(f"     GI / Spike: {item.glycemic_index} / {item.glycemic_spike_risk}")

    print("\n[Meal Totals]:")
    print(f"  * Total Energy:  {report.total_calories:.1f} kcal")
    print(f"  * Total Protein: {report.total_protein_g:.1f} g")
    print(f"  * Total Carbs:   {report.total_carbs_g:.1f} g")
    print(f"  * Total Fat:     {report.total_fat_g:.1f} g")
    print(f"  * Total Fiber:   {report.total_fiber_g:.1f} g")

    # 4. ICMR Reality Check
    rc = report.reality_check
    print("\n" + "-" * 75)
    print("🩺 2. ICMR-NIN REALITY CHECK & METABOLIC FLAGS")
    print("-" * 75)
    print(f"Protein-to-Carb Ratio:   {rc.protein_to_carb_ratio} (Ideal >= 0.40)")
    print(f"Carb-to-Protein Ratio:   {rc.carb_to_protein_ratio}:1 (ICMR <= 2.5:1)")
    print(f"Ratio Status:            {rc.ratio_status}")
    print(f"Glycemic Spike Risk:     {rc.glycemic_spike_risk.upper()}")

    if rc.hidden_sugar_flags:
        print("\nHidden Sugar Flags:")
        for flag in rc.hidden_sugar_flags:
            print(f"  {flag}")

    if rc.acidity_flags:
        print("\nAcidity & Digestive Warnings:")
        for flag in rc.acidity_flags:
            print(f"  {flag}")

    if rc.budget_protein_swaps:
        print("\nBudget Protein & Healthy Swaps:")
        for swap in rc.budget_protein_swaps:
            print(f"  - {swap}")

    # 5. Timbre v3.0 Voice Synthesis
    print("\n" + "-" * 75)
    print("🔊 3. TIMBRE v3.0 VOICE COACH SYNTHESIS")
    print("-" * 75)

    print("\n[Persona 1: Devansh (Youth / Hostel Dost)]")
    print(f"Script: \"{report.spoken_summary_devansh}\"")
    devansh_audio = tts_client.synthesize_speech(
        text=report.spoken_summary_devansh,
        persona="Devansh",
        language="hi-IN",
        output_path="data/temp_audio/reply_devansh.wav"
    )
    print(f"Audio Saved -> {devansh_audio} ({os.path.getsize(devansh_audio)} bytes)")

    print("\n[Persona 2: Shivani (Family / Elder Care)]")
    print(f"Script: \"{report.spoken_summary_shivani}\"")
    shivani_audio = tts_client.synthesize_speech(
        text=report.spoken_summary_shivani,
        persona="Shivani",
        language="hi-IN",
        output_path="data/temp_audio/reply_shivani.wav"
    )
    print(f"Audio Saved -> {shivani_audio} ({os.path.getsize(shivani_audio)} bytes)")

    # Standard default reply.wav as requested
    tts_client.synthesize_speech(
        text=report.spoken_summary_devansh,
        persona="Devansh",
        language="hi-IN",
        output_path="data/temp_audio/reply.wav"
    )

    print("\n" + "=" * 75)
    print("✅ SMOKE TEST PASSED: ALL CORE BACKEND MODULES OPERATIONAL!")
    print("=" * 75)


if __name__ == "__main__":
    run_smoke_test()
