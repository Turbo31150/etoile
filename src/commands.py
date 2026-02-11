"""JARVIS Command Database — Pre-registered voice commands, pipelines, fuzzy matching."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


# ═══════════════════════════════════════════════════════════════════════════
# COMMAND DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class JarvisCommand:
    """A pre-registered JARVIS voice command."""
    name: str                          # Identifiant unique
    category: str                      # Categorie (navigation, fichiers, trading, systeme, app)
    description: str                   # Description en francais
    triggers: list[str]                # Phrases vocales qui declenchent cette commande
    action_type: str                   # Type: powershell, app_open, browser, script, pipeline
    action: str                        # Commande/template a executer
    params: list[str] = field(default_factory=list)  # Parametres a remplir (phrases a trou)
    confirm: bool = False              # Demander confirmation avant execution


# ═══════════════════════════════════════════════════════════════════════════
# PRE-REGISTERED COMMANDS DATABASE
# ═══════════════════════════════════════════════════════════════════════════

COMMANDS: list[JarvisCommand] = [
    # ── NAVIGATION WEB ────────────────────────────────────────────────────
    JarvisCommand(
        name="ouvrir_chrome",
        category="navigation",
        description="Ouvrir le navigateur Google Chrome",
        triggers=[
            "ouvre chrome", "ouvrir chrome", "lance chrome", "ouvre le navigateur",
            "ouvrir le navigateur", "lance le navigateur", "ouvre google chrome",
            "demarre chrome", "ouvre internet", "ouvrir internet",
        ],
        action_type="app_open",
        action="chrome",
    ),
    JarvisCommand(
        name="ouvrir_comet",
        category="navigation",
        description="Ouvrir le navigateur Comet",
        triggers=[
            "ouvre comet", "ouvrir comet", "lance comet", "ouvre le navigateur comet",
        ],
        action_type="app_open",
        action="comet",
    ),
    JarvisCommand(
        name="aller_sur_site",
        category="navigation",
        description="Naviguer vers un site web",
        triggers=[
            "va sur {site}", "ouvre {site}", "navigue vers {site}",
            "aller sur {site}", "ouvrir {site}", "charge {site}",
            "affiche {site}", "montre {site}",
        ],
        action_type="browser",
        action="navigate:{site}",
        params=["site"],
    ),
    JarvisCommand(
        name="chercher_google",
        category="navigation",
        description="Rechercher quelque chose sur Google",
        triggers=[
            "cherche {requete}", "recherche {requete}", "google {requete}",
            "cherche sur google {requete}", "recherche sur google {requete}",
            "trouve {requete}", "chercher {requete}",
        ],
        action_type="browser",
        action="search:{requete}",
        params=["requete"],
    ),
    JarvisCommand(
        name="ouvrir_gmail",
        category="navigation",
        description="Ouvrir Gmail",
        triggers=[
            "ouvre gmail", "ouvrir gmail", "ouvre mes mails", "ouvre mes emails",
            "va sur gmail", "ouvre ma boite mail", "ouvre la messagerie",
            "check mes mails", "verifie mes mails",
        ],
        action_type="browser",
        action="navigate:https://mail.google.com",
    ),
    JarvisCommand(
        name="ouvrir_youtube",
        category="navigation",
        description="Ouvrir YouTube",
        triggers=[
            "ouvre youtube", "va sur youtube", "lance youtube",
            "ouvrir youtube", "mets youtube",
        ],
        action_type="browser",
        action="navigate:https://youtube.com",
    ),
    JarvisCommand(
        name="ouvrir_github",
        category="navigation",
        description="Ouvrir GitHub",
        triggers=[
            "ouvre github", "va sur github", "ouvrir github",
        ],
        action_type="browser",
        action="navigate:https://github.com",
    ),

    # ── FICHIERS & DOCUMENTS ──────────────────────────────────────────────
    JarvisCommand(
        name="ouvrir_documents",
        category="fichiers",
        description="Ouvrir le dossier Documents",
        triggers=[
            "ouvre mes documents", "ouvrir mes documents", "ouvre documents",
            "affiche mes documents", "va dans mes documents", "ouvre le dossier documents",
        ],
        action_type="powershell",
        action="Start-Process explorer.exe -ArgumentList ([Environment]::GetFolderPath('MyDocuments'))",
    ),
    JarvisCommand(
        name="ouvrir_bureau",
        category="fichiers",
        description="Ouvrir le dossier Bureau",
        triggers=[
            "ouvre le bureau", "ouvrir le bureau", "affiche le bureau",
            "ouvre mes fichiers bureau", "va sur le bureau",
        ],
        action_type="powershell",
        action="Start-Process explorer.exe -ArgumentList 'F:\\BUREAU'",
    ),
    JarvisCommand(
        name="ouvrir_dossier",
        category="fichiers",
        description="Ouvrir un dossier specifique",
        triggers=[
            "ouvre le dossier {dossier}", "ouvrir le dossier {dossier}",
            "va dans {dossier}", "affiche {dossier}", "explore {dossier}",
        ],
        action_type="powershell",
        action="Start-Process explorer.exe -ArgumentList '{dossier}'",
        params=["dossier"],
    ),
    JarvisCommand(
        name="ouvrir_telechargements",
        category="fichiers",
        description="Ouvrir le dossier Telechargements",
        triggers=[
            "ouvre les telechargements", "ouvre mes telechargements",
            "ouvrir telechargements", "va dans telechargements",
        ],
        action_type="powershell",
        action="Start-Process explorer.exe -ArgumentList ([Environment]::GetFolderPath('UserProfile') + '\\Downloads')",
    ),

    # ── APPLICATIONS ──────────────────────────────────────────────────────
    JarvisCommand(
        name="ouvrir_vscode",
        category="app",
        description="Ouvrir Visual Studio Code",
        triggers=[
            "ouvre vscode", "ouvrir vscode", "lance vscode", "ouvre visual studio code",
            "ouvre vs code", "lance vs code", "ouvre l'editeur",
        ],
        action_type="app_open",
        action="code",
    ),
    JarvisCommand(
        name="ouvrir_terminal",
        category="app",
        description="Ouvrir un terminal PowerShell",
        triggers=[
            "ouvre le terminal", "ouvrir le terminal", "lance powershell",
            "ouvre powershell", "lance le terminal", "ouvre la console",
        ],
        action_type="app_open",
        action="wt",
    ),
    JarvisCommand(
        name="ouvrir_lmstudio",
        category="app",
        description="Ouvrir LM Studio",
        triggers=[
            "ouvre lm studio", "lance lm studio", "demarre lm studio",
            "ouvrir lm studio", "ouvre l m studio",
        ],
        action_type="app_open",
        action="lmstudio",
    ),
    JarvisCommand(
        name="ouvrir_app",
        category="app",
        description="Ouvrir une application par son nom",
        triggers=[
            "ouvre {app}", "ouvrir {app}", "lance {app}", "demarre {app}",
        ],
        action_type="app_open",
        action="{app}",
        params=["app"],
    ),

    # ── SYSTEME WINDOWS ───────────────────────────────────────────────────
    JarvisCommand(
        name="volume_haut",
        category="systeme",
        description="Augmenter le volume",
        triggers=[
            "monte le volume", "augmente le volume", "volume plus fort",
            "plus fort", "monte le son", "augmente le son",
        ],
        action_type="powershell",
        action="(New-Object -ComObject WScript.Shell).SendKeys([char]175)",
    ),
    JarvisCommand(
        name="volume_bas",
        category="systeme",
        description="Baisser le volume",
        triggers=[
            "baisse le volume", "diminue le volume", "volume moins fort",
            "moins fort", "baisse le son", "diminue le son",
        ],
        action_type="powershell",
        action="(New-Object -ComObject WScript.Shell).SendKeys([char]174)",
    ),
    JarvisCommand(
        name="muet",
        category="systeme",
        description="Couper/activer le son",
        triggers=[
            "coupe le son", "mute", "silence", "muet",
            "active le son", "reactive le son",
        ],
        action_type="powershell",
        action="(New-Object -ComObject WScript.Shell).SendKeys([char]173)",
    ),
    JarvisCommand(
        name="verrouiller",
        category="systeme",
        description="Verrouiller le PC",
        triggers=[
            "verrouille le pc", "verrouille l'ecran", "lock",
            "verrouiller", "bloque le pc",
        ],
        action_type="powershell",
        action="rundll32.exe user32.dll,LockWorkStation",
        confirm=True,
    ),
    JarvisCommand(
        name="eteindre",
        category="systeme",
        description="Eteindre le PC",
        triggers=[
            "eteins le pc", "eteindre le pc", "arrete le pc",
            "shutdown", "eteindre l'ordinateur",
        ],
        action_type="powershell",
        action="Stop-Computer -Force",
        confirm=True,
    ),
    JarvisCommand(
        name="redemarrer",
        category="systeme",
        description="Redemarrer le PC",
        triggers=[
            "redemarre le pc", "redemarrer le pc", "reboot",
            "redemarre l'ordinateur", "restart",
        ],
        action_type="powershell",
        action="Restart-Computer -Force",
        confirm=True,
    ),
    JarvisCommand(
        name="capture_ecran",
        category="systeme",
        description="Faire une capture d'ecran",
        triggers=[
            "capture ecran", "screenshot", "prends une capture",
            "fais une capture", "capture d'ecran", "copie l'ecran",
        ],
        action_type="powershell",
        action="Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen | ForEach-Object { $bmp = New-Object System.Drawing.Bitmap($_.Bounds.Width, $_.Bounds.Height); $g = [System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($_.Bounds.Location, [System.Drawing.Point]::Empty, $_.Bounds.Size); $path = [Environment]::GetFolderPath('Desktop') + '\\capture_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.png'; $bmp.Save($path); Write-Host $path }",
    ),
    JarvisCommand(
        name="info_systeme",
        category="systeme",
        description="Afficher les infos systeme",
        triggers=[
            "info systeme", "infos systeme", "statut systeme",
            "etat du systeme", "donne moi les infos systeme",
        ],
        action_type="jarvis_tool",
        action="system_info",
    ),
    JarvisCommand(
        name="processus",
        category="systeme",
        description="Lister les processus en cours",
        triggers=[
            "liste les processus", "montre les processus",
            "quels processus tournent", "affiche les processus",
        ],
        action_type="jarvis_tool",
        action="list_processes",
    ),

    # ── TRADING ───────────────────────────────────────────────────────────
    JarvisCommand(
        name="scanner_marche",
        category="trading",
        description="Scanner le marche MEXC",
        triggers=[
            "scanne le marche", "scanner le marche", "lance le scanner",
            "analyse le marche", "scan mexc", "lance mexc scanner",
        ],
        action_type="script",
        action="mexc_scanner",
    ),
    JarvisCommand(
        name="detecter_breakout",
        category="trading",
        description="Detecter les breakouts",
        triggers=[
            "detecte les breakouts", "cherche les breakouts",
            "breakout detector", "lance breakout", "lance le detecteur",
        ],
        action_type="script",
        action="breakout_detector",
    ),
    JarvisCommand(
        name="pipeline_trading",
        category="trading",
        description="Lancer le pipeline de trading intensif",
        triggers=[
            "lance le pipeline", "pipeline intensif", "demarre le pipeline",
            "lance le trading", "pipeline trading",
        ],
        action_type="script",
        action="pipeline_intensif_v2",
        confirm=True,
    ),
    JarvisCommand(
        name="sniper_breakout",
        category="trading",
        description="Lancer le sniper breakout",
        triggers=[
            "lance le sniper", "sniper breakout", "demarre le sniper",
            "active le sniper",
        ],
        action_type="script",
        action="sniper_breakout",
        confirm=True,
    ),
    JarvisCommand(
        name="statut_cluster",
        category="trading",
        description="Verifier le statut du cluster IA",
        triggers=[
            "statut du cluster", "etat du cluster", "statut cluster",
            "status cluster", "verifie le cluster", "comment va le cluster",
        ],
        action_type="jarvis_tool",
        action="lm_cluster_status",
    ),
    JarvisCommand(
        name="consensus_ia",
        category="trading",
        description="Lancer un consensus multi-IA",
        triggers=[
            "consensus sur {question}", "demande un consensus sur {question}",
            "lance un consensus {question}", "consensus {question}",
        ],
        action_type="jarvis_tool",
        action="consensus:{question}",
        params=["question"],
    ),

    # ── JARVIS CONTROLE ───────────────────────────────────────────────────
    JarvisCommand(
        name="jarvis_aide",
        category="jarvis",
        description="Afficher l'aide JARVIS",
        triggers=[
            "aide", "help", "quelles commandes", "que sais tu faire",
            "liste les commandes", "montre les commandes",
        ],
        action_type="list_commands",
        action="all",
    ),
    JarvisCommand(
        name="jarvis_stop",
        category="jarvis",
        description="Arreter JARVIS",
        triggers=[
            "stop", "arrete", "quitte", "exit", "jarvis stop",
            "arrete jarvis", "ferme jarvis",
        ],
        action_type="exit",
        action="stop",
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# KNOWN APP PATHS (Windows)
# ═══════════════════════════════════════════════════════════════════════════

APP_PATHS: dict[str, str] = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "comet": "comet-browser",
    "firefox": "firefox",
    "edge": "msedge",
    "code": "code",
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "terminal": "wt",
    "powershell": "powershell",
    "cmd": "cmd",
    "notepad": "notepad",
    "bloc notes": "notepad",
    "calculatrice": "calc",
    "calc": "calc",
    "explorateur": "explorer",
    "explorer": "explorer",
    "paint": "mspaint",
    "word": "winword",
    "excel": "excel",
    "lmstudio": "lmstudio",
    "lm studio": "lmstudio",
    "discord": "discord",
    "spotify": "spotify",
    "telegram": "telegram",
    "obs": "obs64",
    "obs studio": "obs64",
    "gestionnaire de taches": "taskmgr",
    "task manager": "taskmgr",
}


# ═══════════════════════════════════════════════════════════════════════════
# SITE ALIASES
# ═══════════════════════════════════════════════════════════════════════════

SITE_ALIASES: dict[str, str] = {
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "youtube": "https://www.youtube.com",
    "github": "https://github.com",
    "twitter": "https://twitter.com",
    "x": "https://twitter.com",
    "reddit": "https://www.reddit.com",
    "facebook": "https://www.facebook.com",
    "linkedin": "https://www.linkedin.com",
    "chatgpt": "https://chat.openai.com",
    "claude": "https://claude.ai",
    "mexc": "https://www.mexc.com",
    "tradingview": "https://www.tradingview.com",
    "coinglass": "https://www.coinglass.com",
    "coinmarketcap": "https://coinmarketcap.com",
    "binance": "https://www.binance.com",
    "n8n": "http://localhost:5678",
    "lm studio": "http://192.168.1.85:1234",
}


# ═══════════════════════════════════════════════════════════════════════════
# FUZZY MATCHING & VOICE CORRECTION
# ═══════════════════════════════════════════════════════════════════════════

# Corrections courantes de reconnaissance vocale (erreurs frequentes)
VOICE_CORRECTIONS: dict[str, str] = {
    # Mots souvent mal reconnus
    "ouvres": "ouvre",
    "ouvert": "ouvre",
    "ouverts": "ouvre",
    "lances": "lance",
    "lancee": "lance",
    "cherches": "cherche",
    "recherches": "recherche",
    "va-sur": "va sur",
    "vasur": "va sur",
    "vas sur": "va sur",
    "demarre": "demarre",
    "demarres": "demarre",
    "navigue": "navigue",
    "navigues": "navigue",
    # Apps mal reconnues
    "crome": "chrome",
    "krome": "chrome",
    "crohm": "chrome",
    "crom": "chrome",
    "grome": "chrome",
    "chronme": "chrome",
    "comete": "comet",
    "comette": "comet",
    "kommet": "comet",
    "komete": "comet",
    "komett": "comet",
    "vscod": "vscode",
    "vis code": "vscode",
    "visualstudiocode": "vscode",
    "el m studio": "lm studio",
    "aile m studio": "lm studio",
    "elle m studio": "lm studio",
    "elle emme studio": "lm studio",
    # Sites mal reconnus
    "gougueule": "google",
    "gougle": "google",
    "gogol": "google",
    "gogle": "google",
    "gemail": "gmail",
    "jimail": "gmail",
    "jmail": "gmail",
    "g mail": "gmail",
    "you tube": "youtube",
    "youtub": "youtube",
    "git hub": "github",
    "guithub": "github",
    "git-hub": "github",
    "tredingview": "tradingview",
    "traiding view": "tradingview",
    "trading vue": "tradingview",
    # Trading mal reconnu
    "breakaout": "breakout",
    "brequaout": "breakout",
    "brecaoutte": "breakout",
    "snipeur": "sniper",
    "snaiper": "sniper",
    "scanne": "scanne",
    "scan": "scanne",
    "skanne": "scanne",
    "pipelaïne": "pipeline",
    "pailpelaïne": "pipeline",
    "consencus": "consensus",
    "consansus": "consensus",
    # Systeme mal reconnu
    "verouille": "verrouille",
    "verrouie": "verrouille",
    "eteint": "eteins",
    "etteint": "eteins",
    "redemarrre": "redemarre",
    "captur": "capture",
    # Mots francais courants mal transcrits
    "processuce": "processus",
    "procaissus": "processus",
    "sisteme": "systeme",
    "sisthem": "systeme",
    "cleussteur": "cluster",
    "clustere": "cluster",
    "téléchargement": "telechargements",
    "telechargement": "telechargements",
}


def correct_voice_text(text: str) -> str:
    """Apply known voice corrections to transcribed text."""
    text = text.lower().strip()

    # Apply word-level corrections
    words = text.split()
    corrected = []
    for word in words:
        corrected.append(VOICE_CORRECTIONS.get(word, word))
    text = " ".join(corrected)

    # Apply phrase-level corrections
    for wrong, right in VOICE_CORRECTIONS.items():
        if wrong in text:
            text = text.replace(wrong, right)

    return text


def similarity(a: str, b: str) -> float:
    """Calculate string similarity ratio (0.0 to 1.0)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def match_command(voice_text: str, threshold: float = 0.55) -> tuple[JarvisCommand | None, dict[str, str], float]:
    """Match voice input to a pre-registered command.

    Returns: (command, extracted_params, confidence_score)
    """
    # Step 1: Correct common voice errors
    corrected = correct_voice_text(voice_text)

    best_match: JarvisCommand | None = None
    best_score: float = 0.0
    best_params: dict[str, str] = {}

    for cmd in COMMANDS:
        for trigger in cmd.triggers:
            # Check if trigger has parameters (phrases a trou)
            if "{" in trigger:
                # Extract parameter pattern
                param_names = re.findall(r"\{(\w+)\}", trigger)
                # Build regex from trigger template
                pattern = trigger
                for pname in param_names:
                    pattern = pattern.replace(f"{{{pname}}}", r"(.+)")
                pattern = "^" + pattern + "$"

                match = re.match(pattern, corrected, re.IGNORECASE)
                if match:
                    score = 0.95
                    params = {param_names[i]: match.group(i + 1).strip() for i in range(len(param_names))}
                    if score > best_score:
                        best_score = score
                        best_match = cmd
                        best_params = params
                else:
                    # Try fuzzy match on the fixed parts
                    fixed_part = re.sub(r"\{(\w+)\}", "", trigger).strip()
                    if fixed_part and fixed_part in corrected:
                        remaining = corrected.replace(fixed_part, "").strip()
                        if remaining:
                            score = 0.80
                            params = {param_names[0]: remaining} if param_names else {}
                            if score > best_score:
                                best_score = score
                                best_match = cmd
                                best_params = params
            else:
                # Exact match
                if corrected == trigger.lower():
                    score = 1.0
                elif trigger.lower() in corrected:
                    score = 0.90
                else:
                    score = similarity(corrected, trigger)

                if score > best_score:
                    best_score = score
                    best_match = cmd
                    best_params = {}

    if best_score < threshold:
        return None, {}, best_score

    return best_match, best_params, best_score


def get_commands_by_category(category: str | None = None) -> list[JarvisCommand]:
    """List commands, optionally filtered by category."""
    if category:
        return [c for c in COMMANDS if c.category == category]
    return COMMANDS


def format_commands_help() -> str:
    """Format all commands as help text for voice output."""
    categories = {}
    for cmd in COMMANDS:
        categories.setdefault(cmd.category, []).append(cmd)

    lines = ["Commandes JARVIS disponibles:"]
    cat_names = {
        "navigation": "Navigation Web",
        "fichiers": "Fichiers & Documents",
        "app": "Applications",
        "systeme": "Systeme Windows",
        "trading": "Trading",
        "jarvis": "Controle JARVIS",
    }
    for cat, cmds in categories.items():
        lines.append(f"\n  {cat_names.get(cat, cat)}:")
        for cmd in cmds:
            trigger_example = cmd.triggers[0]
            lines.append(f"    - {trigger_example} → {cmd.description}")
    return "\n".join(lines)
