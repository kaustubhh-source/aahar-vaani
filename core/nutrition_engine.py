"""
ICMR-NIN Nutrition Engine & Metabolic Audit
Parses Indian meal transcripts, maps street & mess portion units,
computes glycemic load, and generates clinical metabolic recommendations
aligned with ICMR-NIN (National Institute of Nutrition, Hyderabad) guidelines.
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple

try:
    from pydantic import BaseModel, Field
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    from dataclasses import dataclass, field

logger = logging.getLogger("AaharVaani.Nutrition")

if HAS_PYDANTIC:
    class FoodItemMatch(BaseModel):
        """Represents an identified Indian food item in a meal."""
        id: str
        name_en: str
        name_hi: str
        category: str
        quantity: float
        unit: str
        grams: float
        calories_kcal: float
        carbs_g: float
        protein_g: float
        fat_g: float
        fiber_g: float
        glycemic_index: float
        glycemic_load: float
        icmr_source: str
        metabolic_notes: str

    class MetabolicAuditResult(BaseModel):
        """Comprehensive metabolic health audit for an Indian meal."""
        items: List[FoodItemMatch]
        total_calories_kcal: float
        total_carbs_g: float
        total_protein_g: float
        total_fat_g: float
        total_fiber_g: float
        carb_protein_ratio: float
        average_glycemic_index: float
        total_glycemic_load: float
        glycemic_tier: str  # 'Low', 'Moderate', 'High', 'Severe Spike Risk'
        icmr_compliance_score: int  # 0 to 100
        metabolic_warnings: List[str]
        coaching_recommendations: List[str]
        spoken_summary_hi: str
        spoken_summary_en: str
else:
    @dataclass
    class FoodItemMatch:
        id: str
        name_en: str
        name_hi: str
        category: str
        quantity: float
        unit: str
        grams: float
        calories_kcal: float
        carbs_g: float
        protein_g: float
        fat_g: float
        fiber_g: float
        glycemic_index: float
        glycemic_load: float
        icmr_source: str
        metabolic_notes: str

    @dataclass
    class MetabolicAuditResult:
        items: List[FoodItemMatch]
        total_calories_kcal: float
        total_carbs_g: float
        total_protein_g: float
        total_fat_g: float
        total_fiber_g: float
        carb_protein_ratio: float
        average_glycemic_index: float
        total_glycemic_load: float
        glycemic_tier: str
        icmr_compliance_score: int
        metabolic_warnings: List[str]
        coaching_recommendations: List[str]
        spoken_summary_hi: str
        spoken_summary_en: str


class NutritionEngine:
    """
    Core Nutrition and Metabolic Engine.
    Handles lexicon lookup, Indic unit parsing, and ICMR-NIN audits.
    """

    UNIT_MULTIPLIERS = {
        "katori": 1.0,      # Default standard katori (~150g)
        "cutori": 1.0,
        "bowl": 1.0,
        "chammach": 0.1,    # Spoon (~15g)
        "spoon": 0.1,
        "plate": 1.0,       # Standard plate portion
        "full plate": 1.5,
        "half plate": 0.5,
        "glass": 1.0,       # Standard glass (~200ml)
        "cup": 0.8,         # Standard cup (~150ml)
        "piece": 1.0,       # Unit piece (e.g. 1 roti, 1 samosa)
        "tukda": 1.0,
        "thali": 1.0,       # Full composite meal
    }

    HINDI_NUMBERS = {
        "ek": 1.0, "do": 2.0, "teen": 3.0, "tin": 3.0, "chaar": 4.0, "char": 4.0,
        "paanch": 5.0, "panch": 5.0, "chhah": 6.0, "chhe": 6.0, "saat": 7.0,
        "aath": 8.0, "nau": 9.0, "dus": 10.0, "das": 10.0,
        "aadha": 0.5, "adha": 0.5, "half": 0.5,
        "paanv": 0.25, "paav": 0.25,
        "dhedh": 1.5, "dhed": 1.5,
        "dhai": 2.5,
        "sawa": 1.25,
        "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0, "five": 5.0,
        "six": 6.0, "seven": 7.0, "eight": 8.0, "nine": 9.0, "ten": 10.0,
    }

    def __init__(self, lexicon_path: Optional[str] = None):
        self.lexicon_path = lexicon_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "food_lexicon.json"
        )
        self.items_by_id: Dict[str, Dict[str, Any]] = {}
        self.alias_to_item: Dict[str, Dict[str, Any]] = {}
        self._load_lexicon()

    def _load_lexicon(self):
        """Loads food lexicon data and builds fast lookup indices."""
        if not os.path.exists(self.lexicon_path):
            logger.error(f"Food lexicon file missing at {self.lexicon_path}")
            return

        with open(self.lexicon_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            items = data.get("items", [])
            for item in items:
                self.items_by_id[item["id"]] = item
                self.alias_to_item[item["id"].lower()] = item
                self.alias_to_item[item["name_en"].lower()] = item
                self.alias_to_item[item["name_hi"].strip().lower()] = item
                for alias in item.get("aliases", []):
                    self.alias_to_item[alias.lower().strip()] = item

        logger.info(f"Loaded {len(self.items_by_id)} Indian food items into Nutrition Engine.")

    def parse_quantity_and_unit(self, text: str) -> Tuple[float, str]:
        """Extracts numerical quantity and portion unit from phrase."""
        qty = 1.0
        unit = "piece"

        # Check for numeric digits
        num_match = re.search(r"(\d+(?:\.\d+)?)", text)
        if num_match:
            try:
                qty = float(num_match.group(1))
            except ValueError:
                qty = 1.0
        else:
            # Check Hindi/English number words
            for word, val in self.HINDI_NUMBERS.items():
                pattern = r"\b" + re.escape(word) + r"\b"
                if re.search(pattern, text, re.IGNORECASE):
                    qty = val
                    break

        # Check for units
        for u in self.UNIT_MULTIPLIERS.keys():
            pattern = r"\b" + re.escape(u) + r"\b"
            if re.search(pattern, text, re.IGNORECASE):
                unit = u
                break

        return qty, unit

    def parse_transcript(self, transcript: str) -> List[FoodItemMatch]:
        """
        Parses free-form spoken text into structured food matches with quantities.
        Example: "Maine do katori dal tadka, 3 roti aur ek plate salad khaya"
        """
        matches: List[FoodItemMatch] = []
        lower_text = transcript.lower()

        # Sort alias keys by length descending to prioritize multi-word matches
        sorted_aliases = sorted(self.alias_to_item.keys(), key=len, reverse=True)
        matched_spans = []

        for alias in sorted_aliases:
            pattern = r"\b" + re.escape(alias) + r"\b"
            for m in re.finditer(pattern, lower_text):
                start, end = m.span()
                # Ensure no overlapping matches
                if any(s <= start < e or s < end <= e for s, e in matched_spans):
                    continue

                matched_spans.append((start, end))
                food_dict = self.alias_to_item[alias]

                # Look for quantity/unit in the preceding 35 characters
                context_window_start = max(0, start - 35)
                context_prefix = lower_text[context_window_start:start]
                qty, unit = self.parse_quantity_and_unit(context_prefix)

                # Fallback to default unit if none detected in prefix
                if unit == "piece" and food_dict.get("default_unit") != "piece":
                    unit = food_dict.get("default_unit", "piece")

                unit_scale = self.UNIT_MULTIPLIERS.get(unit, 1.0)
                scaling_factor = qty * unit_scale

                base_grams = float(food_dict.get("serving_grams", 100))
                grams = round(base_grams * scaling_factor, 1)

                calories = round(float(food_dict.get("calories_kcal", 0)) * scaling_factor, 1)
                carbs = round(float(food_dict.get("carbs_g", 0)) * scaling_factor, 1)
                protein = round(float(food_dict.get("protein_g", 0)) * scaling_factor, 1)
                fat = round(float(food_dict.get("fat_g", 0)) * scaling_factor, 1)
                fiber = round(float(food_dict.get("fiber_g", 0)) * scaling_factor, 1)
                gi = float(food_dict.get("glycemic_index", 50))
                gl = round((gi * carbs) / 100.0, 1)

                item_match = FoodItemMatch(
                    id=food_dict["id"],
                    name_en=food_dict["name_en"],
                    name_hi=food_dict["name_hi"],
                    category=food_dict.get("category", "general"),
                    quantity=qty,
                    unit=unit,
                    grams=grams,
                    calories_kcal=calories,
                    carbs_g=carbs,
                    protein_g=protein,
                    fat_g=fat,
                    fiber_g=fiber,
                    glycemic_index=gi,
                    glycemic_load=gl,
                    icmr_source=food_dict.get("icmr_source", "IFCT-2017"),
                    metabolic_notes=food_dict.get("metabolic_notes", ""),
                )
                matches.append(item_match)

        return matches

    def audit_meal(self, items: List[FoodItemMatch]) -> MetabolicAuditResult:
        """
        Runs an ICMR-NIN metabolic audit on the logged food items.
        Evaluates macronutrient distribution, glycemic excursion risk,
        and compliance score.
        """
        if not items:
            return MetabolicAuditResult(
                items=[],
                total_calories_kcal=0.0,
                total_carbs_g=0.0,
                total_protein_g=0.0,
                total_fat_g=0.0,
                total_fiber_g=0.0,
                carb_protein_ratio=0.0,
                average_glycemic_index=0.0,
                total_glycemic_load=0.0,
                glycemic_tier="Empty",
                icmr_compliance_score=100,
                metabolic_warnings=["Koi aahar pehchana nahi gaya. Kripya punah bole ya likhein."],
                coaching_recommendations=["Boliye jaise: '2 katori dal, 2 roti aur kachumber salad'."],
                spoken_summary_hi="कृपया अपने भोजन की सामग्री बताएं ताकि हम पोषण का विश्लेषण कर सकें।",
                spoken_summary_en="Please log your food items to perform a metabolic audit.",
            )

        total_cal = round(sum(i.calories_kcal for i in items), 1)
        total_carbs = round(sum(i.carbs_g for i in items), 1)
        total_prot = round(sum(i.protein_g for i in items), 1)
        total_fat = round(sum(i.fat_g for i in items), 1)
        total_fiber = round(sum(i.fiber_g for i in items), 1)

        carb_protein_ratio = (
            round(total_carbs / total_prot, 2) if total_prot > 0 else round(total_carbs, 2)
        )

        total_gl = round(sum(i.glycemic_load for i in items), 1)

        if total_carbs > 0:
            avg_gi = round(sum(i.glycemic_index * i.carbs_g for i in items) / total_carbs, 1)
        else:
            avg_gi = 0.0

        if total_gl <= 10:
            glycemic_tier = "Low"
        elif 10 < total_gl <= 19:
            glycemic_tier = "Moderate"
        elif 20 <= total_gl <= 35:
            glycemic_tier = "High"
        else:
            glycemic_tier = "Severe Spike Risk"

        warnings: List[str] = []
        recommendations: List[str] = []
        score = 100

        # 1. ICMR-NIN Carb-to-Protein Ratio Check (Ideal <= 2.5 : 1)
        if carb_protein_ratio > 5.0:
            score -= 25
            warnings.append(
                f"अत्यधिक कार्बोहाइड्रेट भार (Carb:Protein ratio = {carb_protein_ratio}:1). ICMR-NIN के अनुसार 2.5:1 से कम होना चाहिए।"
            )
            recommendations.append(
                "भोजन में 1 कटोरी अतिरिक्त दाल, भुना चना या दही शामिल करके प्रोटीन अनुपात सुधारें।"
            )
        elif carb_protein_ratio > 3.5:
            score -= 15
            warnings.append(
                f"मध्यम कार्बोहाइड्रेट अधिकता (Carb:Protein ratio = {carb_protein_ratio}:1)."
            )
            recommendations.append(
                "रोटी/चावल की मात्रा आधी कर के सब्जी या दाल की मात्रा बढ़ाएं।"
            )

        # 2. Glycemic Load Check
        if glycemic_tier in ["High", "Severe Spike Risk"]:
            score -= 25
            warnings.append(
                f"उच्च ग्लाइसेमिक लोड ({total_gl})! भोजन के 45-60 मिनट बाद रक्त शर्करा में तीव्र उछाल आ सकता है।"
            )
            recommendations.append(
                "भोजन क्रम रणनीति (Meal Sequencing): पहले सलाद या छाछ पिएं, फिर दाल/सब्जी और अंत में रोटी/चावल खाएं। इससे ग्लूकोज स्पाइक 35% कम होगा।"
            )
        elif glycemic_tier == "Moderate":
            score -= 5

        # 3. Dietary Fiber Check (ICMR recommends minimum 8-10g per main meal)
        if total_fiber < 4.0:
            score -= 20
            warnings.append(
                f"आहार फाइबर की अत्यधिक कमी ({total_fiber}g). भोजन के पाचन में तीव्रता होगी।"
            )
            recommendations.append(
                "कच्चा कचुंबर सलाद (खीरा, टमाटर, प्याज) या हरी पत्तेदार सब्जी अवश्य जोड़ें।"
            )
        elif total_fiber < 8.0:
            score -= 10
            recommendations.append("फाइबर बढ़ाने के लिए भुने मखाने या साबुत दालें प्राथमिकता दें।")

        # 4. Caloric density check
        if total_cal > 850:
            score -= 15
            warnings.append(f"भारी कैलोरी भार ({total_cal} kcal) एक ही भोजन में।")
            recommendations.append("डीप फ्राइड स्नैक्स या अत्यधिक घी/मक्खन का सीमित प्रयोग करें।")

        score = max(20, min(100, score))

        if score >= 80:
            spoken_hi = (
                f"शाबाश! आपका भोजन पोषण संतुलन में बहुत अच्छा है। कुल {int(total_cal)} कैलोरी और "
                f"{int(total_prot)} ग्राम प्रोटीन मिला है। ग्लाइसेमिक लोड {glycemic_tier} स्तर पर सुरक्षित है।"
            )
            spoken_en = (
                f"Great job! Your meal has a high ICMR metabolic score of {score}/100 with "
                f"{int(total_cal)} calories and {int(total_prot)}g protein."
            )
        elif score >= 60:
            spoken_hi = (
                f"आपका भोजन ठीक है, लेकिन कार्बोहाइड्रेट का अनुपात थोड़ा अधिक है। कुल कैलोरी {int(total_cal)} है। "
                f"ग्लूकोज नियंत्रण के लिए पहले दाल और सलाद खाने की सलाह दी जाती है।"
            )
            spoken_en = (
                f"Your meal is moderately balanced with a score of {score}/100. "
                f"Consider adding more dal or curd to balance the {carb_protein_ratio}:1 carb-to-protein ratio."
            )
        else:
            spoken_hi = (
                f"सावधान! इस भोजन का ग्लाइसेमिक लोड {total_gl} बहुत अधिक है। "
                f"रक्त शर्करा स्पाइक से बचने के लिए तुरंत छाछ या खीरा सलाद साथ लें।"
            )
            spoken_en = (
                f"Alert: This meal carries a high glycemic load of {total_gl}. "
                f"Sequence your food by consuming fiber and protein before simple carbohydrates."
            )

        return MetabolicAuditResult(
            items=items,
            total_calories_kcal=total_cal,
            total_carbs_g=total_carbs,
            total_protein_g=total_prot,
            total_fat_g=total_fat,
            total_fiber_g=total_fiber,
            carb_protein_ratio=carb_protein_ratio,
            average_glycemic_index=avg_gi,
            total_glycemic_load=total_gl,
            glycemic_tier=glycemic_tier,
            icmr_compliance_score=score,
            metabolic_warnings=warnings,
            coaching_recommendations=recommendations,
            spoken_summary_hi=spoken_hi,
            spoken_summary_en=spoken_en,
        )
