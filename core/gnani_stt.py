"""
Gnani AI Prisma v3.0 Speech-to-Text (STT) Connector
Handles sovereign Indic speech recognition with contextual keyterm boosting
for Indian food items, street units, and culinary vernacular.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("AaharVaani.STT")


class GnaniSTTClient:
    """
    Prisma v3.0 STT API Client.
    Connects to Gnani AI's sovereign Indic speech models to transcribe
    spoken Hindi, Hinglish, and regional Indian languages into text,
    incorporating domain-specific culinary keyterms for high recognition accuracy.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        lexicon_path: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("GNANI_API_KEY", "")
        self.endpoint = endpoint or os.getenv(
            "STT_ENDPOINT", "https://api.vachana.ai/stt/v3"
        )
        self.lexicon_path = lexicon_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "food_lexicon.json"
        )
        self._keyterms_cache: Optional[List[str]] = None

    def is_configured(self) -> bool:
        """Check if a valid Gnani AI API key is configured."""
        return bool(self.api_key and not self.api_key.startswith("your_gnani"))

    def get_custom_keyterms(self) -> List[str]:
        """
        Extract custom Indic food vocabulary and portion units from the lexicon
        to bias Prisma v3.0's acoustic and language models.
        """
        if self._keyterms_cache is not None:
            return self._keyterms_cache

        keyterms = set()
        # Common Indian portion and number units
        units_and_numbers = [
            "katori", "cutori", "bowl", "chammach", "spoon", "plate", "full plate", "half plate",
            "thali", "glass", "tukda", "piece", "cup", "ek", "do", "teen", "chaar", "paanch",
            "chhah", "saat", "aath", "nau", "dus", "aadha", "paanv", "sawa", "dhedh", "dhai",
            "nashta", "khana", "lunch", "dinner", "breakfast", "subah", "dopahar", "shaam", "raat"
        ]
        for term in units_and_numbers:
            keyterms.add(term.lower())

        # Extract names and aliases from food_lexicon.json
        if os.path.exists(self.lexicon_path):
            try:
                with open(self.lexicon_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    items = data.get("items", [])
                    for item in items:
                        keyterms.add(item.get("name_en", "").lower())
                        for alias in item.get("aliases", []):
                            keyterms.add(alias.lower())
            except Exception as e:
                logger.warning(f"Could not load food lexicon for keyterms: {e}")

        self._keyterms_cache = sorted(list(keyterms))
        return self._keyterms_cache

    def transcribe_audio(
        self,
        audio_bytes: bytes,
        lang_code: str = "hi-IN",
        custom_keyterms: Optional[List[str]] = None,
        audio_format: str = "wav",
    ) -> Dict[str, Any]:
        """
        Transcribe raw audio bytes using Gnani AI Prisma v3.0 STT API.
        
        Args:
            audio_bytes: Raw audio data in WAV/PCM format
            lang_code: Indic language code (e.g., 'hi-IN', 'en-IN', 'ta-IN')
            custom_keyterms: Optional override list of domain keywords
            audio_format: Audio format encoding (default: 'wav')

        Returns:
            Dict containing 'transcript', 'confidence', 'language', and 'status'.
        """
        if not audio_bytes:
            return {
                "status": "error",
                "message": "Empty audio data received.",
                "transcript": "",
                "confidence": 0.0,
            }

        keyterms = custom_keyterms or self.get_custom_keyterms()

        # If API key is not configured or in mock/dev mode
        if not self.is_configured():
            logger.info("Gnani API key not configured. Using developer simulation mode.")
            return {
                "status": "simulated",
                "transcript": "2 katori dal tadka aur 2 plain roti khaya",
                "confidence": 0.94,
                "language": lang_code,
                "keyterms_boosted": len(keyterms),
                "notice": "Mock transcript generated because GNANI_API_KEY is not configured.",
            }

        headers = {
            "token": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
        }

        files = {
            "audio": ("input_audio." + audio_format, audio_bytes, f"audio/{audio_format}"),
        }
        data = {
            "lang": lang_code,
            "keyterms": json.dumps(keyterms[:100]),  # Top boosted terms
            "encoding": audio_format.upper(),
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                files=files,
                data=data,
                timeout=15,
            )
            if response.status_code == 200:
                resp_json = response.json()
                transcript = (
                    resp_json.get("transcript")
                    or resp_json.get("text")
                    or resp_json.get("result", "")
                )
                confidence = float(resp_json.get("confidence", 0.90))
                return {
                    "status": "success",
                    "transcript": transcript,
                    "confidence": confidence,
                    "language": lang_code,
                    "raw_response": resp_json,
                }
            else:
                logger.error(f"Prisma v3.0 error {response.status_code}: {response.text}")
                return {
                    "status": "api_error",
                    "status_code": response.status_code,
                    "message": response.text,
                    "transcript": "",
                    "confidence": 0.0,
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request to Prisma v3.0 failed: {e}")
            return {
                "status": "connection_error",
                "message": str(e),
                "transcript": "",
                "confidence": 0.0,
            }

    def transcribe_file(
        self,
        file_path: str,
        lang_code: str = "hi-IN",
    ) -> Dict[str, Any]:
        """Convenience method to transcribe an audio file on disk."""
        if not os.path.exists(file_path):
            return {
                "status": "error",
                "message": f"Audio file not found: {file_path}",
                "transcript": "",
            }

        with open(file_path, "rb") as f:
            audio_bytes = f.read()

        fmt = file_path.split(".")[-1].lower()
        return self.transcribe_audio(audio_bytes, lang_code=lang_code, audio_format=fmt)
