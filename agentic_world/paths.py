from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
REGISTRY_FILE = ROOT / "registry" / "agentic-world.yaml"
KNOWLEDGE_DIR = CONTENT / "knowledge"
ROLES_DIR = CONTENT / "roles"
VERTICALS_DIR = CONTENT / "verticals"
TRACK_WORKFLOW = CONTENT / "workflows" / "track.yaml"
CHARTER_FILE = CONTENT / "charter.md"
PROPOSALS_DIR = CONTENT / "evolution" / "proposals"


def data_root() -> Path:
    override = os.environ.get("AGENTIC_WORLD_DATA_DIR")
    path = Path(override) if override else ROOT / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def jobs_dir() -> Path:
    path = data_root() / "jobs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def pipeline_dir() -> Path:
    path = data_root() / "pipeline"
    path.mkdir(parents=True, exist_ok=True)
    return path


def evolution_log() -> Path:
    path = data_root() / "evolution"
    path.mkdir(parents=True, exist_ok=True)
    return path / "log.jsonl"
