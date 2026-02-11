"""JARVIS MCP Tools — Complete toolkit: LM Studio, Windows, files, browser, trading."""

from __future__ import annotations

import subprocess
import sys
from typing import Any

import httpx
from claude_agent_sdk import tool, create_sdk_mcp_server

from src.config import config, SCRIPTS, PATHS


# ═══════════════════════════════════════════════════════════════════════════
# LM STUDIO TOOLS
# ═══════════════════════════════════════════════════════════════════════════

@tool("lm_query", "Interroger un noeud LM Studio. Args: prompt, node (M1/M2/M3), model (optionnel).", {"prompt": str, "node": str, "model": str})
async def lm_query(args: dict[str, Any]) -> dict[str, Any]:
    prompt = args["prompt"]
    node = config.get_node(args.get("node", "M1"))
    if not node:
        return _error(f"Noeud inconnu: {args.get('node')}")
    model = args.get("model", node.default_model)
    try:
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(f"{node.url}/v1/chat/completions", json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": config.temperature, "max_tokens": config.max_tokens})
            r.raise_for_status()
            return _text(f"[{node.name}/{model}] {r.json()['choices'][0]['message']['content']}")
    except httpx.ConnectError:
        return _error(f"Noeud {node.name} hors ligne")
    except Exception as e:
        return _error(f"Erreur LM Studio: {e}")


@tool("lm_models", "Lister les modeles charges sur un noeud LM Studio.", {"node": str})
async def lm_models(args: dict[str, Any]) -> dict[str, Any]:
    url = config.get_node_url(args.get("node", "M1"))
    if not url:
        return _error("Noeud inconnu")
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{url}/v1/models")
            r.raise_for_status()
            models = [m["id"] for m in r.json().get("data", [])]
            return _text(f"Modeles: {', '.join(models) if models else 'aucun'}")
    except Exception as e:
        return _error(str(e))


@tool("lm_cluster_status", "Sante de tous les noeuds LM Studio du cluster.", {})
async def lm_cluster_status(args: dict[str, Any]) -> dict[str, Any]:
    results, online, total = [], 0, 0
    async with httpx.AsyncClient(timeout=5) as c:
        for n in config.lm_nodes:
            try:
                r = await c.get(f"{n.url}/v1/models")
                r.raise_for_status()
                cnt = len(r.json().get("data", []))
                total += cnt; online += 1
                results.append(f"  [OK] {n.name} ({n.role}) — {n.gpus} GPU, {n.vram_gb}GB — {cnt} modeles")
            except Exception:
                results.append(f"  [--] {n.name} ({n.role}) — hors ligne")
    return _text(f"Cluster: {online}/{len(config.lm_nodes)} en ligne, {total} modeles\n" + "\n".join(results))


@tool("consensus", "Consensus multi-noeuds IA. Args: prompt, nodes (M1,M2,M3).", {"prompt": str, "nodes": str})
async def consensus(args: dict[str, Any]) -> dict[str, Any]:
    prompt = args["prompt"]
    names = [n.strip() for n in args.get("nodes", "M1,M2,M3").split(",")]
    responses = []
    async with httpx.AsyncClient(timeout=120) as c:
        for name in names:
            node = config.get_node(name)
            if not node:
                responses.append(f"[{name}] ERREUR: inconnu"); continue
            try:
                r = await c.post(f"{node.url}/v1/chat/completions", json={"model": node.default_model, "messages": [{"role": "user", "content": prompt}], "temperature": config.temperature, "max_tokens": config.max_tokens})
                r.raise_for_status()
                responses.append(f"[{name}/{node.default_model}] {r.json()['choices'][0]['message']['content']}")
            except Exception as e:
                responses.append(f"[{name}] ERREUR: {e}")
    return _text("Consensus:\n\n" + "\n\n---\n\n".join(responses))


# ═══════════════════════════════════════════════════════════════════════════
# SCRIPTS & PROJETS
# ═══════════════════════════════════════════════════════════════════════════

@tool("run_script", "Executer un script Python indexe. Args: script_name, args.", {"script_name": str, "args": str})
async def run_script(args: dict[str, Any]) -> dict[str, Any]:
    name = args["script_name"]
    path = SCRIPTS.get(name)
    if not path:
        return _error(f"Script inconnu: {name}. Disponibles: {', '.join(sorted(SCRIPTS))}")
    if not path.exists():
        return _error(f"Fichier absent: {path}")
    try:
        cmd = [sys.executable, str(path)]
        if args.get("args"):
            cmd.extend(args["args"].split())
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=str(path.parent))
        out = r.stdout[-3000:] if len(r.stdout) > 3000 else r.stdout
        if r.returncode != 0:
            out += f"\n[STDERR] {r.stderr[-1000:]}"
        return _text(f"[{name}] exit={r.returncode}\n{out}")
    except subprocess.TimeoutExpired:
        return _error(f"Timeout 120s: {name}")
    except Exception as e:
        return _error(str(e))


