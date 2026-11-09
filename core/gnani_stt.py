"""
Gnani AI Prisma v3.0 Speech-to-Text (STT) Connector
Connects to sovereign Indic speech models to transcribe spoken Hindi, Hinglish,
and Marathi audio, utilizing dynamic domain keyterms from the food lexicon.
"""

import os
import io
import json
import logging
from typing import List, Dict, Any, Optional, Union
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("AaharVaani.STT")


class GnaniSTTClient:
    """
    Prisma v3.0 STT API Client.
    Connects to Gnani AI's sovereign Indic speech models at STT_ENDPOINT
    using the 'X-API-Key-ID' authentication header.
    """

    DEFAULT_TOPIC = (
        "Daily Indian meal logging, hostel mess food, street food, "
        "canteen diet, regional nutrition, and colloquial portion units"
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        lexicon_path: Optional[str] = None,
        topic: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("GNANI_API_KEY", "")
        self.endpoint = endpoint or os.getenv(
            "STT_ENDPOINT", "https://api.vachana.ai/stt/v3"
        )
        self.lexicon_path = lexicon_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "food_lexicon.json"
        )
        self.topic = topic or self.DEFAULT_TOPIC
        self._keyterms_cache: Optional[List[str]] = None

    def is_configured(self) -> bool:
        """Check if a valid Gnani AI API key is configured."""
        return bool(self.api_key and not self.api_key.startswith("your_gnani"))

    def get_custom_keyterms(self) -> List[str]:
        """
        Dynamically load all food names, regional aliases, and colloquial units
        from data/food_lexicon.json to construct Prisma v3.0 keyterm hints.
        """
        if self._keyterms_cache is not None:
            return self._keyterms_cache

        keyterms = set()

        # Core colloquial units & number words in Hindi, Marathi, Hinglish
        colloquial_vocabulary = [
            "katori", "waati", "plate", "half-plate", "cutting", "kulhad", "dona",
            "chammach", "spoon", "piece", "count", "glass", "cup", "bowl",
            "ek", "do", "teen", "chaar", "paanch", "chhah", "saat", "aath", "nau", "dus",
            "don", "char", "paach", "saha", "daha", "aadha", "ardha", "paanv", "paav",
            "dhedh", "dhai", "deed", "adhich", "sawa", "canteen", "mess", "thela", "tapri",
            "dhabba", "hostel", "ghar", "nashta", "khana", "lunch", "dinner", "breakfast"
        ]
        for word in colloquial_vocabulary:
            keyterms.add(word.lower())

        # Load entries from food_lexicon.json
        if os.path.exists(self.lexicon_path):
            try:
                with open(self.lexicon_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Add unit names
                units_dict = data.get("units", {})
                for u in units_dict.keys():
                    keyterms.add(u.lower())

                # Add item names, Marathi names, and all aliases
                items_list = data.get("items", [])
                for item in items_list:
                    if item.get("name_en"):
                        keyterms.add(item["name_en"].lower())
                    if item.get("name_hi"):
                        keyterms.add(item["name_hi"].strip().lower())
                    if item.get("name_mr"):
                        keyterms.add(item["name_mr"].strip().lower())
                    for alias in item.get("aliases", []):
                        keyterms.add(alias.strip().lower())
            except Exception as e:
                logger.warning(f"Could not load food lexicon for keyterms: {e}")

        self._keyterms_cache = sorted(list(keyterms))
        return self._keyterms_cache

    def transcribe_audio(
        self,
        audio_source: Union[str, bytes, io.IOBase],
        language_code: str = "hi-IN",
        output_style: str = "transcribe",
    ) -> Dict[str, Any]:
        """
        Transcribe raw audio bytes or an audio file using Gnani Prisma v3.0 STT.

        Args:
            audio_source: File path (str), raw audio bytes, or file-like object.
            language_code: Target Indic language code (e.g. 'hi-IN', 'mr-IN', 'en-IN').
            output_style: Output format instruction (default: 'transcribe').

        Returns:
            Structured dict: {"status": "success", "transcript": text, "raw": response_json}
            or structured error dict with graceful handling.
        """
        # Resolve audio bytes
        audio_bytes: bytes = b""
        filename = "input_audio.wav"

        if isinstance(audio_source, (str, os.PathLike)):
            if not os.path.exists(audio_source):
                return {
                    "status": "error",
                    "error_type": "file_not_found",
                    "message": f"Audio file not found at: {audio_source}",
                    "transcript": "",
                    "raw": {},
                }
            filename = os.path.basename(audio_source)
            with open(audio_source, "rb") as f:
                audio_bytes = f.read()
        elif isinstance(audio_source, (bytes, bytearray)):
            audio_bytes = bytes(audio_source)
        elif hasattr(audio_source, "read"):
            audio_bytes = audio_source.read()
        else:
            return {
                "status": "error",
                "error_type": "invalid_input",
                "message": f"Unsupported audio_source type: {type(audio_source)}",
                "transcript": "",
                "raw": {},
            }

        if not audio_bytes:
            return {
                "status": "error",
                "error_type": "empty_audio",
                "message": "Received empty audio payload.",
                "transcript": "",
                "raw": {},
            }

        keyterms = self.get_custom_keyterms()

        # If live credentials are not set, return simulated response for local development
        if not self.is_configured():
            logger.info("GNANI_API_KEY not configured. Returning developer preview transcription.")
            mock_transcript = "Subah do plate poha aur ek cutting chai li canteen mein"
            return {
                "status": "success",
                "transcript": mock_transcript,
                "raw": {
                    "simulation": True,
                    "notice": "Mock transcript generated because GNANI_API_KEY is not configured.",
                    "topic": self.topic,
                    "language": language_code,
                    "keyterms_count": len(keyterms),
                    "confidence": 0.95,
                    "text": mock_transcript,
                },
            }

        # Prepare HTTP request to Prisma v3.0
        headers = {
            "X-API-Key-ID": self.api_key,
        }

        files = {
            "audio_file": (filename, audio_bytes, "audio/wav"),
        }

        data = {
            "topic": self.topic,
            "keyterms": json.dumps(keyterms[:150]),
            "language_code": language_code,
            "lang": language_code,
            "output_style": output_style,
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                files=files,
                data=data,
                timeout=25,
            )

            # Handle 401 Unauthorized
            if response.status_code == 401:
                logger.error("Gnani Prisma v3.0 401 Unauthorized: Invalid X-API-Key-ID.")
                return {
                    "status": "error",
                    "error_type": "unauthorized",
                    "status_code": 401,
                    "message": "401 Unauthorized: Invalid or missing GNANI_API_KEY in X-API-Key-ID header.",
                    "transcript": "",
                    "raw": response.text,
                }

            # Handle 400 Bad Request
            if response.status_code == 400:
                logger.error(f"Gnani Prisma v3.0 400 Bad Request: {response.text}")
                return {
                    "status": "error",
                    "error_type": "bad_request",
                    "status_code": 400,
                    "message": f"400 Bad Request: {response.text}",
                    "transcript": "",
                    "raw": response.text,
                }

            # Handle Success
            if response.status_code == 200:
                try:
                    resp_json = response.json()
                except Exception:
                    resp_json = {"text": response.text}

                transcript_text = (
                    resp_json.get("transcript")
                    or resp_json.get("text")
                    or resp_json.get("result")
                    or resp_json.get("asr_output", "")
                )

                if isinstance(transcript_text, dict):
                    transcript_text = transcript_text.get("text", "")

                return {
                    "status": "success",
                    "transcript": str(transcript_text).strip(),
                    "raw": resp_json,
                }

            # Other HTTP errors
            logger.error(f"Prisma v3.0 returned unexpected status {response.status_code}: {response.text}")
            return {
                "status": "error",
                "error_type": f"http_{response.status_code}",
                "status_code": response.status_code,
                "message": f"API request failed with status code {response.status_code}: {response.text}",
                "transcript": "",
                "raw": response.text,
            }

        except requests.exceptions.Timeout:
            logger.error("Gnani Prisma v3.0 request timed out after 25 seconds.")
            return {
                "status": "error",
                "error_type": "timeout",
                "message": "Gnani Prisma v3.0 request timed out. Please verify network connectivity.",
                "transcript": "",
                "raw": {},
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error connecting to Prisma v3.0: {e}")
            return {
                "status": "error",
                "error_type": "connection_error",
                "message": f"Network error connecting to Gnani STT: {str(e)}",
                "transcript": "",
                "raw": {},
            }
