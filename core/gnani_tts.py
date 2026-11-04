"""
Gnani AI Timbre v3.0 Text-to-Speech (TTS) Connector
Synthesizes natural, sovereign Indic speech responses with expressive tags
for metabolic coaching and dietary guidance in Indian languages.
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


class GnaniTTSClient:
    """
    Timbre v3.0 TTS API Client.
    Connects to Gnani AI's sovereign Indic speech models to convert textual
    nutritional feedback into natural-sounding Indic audio with expressive inflection.
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

    def format_expressive_text(self, text: str, emotion: str = "empathetic_coach") -> str:
        """
        Apply Timbre v3.0 expressive formatting tags or SSML markers
        to adapt vocal prosody according to health coaching nuances.
        """
        clean_text = text.strip()
        if emotion == "encouraging":
            # Upbeat tempo, warm pitch
            return f'<speak><prosody rate="1.05" pitch="+2Hz">{clean_text}</prosody></speak>'
        elif emotion == "cautionary":
            # Measured pace, calm authority for glycemic alerts
            return f'<speak><prosody rate="0.95" pitch="-1Hz">{clean_text}</prosody></speak>'
        else:  # empathetic_coach
            return f'<speak><prosody rate="1.0" pitch="0Hz">{clean_text}</prosody></speak>'

    def _generate_synthetic_tone_wav(self, duration_sec: float = 1.5) -> bytes:
        """
        Generate a gentle harmonic audio cue in WAV format for local dev simulation
        when live API credentials are not yet supplied.
        """
        try:
            import numpy as np
            from scipy.io import wavfile

            sample_rate = 16000
            t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), False)
            # Soft two-tone warm chime (440Hz A4 -> 554Hz C#5)
            signal = 0.25 * np.sin(2 * np.pi * 440 * t) + 0.15 * np.sin(2 * np.pi * 554 * t)
            # Exponential decay envelope
            envelope = np.exp(-2.5 * t)
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
        lang_code: str = "hi-IN",
        voice_gender: str = "female",
        emotion: str = "empathetic_coach",
    ) -> Dict[str, Any]:
        """
        Synthesize speech from nutritional advice text using Timbre v3.0.

        Args:
            text: Nutritional recommendation or companion dialogue text
            lang_code: Language code (e.g. 'hi-IN', 'en-IN')
            voice_gender: 'female' or 'male'
            emotion: Expressive vocal styling ('empathetic_coach', 'encouraging', 'cautionary')

        Returns:
            Dict with 'status', 'audio_bytes', 'temp_path', and 'metadata'.
        """
        if not text:
            return {"status": "error", "message": "Empty text provided.", "audio_bytes": None}

        tagged_text = self.format_expressive_text(text, emotion=emotion)

        if not self.is_configured():
            logger.info("Gnani API key not configured. Generating developer preview audio.")
            audio_bytes = self._generate_synthetic_tone_wav()
            temp_filename = f"tts_dev_{int(time.time())}.wav"
            temp_path = os.path.join(self.temp_dir, temp_filename)
            try:
                with open(temp_path, "wb") as f:
                    f.write(audio_bytes)
            except Exception:
                temp_path = ""

            return {
                "status": "simulated",
                "audio_bytes": audio_bytes,
                "temp_path": temp_path,
                "language": lang_code,
                "voice_gender": voice_gender,
                "notice": "Simulated chime audio returned because GNANI_API_KEY is not configured.",
            }

        headers = {
            "token": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "text": tagged_text,
            "lang": lang_code,
            "voice": voice_gender.lower(),
            "audio_format": "wav",
            "sample_rate": 16000,
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=20,
            )
            if response.status_code == 200:
                audio_bytes = response.content
                temp_filename = f"tts_{int(time.time())}.wav"
                temp_path = os.path.join(self.temp_dir, temp_filename)
                with open(temp_path, "wb") as f:
                    f.write(audio_bytes)

                return {
                    "status": "success",
                    "audio_bytes": audio_bytes,
                    "temp_path": temp_path,
                    "language": lang_code,
                    "voice_gender": voice_gender,
                }
            else:
                logger.error(f"Timbre v3.0 error {response.status_code}: {response.text}")
                return {
                    "status": "api_error",
                    "status_code": response.status_code,
                    "message": response.text,
                    "audio_bytes": None,
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request to Timbre v3.0 failed: {e}")
            return {
                "status": "connection_error",
                "message": str(e),
                "audio_bytes": None,
            }
