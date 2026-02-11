"""JARVIS Command Executor — Executes matched voice commands on the system."""

from __future__ import annotations

import subprocess
from typing import Any

from src.commands import (
    JarvisCommand, APP_PATHS, SITE_ALIASES,
    match_command, correct_voice_text, format_commands_help,
)
from src.windows import run_powershell, open_application
from src.config import SCRIPTS


async def execute_command(cmd: JarvisCommand, params: dict[str, str]) -> str:
    """Execute a matched command and return the result text."""

    if cmd.action_type == "exit":
        return "__EXIT__"

    if cmd.action_type == "list_commands":
        return format_commands_help()

    if cmd.action_type == "app_open":
        app_name = cmd.action
        # Resolve param if needed
        if "{" in app_name and params:
            for k, v in params.items():
                app_name = app_name.replace(f"{{{k}}}", v)
        # Lookup known app path
        resolved = APP_PATHS.get(app_name.lower(), app_name)
        result = run_powershell(f"Start-Process '{resolved}'", timeout=10)
        if result["success"]:
            return f"Application {app_name} ouverte."
        else:
            return f"Impossible d'ouvrir {app_name}: {result['stderr']}"

    if cmd.action_type == "browser":
        action = cmd.action
        # Replace params
        for k, v in params.items():
            action = action.replace(f"{{{k}}}", v)

        if action.startswith("navigate:"):
            url = action[len("navigate:"):]
            # Resolve site aliases
            url = SITE_ALIASES.get(url.lower(), url)
            # Add https if no protocol
            if not url.startswith("http"):
                url = f"https://{url}"
            result = run_powershell(f"Start-Process chrome '{url}'", timeout=10)
            if result["success"]:
                return f"Navigation vers {url}."
            else:
                return f"Erreur navigation: {result['stderr']}"

        elif action.startswith("search:"):
            query = action[len("search:"):]
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            result = run_powershell(f"Start-Process chrome '{url}'", timeout=10)
            if result["success"]:
                return f"Recherche Google: {query}."
            else:
                return f"Erreur recherche: {result['stderr']}"

    if cmd.action_type == "powershell":
        action = cmd.action
        for k, v in params.items():
            action = action.replace(f"{{{k}}}", v)
        result = run_powershell(action, timeout=30)
        if result["success"]:
            output = result["stdout"][:200] if result["stdout"] else "OK"
            return f"Commande executee. {output}"
        else:
            return f"Erreur: {result['stderr'][:200]}"

    if cmd.action_type == "script":
        import sys
        script_name = cmd.action
        script_path = SCRIPTS.get(script_name)
        if not script_path or not script_path.exists():
            return f"Script introuvable: {script_name}"
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True, text=True, timeout=120,
                cwd=str(script_path.parent),
            )
            output = result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
            return f"Script {script_name} termine (exit={result.returncode}). {output}"
        except subprocess.TimeoutExpired:
            return f"Script {script_name} timeout (120s)."
        except Exception as e:
            return f"Erreur script: {e}"

    if cmd.action_type == "jarvis_tool":
        # Return the tool name — the orchestrator will call it
        action = cmd.action
        for k, v in params.items():
            action = action.replace(f"{{{k}}}", v)
        return f"__TOOL__{action}"

    return f"Type d'action inconnu: {cmd.action_type}"


async def process_voice_input(text: str) -> tuple[str, float]:
    """Process raw voice input: correct, match, execute.

    Returns: (response_text, confidence_score)
    """
    # Step 1: Correct voice errors
    corrected = correct_voice_text(text)

    # Step 2: Try to match a pre-registered command
    cmd, params, score = match_command(corrected)

    if cmd is None:
        # No match — return corrected text for JARVIS to handle via IA
        return f"__FREEFORM__{corrected}", score

    # Step 3: Check if confirmation needed
    if cmd.confirm:
        return f"__CONFIRM__{cmd.name}|{cmd.description}", score

    # Step 4: Execute the command
    result = await execute_command(cmd, params)
    return result, score


async def correct_with_ia(text: str, node_url: str = "http://192.168.1.26:1234") -> str:
    """Use a local LM Studio model to correct voice transcription errors.

    Uses M2 (fast inference) by default for speed.
    """
    import httpx
    prompt = (
        "Tu es un correcteur de texte francais specialise dans la correction "
        "de transcriptions vocales. Corrige les erreurs sans changer le sens. "
        "Reponds UNIQUEMENT avec le texte corrige, rien d'autre.\n\n"
        f"Texte a corriger: {text}"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{node_url}/v1/chat/completions",
                json={
                    "model": "nvidia/nemotron-3-nano",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 256,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        # Fallback: return original corrected text
        return correct_voice_text(text)
