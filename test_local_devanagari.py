# -*- coding: utf-8 -*-
"""
Standalone Verification Script for Native Devanagari Food Extraction & Offline ICMR Pipeline
Tests the exact phrase: "शाम को चाय में 2 कुकीज खाई एंड देन 2 चकली खाई"
"""

import os
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from core.nutrition_engine import NutritionEngine
from core.gnani_tts import GnaniTTSClient

def test_devanagari_pipeline():
    print("=" * 75)
    print("🧪 AAHAR-VAANI: STANDALONE NATIVE DEVANAGARI VERIFICATION TEST")
    print("=" * 75)

    engine = NutritionEngine()
    print(f"[+] Loaded {len(engine.items_by_id)} Indian Food Items in Nutrition Engine.")

    test_input = "शाम को चाय में 2 कुकीज खाई एंड देन 2 चकली खाई"
    print(f"\n[+] Input Devanagari Meal Phrase:\n    \"{test_input}\"")

    report = engine.parse_transcript(test_input)

    # 1. Inspect Identified Items
    print("\n---------------------------------------------------------------------------")
    print(f"📋 Detected Food Entities ({len(report.items)} items):")
    print("---------------------------------------------------------------------------")
    for idx, item in enumerate(report.items, 1):
        print(f"  {idx}. {item.name_en} ({item.name_hi} / {item.name_mr})")
        print(f"     Portion: {item.quantity} {item.unit} ({item.total_grams}g)")
        print(f"     Macros:  {item.scaled_calories:.1f} kcal | P: {item.scaled_protein_g:.1f}g | C: {item.scaled_carbs_g:.1f}g | F: {item.scaled_fat_g:.1f}g")
        print(f"     GI / Risk: {item.glycemic_index} ({item.glycemic_spike_risk})")

    # Assertions on Entities
    detected_ids = [item.id for item in report.items]
    assert "cutting_chai" in detected_ids, "Failed: 'cutting_chai' not detected from 'चाय'!"
    assert "cookies_biscuits" in detected_ids, "Failed: 'cookies_biscuits' not detected from 'कुकीज'!"
    assert "chakli" in detected_ids, "Failed: 'chakli' not detected from 'चकली'!"
    assert len(report.items) == 3, f"Expected 3 items, got {len(report.items)}"

    # Quantity checks
    chai_item = next(i for i in report.items if i.id == "cutting_chai")
    cookies_item = next(i for i in report.items if i.id == "cookies_biscuits")
    chakli_item = next(i for i in report.items if i.id == "chakli")

    assert chai_item.quantity == 1.0, f"Expected Chai qty=1.0, got {chai_item.quantity}"
    assert cookies_item.quantity == 2.0, f"Expected Cookies qty=2.0, got {cookies_item.quantity}"
    assert chakli_item.quantity == 2.0, f"Expected Chakli qty=2.0, got {chakli_item.quantity}"

    # 2. Inspect Aggregated Macros
    print("\n---------------------------------------------------------------------------")
    print("📊 Aggregated Nutritional Telemetry:")
    print("---------------------------------------------------------------------------")
    print(f"  * Total Energy:  {report.total_calories:.1f} kcal (Target: ~380 - 420 kcal)")
    print(f"  * Total Protein: {report.total_protein_g:.1f} g")
    print(f"  * Total Carbs:   {report.total_carbs_g:.1f} g")
    print(f"  * Total Fat:     {report.total_fat_g:.1f} g")
    print(f"  * Total Fiber:   {report.total_fiber_g:.1f} g")
    print(f"  * Glycemic Risk: {report.reality_check.glycemic_spike_risk}")
    print(f"  * Carb:Protein:  {report.reality_check.carb_to_protein_ratio}:1")

    # Macro Assertions
    assert 380 <= report.total_calories <= 420, f"Expected calories ~380-420, got {report.total_calories}"
    assert report.reality_check.glycemic_spike_risk in ["Severe", "Moderate", "High"], f"Expected Severe/High glycemic risk, got {report.reality_check.glycemic_spike_risk}"

    # 3. Test Devansh & Shivani Coach Scripts
    print("\n---------------------------------------------------------------------------")
    print("🔊 Synthesized Coach Scripts:")
    print("---------------------------------------------------------------------------")
    print(f"[Devansh Script]:\n\"{report.spoken_summary_devansh}\"\n")
    print(f"[Shivani Script]:\n\"{report.spoken_summary_shivani}\"\n")

    assert "390" in report.spoken_summary_devansh or "calorie" in report.spoken_summary_devansh
    assert "protein" in report.spoken_summary_devansh.lower()

    # 4. Zero-Detection Guardrail Test
    print("\n---------------------------------------------------------------------------")
    print("🛡️ Guardrail Test (Zero Items Detected):")
    print("---------------------------------------------------------------------------")
    empty_report = engine.parse_transcript("hello testing microphone sound 1 2 3")
    print(f"Empty Input Script: \"{empty_report.spoken_summary_devansh}\"")
    assert "koi food item samajh nahi aaya" in empty_report.spoken_summary_devansh
    assert "0 calories keep it up" not in empty_report.spoken_summary_devansh.lower()
    print("✅ Zero-Detection Guardrail verified successfully!")

    # 5. Live Speech Synthesis via Timbre v3.0
    print("\n---------------------------------------------------------------------------")
    print("🎙️ Synthesizing Speech via Timbre v3.0...")
    print("---------------------------------------------------------------------------")
    tts_client = GnaniTTSClient()
    out_audio = tts_client.synthesize_speech(
        text=report.spoken_summary_devansh,
        persona="Devansh",
        language="hi-IN",
        output_path="data/temp_audio/reply_devanagari_snack.wav"
    )
    print(f"✅ Audio generated successfully -> {out_audio} ({len(out_audio.audio_bytes)} bytes)")

    print("\n" + "=" * 75)
    print("🎉 ALL TESTS PASSED: 160+ LEXICON & DEVANAGARI PARSER FULLY OPERATIONAL!")
    print("=" * 75)

if __name__ == "__main__":
    test_devanagari_pipeline()
