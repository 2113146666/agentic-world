from __future__ import annotations

import json
from uuid import uuid4

import yaml

from agentic_world.jobs import now
from agentic_world.paths import PROPOSALS_DIR, VERTICALS_DIR, evolution_log
from agentic_world.registry import load_registry
from agentic_world.util import AgenticWorldError, check_slug, read_text, write_text

DEFAULT_STAGES = [
    {"id": "capture", "name": "捕获", "agent": "product", "done_when": "写清用户和可观察的成功标准"},
    {"id": "evolve", "name": "演化", "agent": "tech", "done_when": "给出至少两条复用现有接口的做法"},
    {"id": "select", "name": "选择", "agent": "product", "done_when": "选定一条，其余保留"},
    {"id": "produce", "name": "产出", "agent": "tech", "done_when": "留下可检查的产物，或明确的空槽位"},
    {"id": "review", "name": "评测", "agent": "test", "done_when": "每条成功标准都有通过或失败"},
    {"id": "operate", "name": "运转", "agent": "ops", "done_when": "写下可重复的步骤，和一条下次评测点"},
]


def create_vertical(
    vertical_id: str,
    name: str,
    focus: str,
    category: str,
) -> dict:
    check_slug(vertical_id, "垂类 id")
    check_slug(category, "分类")
    if not name.strip() or not focus.strip():
        raise AgenticWorldError("名称和焦点都不能空")
    registry = load_registry()
    if any(item.id == vertical_id for item in registry.tracks) or any(
        item.id == vertical_id for item in registry.verticals
    ):
        raise AgenticWorldError(f"id 已被占用：{vertical_id}")
    path = VERTICALS_DIR / f"{vertical_id}.yaml"
    if path.exists():
        raise AgenticWorldError(f"文件已存在：{path}")
    document = {
        "id": vertical_id,
        "name": name.strip(),
        "focus": focus.strip(),
        "category": category,
        "constraints": [],
        "stages": DEFAULT_STAGES,
    }
    write_text(path, yaml.safe_dump(document, allow_unicode=True, sort_keys=False))
    try:
        load_registry()
    except Exception:
        path.unlink(missing_ok=True)
        raise
    document["file"] = str(path)
    document["next"] = "在 content/knowledge 加一条同分类的说明，前端侧栏才会出现这个分类名。"
    return document


def propose(target: str, reason: str, change: str, author_role: str) -> dict:
    registry = load_registry()
    if author_role not in registry.roles:
        raise AgenticWorldError(f"未知角色：{author_role}")
    if not reason.strip() or not change.strip() or not target.strip():
        raise AgenticWorldError("提案要写目标、原因和改动")
    proposal_id = f"e_{uuid4().hex[:8]}"
    document = {
        "id": proposal_id,
        "target": target.strip(),
        "reason": reason.strip(),
        "change": change.strip(),
        "author_role": author_role,
        "status": "proposed",
        "created_at": now(),
    }
    path = PROPOSALS_DIR / f"{proposal_id}.yaml"
    write_text(path, yaml.safe_dump(document, allow_unicode=True, sort_keys=False))
    document["file"] = str(path)
    return document


def list_proposals() -> dict:
    items = []
    if PROPOSALS_DIR.exists():
        for path in sorted(PROPOSALS_DIR.glob("*.yaml")):
            loaded = yaml.safe_load(read_text(path)) or {}
            items.append(loaded)
    return {"count": len(items), "items": items}


def accept_proposal(proposal_id: str) -> dict:
    check_slug(proposal_id, "提案 id")
    path = PROPOSALS_DIR / f"{proposal_id}.yaml"
    if not path.is_file():
        raise AgenticWorldError(f"没有这个提案：{proposal_id}")
    document = yaml.safe_load(read_text(path)) or {}
    document["status"] = "accepted"
    document["accepted_at"] = now()
    write_text(path, yaml.safe_dump(document, allow_unicode=True, sort_keys=False))
    line = {
        "at": document["accepted_at"],
        "proposal_id": proposal_id,
        "target": document.get("target", ""),
        "action": "accepted",
    }
    with evolution_log().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line, ensure_ascii=False) + "\n")
    document["note"] = "已记录接受。目标文件没有自动改写，按 change 改完再跑对应评测。"
    return document
