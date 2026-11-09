"""
ICMR-NIN Metabolic Nutrition Engine & Clinical Auditor
Parses Indian meal logs in Hinglish and Marathi, applies preparation context multipliers
(home vs hostel mess vs canteen/thela), computes macro distribution, and evaluates
metabolic health metrics according to ICMR-NIN IFCT-2017 standards.
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("AaharVaani.Nutrition")


@dataclass
class MatchedFoodItem:
    """Represents an identified Indian food item with scaled nutritional profile."""
    id: str
    name_en: str
    name_hi: str
    name_mr: str
    category: str
    quantity: float
    unit: str
    unit_grams: float
    total_grams: float
    # Base unscaled per-serving values
    base_calories: float
    base_protein_g: float
    base_carbs_g: float
    base_fat_g: float
    base_fiber_g: float
    glycemic_index: str  # 'Low', 'Medium', 'High'
    glycemic_spike_risk: str  # 'Low', 'Moderate', 'Severe'
    sugar_content_g: float
    is_fried: bool
    is_refined_carb: bool
    icmr_source: str
    metabolic_notes: str
    # Context & portion scaled values
    scaled_calories: float = 0.0
    scaled_protein_g: float = 0.0
    scaled_carbs_g: float = 0.0
    scaled_fat_g: float = 0.0
    scaled_fiber_g: float = 0.0


@dataclass
class ICMRRealityCheck:
    """Evaluates nutritional balance against ICMR-NIN clinical benchmarks."""
    protein_to_carb_ratio: float  # e.g., 0.12 (Ideal >= 0.40 or 1:2.5)
    carb_to_protein_ratio: float  # e.g., 8.3:1 (Typical Indian carb heavy)
    ratio_status: str             # "Balanced" or "Severe Carb-Heavy Imbalance"
    glycemic_spike_risk: str      # 'Low', 'Moderate', 'Severe'
    hidden_sugar_flags: List[str] = field(default_factory=list)
    acidity_flags: List[str] = field(default_factory=list)
    budget_protein_swaps: List[str] = field(default_factory=list)


@dataclass
class MetabolicReport:
    """Aggregated nutritional and clinical metabolic report."""
    input_text: str
    detected_context: str  # 'home', 'mess', 'canteen_thela'
    context_description: str
    context_multipliers: Dict[str, float]
    items: List[MatchedFoodItem]
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    total_fiber_g: float
    reality_check: ICMRRealityCheck
    spoken_summary_devansh: str
    spoken_summary_shivani: str

    @property
    def total_calories_kcal(self) -> float:
        return self.total_calories

    @property
    def carb_protein_ratio(self) -> float:
        return self.reality_check.carb_to_protein_ratio

    @property
    def glycemic_tier(self) -> str:
        return self.reality_check.glycemic_spike_risk

    @property
    def total_glycemic_load(self) -> float:
        # Approximate meal glycemic load based on items
        return round(sum(
            (70.0 if i.glycemic_index == "High" else (50.0 if i.glycemic_index == "Medium" else 30.0))
            * i.scaled_carbs_g / 100.0 for i in self.items
        ), 1)

    @property
    def icmr_compliance_score(self) -> int:
        score = 100
        if self.reality_check.glycemic_spike_risk == "Severe":
            score -= 30
        elif self.reality_check.glycemic_spike_risk == "Moderate":
            score -= 15
        if self.reality_check.carb_to_protein_ratio > 6.0:
            score -= 30
        elif self.reality_check.carb_to_protein_ratio > 3.0:
            score -= 15
        if self.reality_check.hidden_sugar_flags:
            score -= 15
        return max(20, min(100, score))

    @property
    def metabolic_warnings(self) -> List[str]:
        return self.reality_check.hidden_sugar_flags + self.reality_check.acidity_flags

    @property
    def coaching_recommendations(self) -> List[str]:
        return self.reality_check.budget_protein_swaps

    @property
    def spoken_summary_hi(self) -> str:
        return self.spoken_summary_shivani

    @property
    def spoken_summary_en(self) -> str:
        return self.spoken_summary_devansh



class NutritionEngine:
    """
    Core Metabolic & Clinical Nutrition Engine.
    Handles lexicon indexing, Hinglish/Marathi entity parsing,
    preparation multipliers, and ICMR reality checks.
    """

    HINDI_MARATHI_NUMBERS = {
        # Devanagari Numerals & Hindi/Marathi Number Words
        "एक": 1.0, "दोन": 2.0, "दो": 2.0, "तीन": 3.0, "चार": 4.0,
        "पांच": 5.0, "पाच": 5.0, "छह": 6.0, "सहा": 6.0, "सात": 7.0,
        "आठ": 8.0, "नौ": 9.0, "नऊ": 9.0, "दस": 10.0, "दहा": 10.0,
        "आधा": 0.5, "अर्धा": 0.5, "पाव": 0.25, "डेढ़": 1.5, "दीड": 1.5,
        "ढाई": 2.5, "अडीच": 2.5, "सवा": 1.25,
        "१": 1.0, "२": 2.0, "३": 3.0, "४": 4.0, "५": 5.0,
        "६": 6.0, "७": 7.0, "८": 8.0, "९": 9.0, "१०": 10.0,
        # Hinglish & Marathi Transliterated words
        "ek": 1.0, "do": 2.0, "don": 2.0, "teen": 3.0, "tin": 3.0,
        "chaar": 4.0, "char": 4.0, "paanch": 5.0, "panch": 5.0, "paach": 5.0,
        "chhah": 6.0, "chhe": 6.0, "saha": 6.0, "saat": 7.0, "aath": 8.0,
        "nau": 9.0, "dus": 10.0, "das": 10.0, "daha": 10.0,
        # Fractions
        "aadha": 0.5, "adha": 0.5, "ardha": 0.5, "half": 0.5,
        "paanv": 0.25, "paav": 0.25, "quarter": 0.25,
        "dhedh": 1.5, "dhed": 1.5, "deed": 1.5,
        "dhai": 2.5, "adhich": 2.5,
        "sawa": 1.25,
        # English words
        "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0, "five": 5.0,
        "single": 1.0, "double": 2.0, "triple": 3.0,
    }

    # Preparation Context Keywords (Bilingual: Devanagari + Romanized)
    CONTEXT_PATTERNS = {
        "canteen_thela": [
            r"\bcanteen\b", r"\btapri\b", r"\bthela\b", r"\bthele\b", r"\bstall\b",
            r"\bstreet\b", r"\bbahar\b", r"\boutside\b", r"\bhotel\b", r"\bdhaba\b",
            r"\bdhabba\b", r"\btapri\s*var\b", r"\bcanteen\s*madhe\b", r"\bcanteen\s*mein\b",
            r"\bthele\s*pe\b", r"\bthelya\s*var\b",
            r"कैंटीन", r"कॅन्टीन", r"कन्टीन", r"टपरी", r"ठेला", r"ठेले", r"ठेलावर",
            r"होटल", r"हॉटेल", r"ढाबा", r"स्टॉल", r"बाहर", r"बाहेर"
        ],
        "mess": [
            r"\bmess\b", r"\bhostel\b", r"\bhostel\s*mess\b", r"\bdining\s*hall\b",
            r"\bmess\s*mein\b", r"\bmess\s*madhe\b", r"\bmess\s*cha\b", r"\bmess\s*che\b",
            r"\bhostel\s*chya\b",
            r"मेस", r"हॉस्टल", r"हॉस्टेल", r"डाइनिंग"
        ],
        "home": [
            r"\bghar\b", r"\bghari\b", r"\bhome\b", r"\bhomemade\b", r"\bghar\s*ka\b",
            r"\bgharcha\b", r"\bmummy\b", r"\baai\b", r"\baaine\b", r"\bmummy\s*ne\b",
            r"घर", r"घरी", r"घर का", r"घरचे", r"आई", r"आईने", r"मम्मी", r"मम्मीने"
        ]
    }

    def __init__(self, lexicon_path: Optional[str] = None):
        self.lexicon_path = lexicon_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "food_lexicon.json"
        )
        self.units: Dict[str, Any] = {}
        self.preparation_multipliers: Dict[str, Any] = {}
        self.items_by_id: Dict[str, Dict[str, Any]] = {}
        self.alias_to_item: Dict[str, Dict[str, Any]] = {}
        self._load_lexicon()

    def _load_lexicon(self):
        """Loads food lexicon data, units, and preparation multipliers."""
        if not os.path.exists(self.lexicon_path):
            logger.error(f"Food lexicon file missing at {self.lexicon_path}")
            return

        with open(self.lexicon_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.units = data.get("units", {})
        self.preparation_multipliers = data.get("preparation_multipliers", {
            "home": {"oil_fat_multiplier": 1.0, "carb_multiplier": 1.0, "protein_multiplier": 1.0},
            "mess": {"oil_fat_multiplier": 1.25, "carb_multiplier": 1.15, "protein_multiplier": 0.85},
            "canteen_thela": {"oil_fat_multiplier": 1.5, "carb_multiplier": 1.30, "protein_multiplier": 0.80}
        })

        items = data.get("items", [])
        for item in items:
            self.items_by_id[item["id"]] = item
            self.alias_to_item[item["id"].lower()] = item
            if item.get("name_en"):
                self.alias_to_item[item["name_en"].lower()] = item
            if item.get("name_hi"):
                self.alias_to_item[item["name_hi"].strip().lower()] = item
            if item.get("name_mr"):
                self.alias_to_item[item["name_mr"].strip().lower()] = item
            for alias in item.get("aliases", []):
                self.alias_to_item[alias.strip().lower()] = item

        logger.info(f"Loaded {len(self.items_by_id)} Indian food items into Nutrition Engine.")

    def detect_preparation_context(self, text: str) -> Tuple[str, Dict[str, float], str]:
        """
        Determines whether the meal was prepared at home, hostel mess, or street/canteen.
        Returns: (context_key, multipliers_dict, description)
        """
        lower_text = text.lower()

        for pattern in self.CONTEXT_PATTERNS["canteen_thela"]:
            if re.search(pattern, lower_text):
                cfg = self.preparation_multipliers.get("canteen_thela", {})
                return "canteen_thela", cfg, cfg.get("description", "Canteen / Tapri / Thela: 1.5x oil/fat multiplier, high refined carbs")

        for pattern in self.CONTEXT_PATTERNS["mess"]:
            if re.search(pattern, lower_text):
                cfg = self.preparation_multipliers.get("mess", {})
                return "mess", cfg, cfg.get("description", "Hostel / Office Mess: 1.25x oil/carb multiplier, lower bioavailable protein")

        for pattern in self.CONTEXT_PATTERNS["home"]:
            if re.search(pattern, lower_text):
                cfg = self.preparation_multipliers.get("home", {})
                return "home", cfg, cfg.get("description", "Home Cooked: 1.0x baseline grease/oil")

        cfg = self.preparation_multipliers.get("home", {
            "oil_fat_multiplier": 1.0, "carb_multiplier": 1.0, "protein_multiplier": 1.0
        })
        return "home", cfg, cfg.get("description", "Home Cooked: 1.0x baseline grease/oil")

    def parse_quantity_and_unit(self, prefix_text: str, default_unit: str = "plate") -> Tuple[float, str]:
        """Extracts numerical quantity and colloquial Indian portion unit from surrounding text."""
        qty = 1.0
        unit = default_unit

        b_start = r'(?<![a-zA-Z0-9\u0900-\u097F])'
        b_end = r'(?![a-zA-Z0-9\u0900-\u097F])'

        # 1. Search for numeric digits (e.g., 2, 2.5, 3)
        num_match = re.search(r"(\d+(?:\.\d+)?)", prefix_text)
        if num_match:
            try:
                qty = float(num_match.group(1))
            except ValueError:
                qty = 1.0
        else:
            # 2. Check for Devanagari numerals (e.g. १, २, ३)
            dev_digits = {"०": "0", "१": "1", "२": "2", "३": "3", "४": "4", "५": "5", "६": "6", "७": "7", "८": "8", "९": "9"}
            dev_match = re.search(r"([०-९]+(?:\.[०-९]+)?)", prefix_text)
            if dev_match:
                try:
                    eng_num = "".join(dev_digits.get(c, c) for c in dev_match.group(1))
                    qty = float(eng_num)
                except ValueError:
                    qty = 1.0
            else:
                # 3. Search for Hindi / Marathi / English number words
                for word, val in self.HINDI_MARATHI_NUMBERS.items():
                    pattern = b_start + re.escape(word) + b_end
                    if re.search(pattern, prefix_text, re.IGNORECASE):
                        qty = val
                        break

        # 4. Search for recognized units in prefix (English / Romanized)
        sorted_units = sorted(self.units.keys(), key=len, reverse=True)
        found_unit = False
        for u in sorted_units:
            u_clean = u.replace("-", r"[\s\-]?")
            pattern = b_start + u_clean + b_end
            if re.search(pattern, prefix_text, re.IGNORECASE):
                unit = u
                found_unit = True
                break

        # 5. Search for Devanagari unit equivalents
        if not found_unit:
            dev_unit_map = {
                "कटोरी": "katori", "वाटी": "waati", "प्लेट": "plate", "थाली": "plate",
                "दोना": "dona", "चम्मच": "chammach", "चमचा": "chammach",
                "कटिंग": "cutting", "ग्लास": "glass", "कप": "cup",
                "पीस": "piece", "नग": "piece", "रोटी": "piece", "पराठा": "piece"
            }
            for dev_u, std_u in dev_unit_map.items():
                if re.search(b_start + re.escape(dev_u) + b_end, prefix_text):
                    unit = std_u
                    found_unit = True
                    break

        if not found_unit:
            unit = default_unit

        return qty, unit

    def get_unit_grams(self, unit: str, context: str, item_serving_grams: float) -> float:
        """Computes gram weight per unit based on standard vs mess sizing."""
        unit_info = self.units.get(unit, {})
        if unit in ["piece", "count"]:
            return float(item_serving_grams)

        if context == "mess":
            return float(unit_info.get("mess_grams", unit_info.get("standard_grams", item_serving_grams)))
        return float(unit_info.get("standard_grams", item_serving_grams))

    def parse_transcript(self, text: str) -> MetabolicReport:
        """
        Parses spoken Hinglish/Marathi meal descriptions, applies preparation context,
        aggregates macros, and performs full ICMR-NIN reality checks.
        """
        context_name, context_mults, context_desc = self.detect_preparation_context(text)
        fat_mult = float(context_mults.get("oil_fat_multiplier", 1.0))
        carb_mult = float(context_mults.get("carb_multiplier", 1.0))
        prot_mult = float(context_mults.get("protein_multiplier", 1.0))

        lower_text = text.lower()
        raw_matches = []

        # Boundary-safe lookup for both ASCII words and Devanagari Unicode
        b_start = r'(?<![a-zA-Z0-9\u0900-\u097F])'
        b_end = r'(?![a-zA-Z0-9\u0900-\u097F])'

        # Find all candidate alias matches using lookaround boundary
        sorted_aliases = sorted(self.alias_to_item.keys(), key=len, reverse=True)
        for alias in sorted_aliases:
            pattern = b_start + re.escape(alias) + b_end
            for m in re.finditer(pattern, lower_text):
                start, end = m.span()
                raw_matches.append((start, end, alias, self.alias_to_item[alias]))

        # Filter overlapping matches, giving priority to longer strings
        raw_matches.sort(key=lambda x: (x[1] - x[0]), reverse=True)
        chosen_matches = []
        for match in raw_matches:
            start, end, alias, food_dict = match
            if not any(s < end and end <= e or start >= s and start < e for s, e, _, _ in chosen_matches):
                chosen_matches.append(match)

        # Sort matches by appearance in text
        chosen_matches.sort(key=lambda x: x[0])

        matched_items: List[MatchedFoodItem] = []
        prev_end = 0

        for start, end, alias, food_dict in chosen_matches:
            # Segment strictly between previous food item and current food item
            prefix_segment = lower_text[prev_end:start]
            prev_end = end

            # Conjunctions in English, Hinglish, Marathi, and Devanagari
            conj_pattern = r"(?:\b(aur|ani|and|with|saath|sobat|then|end|mein|madhe|,)\b|(?:और|आणि|व|तसेच|देन|एंड|में|मध्ये|खाई|खाया|घेतली|घेतला|पिली|पिया|,|।))"
            conjunction_matches = list(re.finditer(conj_pattern, prefix_segment, re.IGNORECASE))
            if conjunction_matches:
                last_conj_end = conjunction_matches[-1].end()
                prefix_segment = prefix_segment[last_conj_end:]

            default_u = food_dict.get("standard_serving_unit", "plate")
            qty, detected_unit = self.parse_quantity_and_unit(prefix_segment, default_unit=default_u)

            # Determine gram weight
            base_serving_g = float(food_dict.get("serving_grams", 150))
            unit_g = self.get_unit_grams(detected_unit, context_name, base_serving_g)

            # Proportion ratio relative to standard serving
            portion_ratio = (unit_g / base_serving_g) * qty

            # Extract base nutrients
            base_cal = float(food_dict.get("calories", 0.0))
            base_prot = float(food_dict.get("protein_g", 0.0))
            base_carb = float(food_dict.get("carbs_g", 0.0))
            base_fat = float(food_dict.get("fat_g", 0.0))
            base_fib = float(food_dict.get("fiber_g", 0.0))

            # Apply portion and context multipliers
            scaled_prot = round(base_prot * portion_ratio * prot_mult, 1)
            scaled_carb = round(base_carb * portion_ratio * carb_mult, 1)
            scaled_fat = round(base_fat * portion_ratio * fat_mult, 1)
            scaled_fib = round(base_fib * portion_ratio, 1)

            # Re-calculate calories based on Atwater physiological fuel values (4-4-9)
            scaled_cal = round((scaled_carb * 4.0) + (scaled_prot * 4.0) + (scaled_fat * 9.0), 1)

            matched_item = MatchedFoodItem(
                id=food_dict["id"],
                name_en=food_dict["name_en"],
                name_hi=food_dict.get("name_hi", food_dict["name_en"]),
                name_mr=food_dict.get("name_mr", food_dict["name_en"]),
                category=food_dict.get("category", "general"),
                quantity=qty,
                unit=detected_unit,
                unit_grams=unit_g,
                total_grams=round(unit_g * qty, 1),
                base_calories=base_cal,
                base_protein_g=base_prot,
                base_carbs_g=base_carb,
                base_fat_g=base_fat,
                base_fiber_g=base_fib,
                glycemic_index=food_dict.get("glycemic_index", "Medium"),
                glycemic_spike_risk=food_dict.get("glycemic_spike_risk", "Moderate"),
                sugar_content_g=float(food_dict.get("sugar_content_g", 0.0)) * portion_ratio,
                is_fried=bool(food_dict.get("is_fried", False)),
                is_refined_carb=bool(food_dict.get("is_refined_carb", False)),
                icmr_source=food_dict.get("icmr_source", "IFCT-2017"),
                metabolic_notes=food_dict.get("metabolic_notes", ""),
                scaled_calories=scaled_cal,
                scaled_protein_g=scaled_prot,
                scaled_carbs_g=scaled_carb,
                scaled_fat_g=scaled_fat,
                scaled_fiber_g=scaled_fib,
            )
            matched_items.append(matched_item)

        # Aggregate totals
        tot_cal = round(sum(i.scaled_calories for i in matched_items), 1)
        tot_prot = round(sum(i.scaled_protein_g for i in matched_items), 1)
        tot_carb = round(sum(i.scaled_carbs_g for i in matched_items), 1)
        tot_fat = round(sum(i.scaled_fat_g for i in matched_items), 1)
        tot_fib = round(sum(i.scaled_fiber_g for i in matched_items), 1)

        # Perform ICMR Reality Check
        reality_check = self._evaluate_icmr_reality(
            matched_items, tot_prot, tot_carb, tot_fat, tot_fib, context_name
        )

        # Generate Persona Spoken Dialogue for Timbre v3.0
        spoken_devansh = self._generate_devansh_script(
            matched_items, tot_cal, tot_prot, tot_carb, reality_check, context_name
        )
        spoken_shivani = self._generate_shivani_script(
            matched_items, tot_cal, tot_prot, tot_carb, reality_check, context_name
        )

        return MetabolicReport(
            input_text=text,
            detected_context=context_name,
            context_description=context_desc,
            context_multipliers={
                "oil_fat": fat_mult,
                "carbs": carb_mult,
                "protein": prot_mult,
            },
            items=matched_items,
            total_calories=tot_cal,
            total_protein_g=tot_prot,
            total_carbs_g=tot_carb,
            total_fat_g=tot_fat,
            total_fiber_g=tot_fib,
            reality_check=reality_check,
            spoken_summary_devansh=spoken_devansh,
            spoken_summary_shivani=spoken_shivani,
        )

    def _evaluate_icmr_reality(
        self,
        items: List[MatchedFoodItem],
        total_prot: float,
        total_carb: float,
        total_fat: float,
        total_fib: float,
        context: str,
    ) -> ICMRRealityCheck:
        """Evaluates ratios, hidden sugars, acidity risks, and suggests budget swaps."""
        if total_prot > 0:
            p_to_c = round(total_prot / total_carb, 2) if total_carb > 0 else 1.0
            c_to_p = round(total_carb / total_prot, 2)
        else:
            p_to_c = 0.0
            c_to_p = round(total_carb, 1)

        # ICMR guidelines: Carb-to-Protein should be <= 2.5:1 (or P:C >= 0.40)
        if c_to_p > 5.0 or p_to_c < 0.20:
            ratio_status = f"Extreme Carb-Heavy Imbalance ({c_to_p}:1 Carb:Protein vs ICMR <= 2.5:1 benchmark)"
        elif c_to_p > 3.0:
            ratio_status = f"Moderate Carb Dominance ({c_to_p}:1 Carb:Protein)"
        else:
            ratio_status = f"Balanced Macronutrient Ratio ({c_to_p}:1 Carb:Protein)"

        # Glycemic Spike Risk Assessment
        has_refined_carbs = any(i.is_refined_carb for i in items)
        total_sugar = sum(i.sugar_content_g for i in items)
        any_severe_item = any(i.glycemic_spike_risk == "Severe" for i in items)

        if any_severe_item or has_refined_carbs or total_sugar > 15.0 or c_to_p > 6.0:
            spike_risk = "Severe"
        elif any(i.glycemic_spike_risk == "Moderate" for i in items) or c_to_p > 3.5:
            spike_risk = "Moderate"
        else:
            spike_risk = "Low"

        # Hidden Sugar Flags
        hidden_sugar_flags = []
        for i in items:
            if i.id in ["cutting_chai", "sweet_lassi"] or i.sugar_content_g >= 7.0:
                hidden_sugar_flags.append(
                    f"[!] {i.name_en}: ~{int(i.sugar_content_g)}g hidden refined sugar detected! (1 cup chai ~ 2-2.5 tsp sugar)."
                )
        if total_sugar > 15.0:
            hidden_sugar_flags.append(
                f"[ALERT] Total Meal Sugar: {int(total_sugar)}g exceeds WHO recommended single-meal discretionary sugar limits."
            )

        # Acidity & Fried Warnings
        acidity_flags = []
        fried_items = [i for i in items if i.is_fried]
        if fried_items:
            names = ", ".join([f"{i.name_en}" for i in fried_items])
            if context == "canteen_thela":
                acidity_flags.append(
                    f"[ACIDITY] Reheated Canteen Oil Alert ({names}): Canteen and roadside deep-frying repeatedly reheats oil, generating oxidized free radicals, trans fats, and triggering severe gastric acid reflux."
                )
            else:
                acidity_flags.append(
                    f"[WARNING] Deep-Fried Item ({names}): High lipid saturation delays gastric clearance, triggering heartburn and digestive heaviness."
                )

        if any(i.id == "cutting_chai" for i in items) and fried_items:
            acidity_flags.append(
                "[COMBO] Thela Chai + Fried Snack Combo: Combining tannic hot sweet tea with deep-fried snacks is the #1 trigger for chronic student hyperacidity and bloating."
            )

        # Generate Budget Protein & Healthy Swaps
        budget_swaps = []
        if c_to_p > 3.5:
            budget_swaps.append("Sattu Drink Swap: Add 1 glass Namkeen Chana Sattu (+13g cheap plant protein, low GI, costs Rs 15).")
            budget_swaps.append("Double Egg Swap: Add 2 boiled eggs or egg bhurji (+13-14g complete bioavailable protein, 0 carb spike).")
            budget_swaps.append("Roasted Chana Swap: Snack on 1 dona Bhuna Chana with skin (+10g protein, 8.5g fiber, costs Rs 10).")

        if any(i.id == "cutting_chai" for i in items):
            budget_swaps.append("Probiotic Taak Swap: Replace sugary cutting chai with 1 glass Masala Taak / Chaas (soothes acidity, zero added sugar).")

        if any(i.is_refined_carb for i in items):
            budget_swaps.append("Fiber Sequencing: Eat 1 plate Kachumber Salad (cucumber, tomato, onion) 10 minutes before carbs to cut insulin spike by 35%.")

        return ICMRRealityCheck(
            protein_to_carb_ratio=p_to_c,
            carb_to_protein_ratio=c_to_p,
            ratio_status=ratio_status,
            glycemic_spike_risk=spike_risk,
            hidden_sugar_flags=hidden_sugar_flags,
            acidity_flags=acidity_flags,
            budget_protein_swaps=budget_swaps,
        )

    def _generate_devansh_script(
        self,
        items: List[MatchedFoodItem],
        total_cal: float,
        total_prot: float,
        total_carb: float,
        reality: ICMRRealityCheck,
        context: str,
    ) -> str:
        """Generates dynamic Devansh (Youth/Hostel Dost) coach script with inline expressive tags."""
        if not items or len(items) == 0:
            return "Dost, koi food item samajh nahi aaya. Kripya thoda clearly batayein jaise '2 samosa aur ek cutting chai'."

        # High-carb low-protein snack special handling (e.g. Chai + Cookies + Chakli)
        is_snack_profile = all(i.category in ["snack", "sweet", "beverage", "fast_food"] for i in items)
        if is_snack_profile and total_prot <= 6.0 and total_cal >= 200:
            return (
                f"Arre dost! Sham ke naste mein chai, cookies aur chakli se lagbhag {int(total_cal)} calorie load ho gayi. "
                f"<sigh> Refined maida aur deep-fried trans fat toh aa gaya par protein bilkul zero hai! </sigh> "
                f"Agli baar chakli ki jagah thoda roasted chana ya sattu drink try kar."
            )

        item_summary = " aur ".join([f"{int(i.quantity)} {i.unit} {i.name_mr or i.name_en}" for i in items[:3]])

        if reality.glycemic_spike_risk == "Severe":
            script = (
                f"Arre bhai! <excited> {item_summary} daba li? </excited> "
                f"<laugh> Taste toh kadak tha, </laugh> lekin metabolic reality check sun: "
                f"Canteen mein lagbhag {int(total_cal)} calorie aur {int(total_carb)} gram carbs load ho gaye, "
                f"aur protein mila sirf {int(total_prot)} gram! "
                f"Carb to protein ratio {reality.carb_to_protein_ratio} chal रहा है भाई। "
                f"Agli baar 10 rupaye ka bhuna chana ya sattu drink add kar, glucose crash nahi hoga!"
            )
        else:
            script = (
                f"Sahi ja raha hai dost! <excited> {item_summary} </excited> "
                f"mein total {int(total_cal)} calorie aur {int(total_prot)} gram protein mila hai. "
                f"Macronutrient balance kaafi control mein hai. Keep it up!"
            )
        return script

    def _generate_shivani_script(
        self,
        items: List[MatchedFoodItem],
        total_cal: float,
        total_prot: float,
        total_carb: float,
        reality: ICMRRealityCheck,
        context: str,
    ) -> str:
        """Generates dynamic Shivani (Family/Elder Care) coach script with warm, respectful pacing."""
        if not items or len(items) == 0:
            return "Kshama karein, mujhe bhojan ka vivaran samajh nahi aaya. Kripya thoda spashth roop se kahein, jaise 'do roti aur dal'."

        item_summary = " aur ".join([f"{int(i.quantity)} {i.unit} {i.name_hi}" for i in items[:3]])

        is_snack_profile = all(i.category in ["snack", "sweet", "beverage", "fast_food"] for i in items)
        if is_snack_profile and total_prot <= 6.0 and total_cal >= 200:
            return (
                f"Namaste. Sham ke naste mein aahar se lagbhag {int(total_cal)} calories aur tel ki matra badh gayi hai, "
                f"parantu protein ki kami hai. Pachan aur rakt sharkara ko santulit rakhne ke liye, "
                f"tali hui cheezon ke sthan par thoda bhuna chana ya taak lena adhik hitkari hoga."
            )

        if reality.hidden_sugar_flags or reality.glycemic_spike_risk in ["Severe", "Moderate"]:
            script = (
                f"Namaste. Aapne {item_summary} ka sevan kiya hai. "
                f"Is aahar mein kul {int(total_cal)} calories aur {int(total_carb)} gram carbohydrates hain. "
                f"Rakt sharkara aur pachan santulan ke liye, chai mein cheeni ki matra kam karein, "
                f"aur bhojan se pehle thoda kheera ya dahi zaroor shamil karein."
            )
        else:
            script = (
                f"Namaste. Aapka bhojan kaafi santulit hai. "
                f"Kul {int(total_cal)} calories aur {int(total_prot)} gram shuddh protein prapt hua hai. "
                f"Yah poshan aapke pachan tantra ke liye uttam hai."
            )
        return script

    def audit_meal(self, input_val: Any) -> MetabolicReport:
        """Convenience method accepting text string or existing items list."""
        if isinstance(input_val, str):
            return self.parse_transcript(input_val)
        elif isinstance(input_val, MetabolicReport):
            return input_val
        elif isinstance(input_val, list):
            tot_cal = round(sum(getattr(i, 'scaled_calories', getattr(i, 'calories_kcal', 0.0)) for i in input_val), 1)
            tot_prot = round(sum(getattr(i, 'scaled_protein_g', getattr(i, 'protein_g', 0.0)) for i in input_val), 1)
            tot_carb = round(sum(getattr(i, 'scaled_carbs_g', getattr(i, 'carbs_g', 0.0)) for i in input_val), 1)
            tot_fat = round(sum(getattr(i, 'scaled_fat_g', getattr(i, 'fat_g', 0.0)) for i in input_val), 1)
            tot_fib = round(sum(getattr(i, 'scaled_fiber_g', getattr(i, 'fiber_g', 0.0)) for i in input_val), 1)
            rc = self._evaluate_icmr_reality(input_val, tot_prot, tot_carb, tot_fat, tot_fib, "home")
            return MetabolicReport(
                input_text="",
                detected_context="home",
                context_description="Direct Item Audit",
                context_multipliers={"oil_fat": 1.0, "carbs": 1.0, "protein": 1.0},
                items=input_val,
                total_calories=tot_cal,
                total_protein_g=tot_prot,
                total_carbs_g=tot_carb,
                total_fat_g=tot_fat,
                total_fiber_g=tot_fib,
                reality_check=rc,
                spoken_summary_devansh=self._generate_devansh_script(input_val, tot_cal, tot_prot, tot_carb, rc, "home"),
                spoken_summary_shivani=self._generate_shivani_script(input_val, tot_cal, tot_prot, tot_carb, rc, "home"),
            )
        return self.parse_transcript("")



# Aliases for backwards compatibility with earlier milestones
FoodItemMatch = MatchedFoodItem
MetabolicAuditResult = MetabolicReport
