"""JARVIS Voice Interface — Whisper STT + TTS integration."""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Any

from src.config import config


# Voice system from TRADING_V2_PRODUCTION
VOICE_DRIVER_PATH = Path("F:/BUREAU/TRADING_V2_PRODUCTION/voice_system/voice_driver.py")


async def listen_voice(timeout: float = 10.0, keyboard_fallback: bool = False) -> str | None:
    """Capture voice input via Whisper STT (voice_driver.py).

    Returns transcribed text or None on timeout/error.
    If keyboard_fallback=True, falls back to keyboard input when voice fails.
    """
    if VOICE_DRIVER_PATH.exists():
        try:
            result = await asyncio.to_thread(
                lambda: subprocess.run(
                    [sys.executable, str(VOICE_DRIVER_PATH), "--listen", "--timeout", str(timeout)],
                    capture_output=True, text=True, timeout=timeout + 5,
                    cwd=str(VOICE_DRIVER_PATH.parent),
                )
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, Exception):
            pass

    if keyboard_fallback:
        try:
            text = await asyncio.to_thread(input, "[JARVIS] > ")
            if text and text.strip():
                return text.strip()
        except (EOFError, KeyboardInterrupt):
            return None

    return None


async def speak_text(text: str, voice: str = "fr-FR") -> bool:
    """Synthesize speech via Windows SAPI or voice_driver TTS.

    Falls back to PowerShell SAPI if voice_driver unavailable.
    """
    # Try voice_driver first
    if VOICE_DRIVER_PATH.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(VOICE_DRIVER_PATH), "--speak", text],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(VOICE_DRIVER_PATH.parent),
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass

    # Fallback: Windows SAPI via PowerShell
    try:
        ps_script = (
            f'Add-Type -AssemblyName System.Speech; '
            f'$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
            f'$synth.SelectVoiceByHints("NotSet", 0, 0, '
            f'[System.Globalization.CultureInfo]::GetCultureInfo("{voice}")); '
            f'$synth.Speak("{text.replace(chr(34), chr(39))}")'
        )
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except Exception:
        return False


async def voice_loop(callback) -> None:
    """Continuous voice listening loop.

    callback: async function(text: str) -> str  (returns response to speak)
    """
    print("[JARVIS] Mode vocal actif. Parle pour interagir.")
    while True:
        text = await listen_voice(timeout=15.0)
        if text:
            if text.lower().strip() in ("stop", "arrete", "exit", "quitter"):
                await speak_text("Session vocale terminee.")
                break
            print(f"[VOICE] {text}")
            response = await callback(text)
            if response:
                await speak_text(response)