@tool("list_scripts", "Lister les scripts Python disponibles.", {})
async def list_scripts(args: dict[str, Any]) -> dict[str, Any]:
    lines = [f"  [{'OK' if p.exists() else 'ABSENT'}] {n}: {p}" for n, p in sorted(SCRIPTS.items())]
    return _text("Scripts:\n" + "\n".join(lines))


@tool("list_project_paths", "Lister les dossiers projets indexes.", {})
async def list_project_paths(args: dict[str, Any]) -> dict[str, Any]:
    lines = [f"  [{'OK' if p.exists() else 'ABSENT'}] {n}: {p}" for n, p in sorted(PATHS.items())]
    return _text("Projets:\n" + "\n".join(lines))


# ═══════════════════════════════════════════════════════════════════════════
# WINDOWS — APPLICATIONS
# ═══════════════════════════════════════════════════════════════════════════

@tool("open_app", "Ouvrir une application par nom. Args: name, args.", {"name": str, "args": str})
async def open_app(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import open_application
    return _text(open_application(args["name"], args.get("args", "")))


@tool("close_app", "Fermer une application par nom de processus. Args: name.", {"name": str})
async def close_app(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import close_application
    return _text(close_application(args["name"]))


@tool("open_url", "Ouvrir une URL dans le navigateur. Args: url, browser.", {"url": str, "browser": str})
async def open_url_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import open_url
    return _text(open_url(args["url"], args.get("browser", "chrome")))


# ═══════════════════════════════════════════════════════════════════════════
# WINDOWS — PROCESSUS
# ═══════════════════════════════════════════════════════════════════════════

@tool("list_processes", "Lister les processus Windows. Args: filter.", {"filter": str})
async def list_processes_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import list_processes
    procs = list_processes(args.get("filter"))
    if not procs:
        return _text("Aucun processus.")
    lines = [f"  {p.get('Name','?')} (PID {p.get('Id','?')}) — {round(p.get('WorkingSet64',0)/1048576,1)} MB" for p in procs[:30]]
    return _text(f"Processus ({len(procs)}):\n" + "\n".join(lines))


@tool("kill_process", "Arreter un processus par nom ou PID. Args: target.", {"target": str})
async def kill_process_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import kill_process
    return _text(kill_process(args["target"]))


# ═══════════════════════════════════════════════════════════════════════════
# WINDOWS — FENETRES
# ═══════════════════════════════════════════════════════════════════════════

@tool("list_windows", "Lister toutes les fenetres visibles avec leurs titres.", {})
async def list_windows_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import list_windows
    return _text(list_windows())


@tool("focus_window", "Mettre une fenetre au premier plan. Args: title.", {"title": str})
async def focus_window_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import focus_window
    return _text(focus_window(args["title"]))


@tool("minimize_window", "Minimiser une fenetre. Args: title.", {"title": str})
async def minimize_window_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import minimize_window
    return _text(minimize_window(args["title"]))


@tool("maximize_window", "Maximiser une fenetre. Args: title.", {"title": str})
async def maximize_window_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import maximize_window
    return _text(maximize_window(args["title"]))


# ═══════════════════════════════════════════════════════════════════════════
# WINDOWS — CLAVIER & SOURIS
# ═══════════════════════════════════════════════════════════════════════════

@tool("send_keys", "Envoyer des touches clavier a la fenetre active. Args: keys.", {"keys": str})
async def send_keys_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import send_keys
    return _text(send_keys(args["keys"]))


@tool("type_text", "Taper du texte dans la fenetre active. Args: text.", {"text": str})
async def type_text_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import type_text
    return _text(type_text(args["text"]))


@tool("press_hotkey", "Appuyer sur un raccourci clavier (ctrl+c, alt+tab, win+d). Args: keys.", {"keys": str})
async def press_hotkey_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import press_hotkey
    return _text(press_hotkey(args["keys"]))


@tool("mouse_click", "Cliquer a des coordonnees ecran. Args: x, y.", {"x": int, "y": int})
async def mouse_click_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import mouse_click
    return _text(mouse_click(args["x"], args["y"]))


# ═══════════════════════════════════════════════════════════════════════════
# WINDOWS — CLIPBOARD
# ═══════════════════════════════════════════════════════════════════════════

@tool("clipboard_get", "Lire le contenu du presse-papier.", {})
async def clipboard_get_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import clipboard_get
    return _text(f"Presse-papier: {clipboard_get()}")


@tool("clipboard_set", "Ecrire dans le presse-papier. Args: text.", {"text": str})
async def clipboard_set_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import clipboard_set
    return _text(clipboard_set(args["text"]))


# ═══════════════════════════════════════════════════════════════════════════
# WINDOWS — FICHIERS
# ═══════════════════════════════════════════════════════════════════════════

@tool("open_folder", "Ouvrir un dossier dans l'Explorateur. Args: path.", {"path": str})
async def open_folder_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import open_folder
    return _text(open_folder(args["path"]))


@tool("list_folder", "Lister le contenu d'un dossier. Args: path, pattern.", {"path": str, "pattern": str})
async def list_folder_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import list_folder
    return _text(list_folder(args["path"], args.get("pattern", "*")))


@tool("create_folder", "Creer un nouveau dossier. Args: path.", {"path": str})
async def create_folder_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import create_folder
    return _text(create_folder(args["path"]))


@tool("copy_item", "Copier un fichier ou dossier. Args: source, dest.", {"source": str, "dest": str})
async def copy_item_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import copy_item
    return _text(copy_item(args["source"], args["dest"]))


@tool("move_item", "Deplacer un fichier ou dossier. Args: source, dest.", {"source": str, "dest": str})
async def move_item_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import move_item
    return _text(move_item(args["source"], args["dest"]))


@tool("delete_item", "Supprimer un fichier (vers la corbeille). Args: path.", {"path": str})
async def delete_item_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import delete_item
    return _text(delete_item(args["path"]))


@tool("read_text_file", "Lire un fichier texte. Args: path, lines.", {"path": str, "lines": int})
async def read_text_file_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import read_file
    return _text(read_file(args["path"], args.get("lines", 50)))


@tool("write_text_file", "Ecrire dans un fichier texte. Args: path, content.", {"path": str, "content": str})
async def write_text_file_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import write_file
    return _text(write_file(args["path"], args["content"]))


@tool("search_files", "Chercher des fichiers recursivement. Args: path, pattern.", {"path": str, "pattern": str})
async def search_files_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import search_files
    return _text(search_files(args["path"], args["pattern"]))


# ═══════════════════════════════════════════════════════════════════════════
# WINDOWS — AUDIO
# ═══════════════════════════════════════════════════════════════════════════

@tool("volume_up", "Augmenter le volume systeme.", {})
async def volume_up_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import volume_up
    return _text(volume_up())


@tool("volume_down", "Baisser le volume systeme.", {})
async def volume_down_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import volume_down
    return _text(volume_down())


@tool("volume_mute", "Basculer muet/son.", {})
async def volume_mute_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import volume_mute
    return _text(volume_mute())


# ═══════════════════════════════════════════════════════════════════════════
# WINDOWS — ECRAN
# ═══════════════════════════════════════════════════════════════════════════

@tool("screenshot", "Prendre une capture d'ecran. Args: filename.", {"filename": str})
async def screenshot_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import screenshot
    return _text(screenshot(args.get("filename", "")))


@tool("screen_resolution", "Obtenir la resolution de l'ecran.", {})
async def screen_resolution_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import get_screen_resolution
    return _text(get_screen_resolution())


# ═══════════════════════════════════════════════════════════════════════════
# WINDOWS — SYSTEME
# ═══════════════════════════════════════════════════════════════════════════

@tool("system_info", "Infos systeme completes: CPU, RAM, GPU, disques, uptime.", {})
async def system_info_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import get_system_info
    info = get_system_info()
    return _text("Systeme:\n" + "\n".join(f"  {k}: {v}" for k, v in info.items()))


@tool("gpu_info", "Infos detaillees GPU (VRAM, driver).", {})
async def gpu_info_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import get_gpu_info
    return _text(get_gpu_info())


@tool("network_info", "Adresses IP et interfaces reseau.", {})
async def network_info_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import get_network_info
    return _text(get_network_info())


@tool("powershell_run", "Executer une commande PowerShell. Args: command.", {"command": str})
async def powershell_run_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import run_powershell
    r = run_powershell(args["command"], timeout=60)
    out = r["stdout"] if r["success"] else f"ERREUR: {r['stderr']}"
    return _text(f"[PS] exit={r['exit_code']}\n{out}")


@tool("lock_screen", "Verrouiller le PC.", {})
async def lock_screen_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import lock_screen
    return _text(lock_screen())


@tool("shutdown_pc", "Eteindre le PC.", {})
async def shutdown_pc_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import shutdown_pc
    return _text(shutdown_pc())


@tool("restart_pc", "Redemarrer le PC.", {})
async def restart_pc_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import restart_pc
    return _text(restart_pc())


@tool("sleep_pc", "Mettre le PC en veille.", {})
async def sleep_pc_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import sleep_pc
    return _text(sleep_pc())


# ═══════════════════════════════════════════════════════════════════════════
# WINDOWS — SERVICES
# ═══════════════════════════════════════════════════════════════════════════

@tool("list_services", "Lister les services Windows. Args: filter.", {"filter": str})
async def list_services_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import list_services
    return _text(list_services(args.get("filter", "")))


@tool("start_service", "Demarrer un service Windows. Args: name.", {"name": str})
async def start_service_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import start_service
    return _text(start_service(args["name"]))


@tool("stop_service", "Arreter un service Windows. Args: name.", {"name": str})
async def stop_service_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import stop_service
    return _text(stop_service(args["name"]))


# ═══════════════════════════════════════════════════════════════════════════
# WINDOWS — RESEAU
# ═══════════════════════════════════════════════════════════════════════════

@tool("wifi_networks", "Lister les reseaux WiFi disponibles.", {})
async def wifi_networks_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import get_wifi_networks
    return _text(get_wifi_networks())


@tool("ping", "Ping un hote. Args: host.", {"host": str})
async def ping_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import ping_host
    return _text(ping_host(args["host"]))


@tool("get_ip", "Obtenir les adresses IP locales.", {})
async def get_ip_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import get_ip_address
    return _text(get_ip_address())


# ═══════════════════════════════════════════════════════════════════════════
# WINDOWS — REGISTRE
# ═══════════════════════════════════════════════════════════════════════════

@tool("registry_read", "Lire une valeur du registre Windows. Args: path, name.", {"path": str, "name": str})
async def registry_read_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import registry_get
    return _text(registry_get(args["path"], args.get("name", "")))


@tool("registry_write", "Ecrire une valeur dans le registre. Args: path, name, value, type.", {"path": str, "name": str, "value": str, "type": str})
async def registry_write_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import registry_set
    return _text(registry_set(args["path"], args["name"], args["value"], args.get("type", "String")))


# ═══════════════════════════════════════════════════════════════════════════
# WINDOWS — NOTIFICATIONS & VOIX
# ═══════════════════════════════════════════════════════════════════════════

@tool("notify", "Notification toast Windows. Args: title, message.", {"title": str, "message": str})
async def notify_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import notify_windows
    ok = notify_windows(args.get("title", "JARVIS"), args.get("message", ""))
    return _text(f"Notification {'OK' if ok else 'echouee'}")


@tool("speak", "Synthese vocale Windows SAPI. Args: text.", {"text": str})
async def speak_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.voice import speak_text
    ok = await speak_text(args.get("text", ""))
    return _text(f"Parole {'OK' if ok else 'echouee'}")


@tool("scheduled_tasks", "Lister les taches planifiees Windows. Args: filter.", {"filter": str})
async def scheduled_tasks_tool(args: dict[str, Any]) -> dict[str, Any]:
    from src.windows import list_scheduled_tasks
    return _text(list_scheduled_tasks(args.get("filter", "")))


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _text(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}

def _error(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}], "is_error": True}


