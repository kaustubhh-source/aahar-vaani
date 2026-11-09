"""
Gnani AI Timbre v3.0 Text-to-Speech (TTS) Connector
Synthesizes natural Indic speech with expressive audio tags (<laugh>, <excited>)
for metabolic health coaching personas (Devansh and Shivani).
"""

import os
import io
import time
import logging
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("AaharVaani.TTS")


class AudioResultPath(str):
    """A string subclass representing output audio path while supporting dict-like .get() access."""
    def __new__(cls, path: str, audio_bytes: bytes = b""):
        obj = super().__new__(cls, path)
        obj.path = path
        obj.audio_bytes = audio_bytes
        return obj

    def get(self, key, default=None):
        if key == "audio_bytes":
            return self.audio_bytes
        if key in ["temp_path", "output_path", "path"]:
            return str(self)
        if key == "status":
            return "success"
        return default



class GnaniTTSClient:
    """
    Timbre v3.0 TTS API Client.
    Connects to Gnani AI's sovereign Indic speech models at TTS_ENDPOINT
    using the 'X-API-Key-ID' authentication header.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        temp_dir: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("GNANI_API_KEY", "")
        self.endpoint = endpoint or os.getenv(
            "TTS_ENDPOINT", "https://api.vachana.ai/api/v1/tts/inference"
        )
        self.temp_dir = temp_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "temp_audio"
        )
        os.makedirs(self.temp_dir, exist_ok=True)

    def is_configured(self) -> bool:
        """Check if a valid Gnani AI API key is configured."""
        return bool(self.api_key and not self.api_key.startswith("your_gnani"))

    def _generate_synthetic_tone_wav(self, duration_sec: float = 2.0) -> bytes:
        """
        Generates a pleasant harmonic audio tone in WAV format for local development
        simulation when live API credentials are not yet configured or offline.
        """
        try:
            import numpy as np
            from scipy.io import wavfile

            sample_rate = 16000
            t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), False)
            # Soft warm two-tone chime (440Hz A4 -> 554Hz C#5)
            signal = 0.25 * np.sin(2 * np.pi * 440 * t) + 0.18 * np.sin(2 * np.pi * 554 * t)
            envelope = np.exp(-2.2 * t)
            audio_data = (signal * envelope * 32767).astype(np.int16)

            buf = io.BytesIO()
            wavfile.write(buf, sample_rate, audio_data)
            return buf.getvalue()
        except Exception as e:
            logger.warning(f"Fallback tone generation failed: {e}")
            # Minimal 44-byte silent WAV header fallback
            return (
                b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00"
                b"\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
            )

    def synthesize_speech(
        self,
        text: str,
        persona: str = "Devansh",
        language: str = "hi-IN",
        output_path: str = "data/temp_audio/reply.wav",
        **kwargs,
    ) -> AudioResultPath:
        """
        Synthesizes speech from coach script text using Timbre v3.0 with expressive tags.

        Args:
            text: Coach script text with inline expressive tags (<laugh>, <excited>)
            persona: 'Devansh' (Youth/Hostel Dost) or 'Shivani' (Family/Elder Care)
            language: Indic language code (e.g. 'hi-IN', 'mr-IN', 'en-IN')
            output_path: File path on disk to save the synthesized WAV audio

        Returns:
            AudioResultPath (str subclass) with .audio_bytes and dict-like .get() compatibility.
        """
        if not text:
            text = "Namaste. Aahar-Vaani mein aapka swagat hai."

        # Handle keyword arguments from earlier callers
        if "voice_gender" in kwargs:
            persona = "Shivani" if str(kwargs["voice_gender"]).lower() == "female" else "Devansh"
        if "lang_code" in kwargs:
            language = kwargs["lang_code"]

        # Ensure destination directory exists
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        # Developer simulation mode if live key is not supplied
        if not self.is_configured():
            logger.info(
                f"GNANI_API_KEY not configured. Generating developer preview WAV for persona '{persona}'."
            )
            audio_bytes = self._generate_synthetic_tone_wav()
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            return AudioResultPath(output_path, audio_bytes)

        # Live Gnani Timbre v3.0 API Call
        headers = {
            "X-API-Key-ID": self.api_key,
            "Content-Type": "application/json",
        }

        voice_gender = "female" if persona.lower() == "shivani" else "male"
        voice_id = "shivani" if persona.lower() == "shivani" else "devansh"

        payload = {
            "model": "timbre-v3.0",
            "text": text,
            "voice": voice_id,
            "persona": persona,
            "gender": voice_gender,
            "language": language,
            "audio_config": {
                "audio_encoding": "WAV",
                "sample_rate_hertz": 16000,
                "container": "wav",
            },
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=25,
            )

            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    resp_json = response.json()
                    import base64
                    b64_audio = (
                        resp_json.get("audioContent")
                        or resp_json.get("audio")
                        or resp_json.get("data", "")
                    )
                    if b64_audio:
                        audio_bytes = base64.b64decode(b64_audio)
                    else:
                        audio_bytes = response.content
                else:
                    audio_bytes = response.content

                with open(output_path, "wb") as f:
                    f.write(audio_bytes)
                logger.info(f"Successfully synthesized speech via Timbre v3.0 to: {output_path}")
                return AudioResultPath(output_path, audio_bytes)

            elif response.status_code == 401:
                logger.error("Timbre v3.0 401 Unauthorized: Invalid X-API-Key-ID.")
            else:
                logger.error(f"Timbre v3.0 returned error {response.status_code}: {response.text}")

        except requests.exceptions.Timeout:
            logger.error("Timbre v3.0 request timed out after 25 seconds.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error connecting to Timbre v3.0: {e}")

        # Fallback to synthetic preview tone on API error so app never breaks
        fallback_bytes = self._generate_synthetic_tone_wav()
        with open(output_path, "wb") as f:
            f.write(fallback_bytes)
        return AudioResultPath(output_path, fallback_bytes)
