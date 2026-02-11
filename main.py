"""JARVIS Turbo - Entry point."""

from __future__ import annotations

import asyncio
import sys

from src.orchestrator import run_once, run_interactive, run_voice


async def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("-i", "--interactive"):
        await run_interactive()
    elif args[0] in ("-v", "--voice", "--vocal"):
        await run_voice()
    elif args[0] in ("-s", "--status"):
        await run_once("Utilise lm_cluster_status et rapporte le statut du cluster.")
    elif args[0] in ("-h", "--help"):
        print(
            "JARVIS Turbo — Orchestrateur IA Distribue\n"
            "\n"
            "Usage:\n"
            "  python main.py                   Mode interactif (REPL)\n"
            "  python main.py -i                Mode interactif (REPL)\n"
            "  python main.py -v                Mode vocal (Voice-First)\n"
            "  python main.py -s                Statut du cluster\n"
            '  python main.py "<prompt>"        Requete unique\n'
            "  python main.py -h                Aide"
        )
    else:
        prompt = " ".join(args)
        await run_once(prompt)


def main_sync() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