# ═══════════════════════════════════════════════════════════════════════════
# ASSEMBLE MCP SERVER — ALL TOOLS
# ═══════════════════════════════════════════════════════════════════════════

jarvis_server = create_sdk_mcp_server(
    name="jarvis",
    version="3.0.0",
    tools=[
        # LM Studio (4)
        lm_query, lm_models, lm_cluster_status, consensus,
        # Scripts & projets (3)
        run_script, list_scripts, list_project_paths,
        # Applications (3)
        open_app, close_app, open_url_tool,
        # Processus (2)
        list_processes_tool, kill_process_tool,
        # Fenetres (4)
        list_windows_tool, focus_window_tool, minimize_window_tool, maximize_window_tool,
        # Clavier & souris (4)
        send_keys_tool, type_text_tool, press_hotkey_tool, mouse_click_tool,
        # Clipboard (2)
        clipboard_get_tool, clipboard_set_tool,
        # Fichiers (8)
        open_folder_tool, list_folder_tool, create_folder_tool,
        copy_item_tool, move_item_tool, delete_item_tool,
        read_text_file_tool, write_text_file_tool, search_files_tool,
        # Audio (3)
        volume_up_tool, volume_down_tool, volume_mute_tool,
        # Ecran (2)
        screenshot_tool, screen_resolution_tool,
        # Systeme (7)
        system_info_tool, gpu_info_tool, network_info_tool, powershell_run_tool,
        lock_screen_tool, shutdown_pc_tool, restart_pc_tool, sleep_pc_tool,
        # Services (3)
        list_services_tool, start_service_tool, stop_service_tool,
        # Reseau (3)
        wifi_networks_tool, ping_tool, get_ip_tool,
        # Registre (2)
        registry_read_tool, registry_write_tool,
        # Notifications & voix (3)
        notify_tool, speak_tool, scheduled_tasks_tool,
    ],
)
