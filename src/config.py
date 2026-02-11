"""JARVIS configuration — Real cluster, models, routing, project paths."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

JARVIS_VERSION = "10.1"

# ── Project paths (existing codebase) ──────────────────────────────────────
PATHS = {
    "carV1":          Path("F:/BUREAU/carV1"),
    "mcp_lmstudio":   Path("F:/BUREAU/MCP_MCPLMSTUDIO1"),
    "lmstudio_backup": Path("F:/BUREAU/LMSTUDIO_BACKUP"),
    "prod_intensive":  Path("F:/BUREAU/PROD_INTENSIVE_V1"),
    "trading_v2":      Path("F:/BUREAU/TRADING_V2_PRODUCTION"),
    "turbo":           Path("F:/BUREAU/turbo"),
}

# ── Existing scripts index ─────────────────────────────────────────────────
SCRIPTS = {
    # Core orchestration
    "multi_ia_orchestrator": PATHS["carV1"] / "python_scripts/core/multi_ia_orchestrator.py",
    "unified_orchestrator":  PATHS["carV1"] / "python_scripts/core/unified_orchestrator.py",
    "gpu_pipeline":          PATHS["carV1"] / "python_scripts/core/gpu_pipeline.py",
    # Scanners
    "mexc_scanner":          PATHS["carV1"] / "python_scripts/scanners/mexc_scanner.py",
    "breakout_detector":     PATHS["carV1"] / "python_scripts/scanners/breakout_detector.py",
    "gap_detector":          PATHS["carV1"] / "python_scripts/scanners/gap_detector.py",
    # Utils
    "live_data_connector":   PATHS["carV1"] / "python_scripts/utils/live_data_connector.py",
    "coinglass_client":      PATHS["carV1"] / "python_scripts/utils/coinglass_client.py",
    "position_tracker":      PATHS["carV1"] / "python_scripts/utils/position_tracker.py",
    "perplexity_client":     PATHS["carV1"] / "python_scripts/utils/perplexity_client.py",
    # Strategies
    "all_strategies":        PATHS["carV1"] / "python_scripts/strategies/all_strategies.py",
    "advanced_strategies":   PATHS["carV1"] / "python_scripts/strategies/advanced_strategies.py",
    # Trading MCP (the big one — 70+ tools)
    "trading_mcp_v3":        PATHS["trading_v2"] / "trading_mcp_ultimate_v3.py",
    "lmstudio_mcp_bridge":   PATHS["lmstudio_backup"] / "mcp_configs/lmstudio_mcp_bridge.py",
    # Pipelines
    "pipeline_intensif_v2":  PATHS["prod_intensive"] / "scripts/pipeline_intensif_v2.py",
    "pipeline_intensif":     PATHS["mcp_lmstudio"] / "scripts/pipeline_intensif.py",
    # Trading scripts
    "river_scalp_1min":      PATHS["trading_v2"] / "scripts/river_scalp_1min.py",
    "execute_trident":       PATHS["trading_v2"] / "scripts/execute_trident.py",
    "sniper_breakout":       PATHS["trading_v2"] / "scripts/sniper_breakout.py",
    "sniper_10cycles":       PATHS["trading_v2"] / "scripts/sniper_10cycles.py",
    "auto_cycle_10":         PATHS["trading_v2"] / "scripts/auto_cycle_10.py",
    "hyper_scan_v2":         PATHS["trading_v2"] / "scripts/hyper_scan_v2.py",
    # Voice
    "voice_driver":          PATHS["trading_v2"] / "voice_system/voice_driver.py",
    # Dashboard
    "dashboard":             PATHS["mcp_lmstudio"] / "dashboard/app.py",
}


@dataclass
class LMStudioNode:
    name: str
    url: str
    role: str
    gpus: int = 0
    vram_gb: int = 0
    default_model: str = ""
    weight: float = 1.0
    use_cases: list[str] = field(default_factory=list)


@dataclass
class JarvisConfig:
    version: str = JARVIS_VERSION
    mode: str = "DUAL_CORE"

    # ── Real cluster ─────────────────────────────────────────────────────
    # M1: RTX 2060 (12.88GB) + 3x GTX 1660 SUPER (6.44GB) + RTX 3080 (10.74GB) = ~43GB
    # M2: 3 GPU, 24GB VRAM
    # M3: 2 GPU, 16GB VRAM
    # Total: 10 GPU, ~83 GB VRAM
    lm_nodes: list[LMStudioNode] = field(default_factory=lambda: [
        LMStudioNode(
            "M1", os.getenv("LM_STUDIO_1_URL", "http://localhost:1234"),
            "deep_analysis", gpus=5, vram_gb=43,
            default_model="qwen3-30b-a3b-instruct-2507", weight=1.3,
            use_cases=["Analyse technique", "Elliott waves", "Patterns complexes"],
        ),
        LMStudioNode(
            "M2", os.getenv("LM_STUDIO_2_URL", "http://192.168.1.26:1234"),
            "fast_inference", gpus=3, vram_gb=24,
            default_model="nvidia/nemotron-3-nano", weight=1.0,
            use_cases=["Trading signals", "Quick responses", "Code generation"],
        ),
        LMStudioNode(
            "M3", os.getenv("LM_STUDIO_3_URL", "http://192.168.1.113:1234"),
            "validator", gpus=2, vram_gb=16,
            default_model="mistral-7b-instruct-v0.3", weight=0.8,
            use_cases=["Consensus", "Validation", "Quick checks"],
        ),
    ])

    default_model: str = field(
        default_factory=lambda: os.getenv("LM_STUDIO_DEFAULT_MODEL", "qwen/qwen3-30b-a3b-2507")
    )

    # ── Model catalog (verified loaded on M1) ────────────────────────────
    models: dict[str, str] = field(default_factory=lambda: {
        "default":    "qwen/qwen3-30b-a3b-2507",
        "coding":     "qwen/qwen3-coder-30b",
        "fast":       "nvidia/nemotron-3-nano",
        "vision":     "zai-org/glm-4.7-flash",
        "dev":        "mistralai/devstral-small-2-2512",
        "general":    "openai/gpt-oss-20b",
        "embeddings": "text-embedding-nomic-embed-text-v1.5",
    })

    # ── Routing rules ──────────────────────────────────────────────────────
    routing: dict[str, list[str]] = field(default_factory=lambda: {
        "short_answer":   ["M3", "M2"],
        "deep_analysis":  ["M1"],
        "trading_signal": ["M2", "M1"],
        "code_generation": ["M2"],
        "validation":     ["M3"],
        "critical":       ["M1", "M2", "M3"],
        "consensus":      ["M1", "M2", "M3"],
    })

    # ── Trading config ─────────────────────────────────────────────────────
    exchange: str = "mexc"
    trading_mode: str = "futures"
    pairs: list[str] = field(default_factory=lambda: [
        "BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT", "SUI/USDT:USDT",
        "PEPE/USDT:USDT", "DOGE/USDT:USDT", "XRP/USDT:USDT", "ADA/USDT:USDT",
        "AVAX/USDT:USDT", "LINK/USDT:USDT",
    ])
    leverage: int = 10
    tp_percent: float = 0.4
    sl_percent: float = 0.25

    # Generation params
    temperature: float = 0.7
    max_tokens: int = 8192

    def get_node_url(self, name: str) -> str | None:
        for node in self.lm_nodes:
            if node.name == name:
                return node.url
        return None

    def get_node(self, name: str) -> LMStudioNode | None:
        for node in self.lm_nodes:
            if node.name == name:
                return node
        return None

    def route(self, task_type: str) -> list[str]:
        """Return node names for a given task type."""
        return self.routing.get(task_type, ["M1"])


config = JarvisConfig()
