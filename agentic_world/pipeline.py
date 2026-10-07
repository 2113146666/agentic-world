from __future__ import annotations

import threading
from uuid import uuid4

from agentic_world.guards import FINANCE_DISCLAIMER
from agentic_world.jobs import llm_mode, now
from agentic_world.paths import pipeline_dir
from agentic_world.util import AgenticWorldError, read_json, write_json

_lock = threading.Lock()

SEEDS = [
    (
        "一个会记住选择的故事：人物行为由卡片约束，支线必须先在世界观规则里长出来，再被选中。",
        ["novel", "character-card"],
    ),
    (
        "一集漫剧先选定开源或闭源作为主路径，另一条只记录差异。",
        ["comic"],
    ),
    (
        "游戏先做一轮不看讲解也能玩完的核心循环。",
        ["game"],
    ),
]


def _append(filename: str, item: dict) -> dict:
    path = pipeline_dir() / filename
    with _lock:
        items = read_json(path, [])
        items.append(item)
        write_json(path, items)
    return item


def _latest(filename: str, label: str) -> dict:
    items = read_json(pipeline_dir() / filename, [])
    if not items:
        raise AgenticWorldError(f"还没有{label}")
    return items[-1]


def _replace_latest_world(world: dict) -> None:
    path = pipeline_dir() / "worlds.json"
    with _lock:
        items = read_json(path, [])
        if not items:
            raise AgenticWorldError("还没有世界观")
        items[-1] = world
        write_json(path, items)


def inspire_add(raw: str, tags: list[str]) -> dict:
    text = raw.strip()
    if not text:
        raise AgenticWorldError("灵感是空的")
    item = {
        "id": f"i_{uuid4().hex[:8]}",
        "raw": text,
        "tags": [tag.strip() for tag in tags if tag.strip()],
        "created_at": now(),
    }
    return _append("inspire.json", item)


def inspire_seed() -> dict:
    items = [inspire_add(raw, tags) for raw, tags in SEEDS]
    return {"count": len(items), "items": items}


def inspire_list() -> dict:
    items = read_json(pipeline_dir() / "inspire.json", [])
    return {"count": len(items), "items": items}


def inspire_export(title: str, theme: str | None) -> dict:
    items = read_json(pipeline_dir() / "inspire.json", [])
    if not items:
        raise AgenticWorldError("还没有灵感。先添加，或执行 seed。")
    batch = {
        "id": f"b_{uuid4().hex[:8]}",
        "title": title.strip() or "untitled",
        "theme": theme,
        "items": items,
        "created_at": now(),
    }
    return _append("batches.json", batch)


def world_build(name: str | None) -> dict:
    batch = _latest("batches.json", "灵感 batch。先导出。")
    world = {
        "id": f"w_{uuid4().hex[:8]}",
        "name": (name or "").strip() or batch["title"],
        "source_batch": batch["id"],
        "theme": batch.get("theme"),
        "rules": [
            "每条支线都能回溯到一条灵感",
            "未选支线保留，不删除",
            "选定支线后再补人物卡",
        ],
        "choices": [
            {
                "id": f"c{index}",
                "from_inspire": item["id"],
                "summary": item["raw"],
                "selected": False,
            }
            for index, item in enumerate(batch["items"], start=1)
        ],
        "character_cards": [],
        "mode": llm_mode(),
        "created_at": now(),
    }
    return _append("worlds.json", world)


def world_list() -> dict:
    items = read_json(pipeline_dir() / "worlds.json", [])
    return {"count": len(items), "items": items}


def select_choice(choice_id: str, card_name: str = "", card_want: str = "", note: str = "") -> dict:
    world = _latest("worlds.json", "世界观。先构建。")
    found = False
    for choice in world["choices"]:
        choice["selected"] = choice["id"] == choice_id
        found = found or choice["selected"]
    if not found:
        known = ", ".join(choice["id"] for choice in world["choices"])
        raise AgenticWorldError(f"没有这条支线：{choice_id}。可选：{known}")
    card = None
    if card_name.strip():
        card = {
            "name": card_name.strip(),
            "want": card_want.strip(),
            "constraint": "行为要能回溯到这张卡",
        }
        world["character_cards"].append(card)
    _replace_latest_world(world)
    selection = {
        "id": f"s_{uuid4().hex[:8]}",
        "world_id": world["id"],
        "choice_id": choice_id,
        "card": card,
        "note": note.strip(),
        "created_at": now(),
    }
    _append("selections.json", selection)
    return {"selection": selection, "world": world}


def transform_run(include_comic: bool = True, include_game: bool = True) -> dict:
    world = _latest("worlds.json", "世界观。先构建。")
    if not world["choices"]:
        raise AgenticWorldError("世界观里没有可选支线")
    selected = next((choice for choice in world["choices"] if choice["selected"]), None)
    implicit = selected is None
    if selected is None:
        selected = world["choices"][0]
    slots = {
        "novel": {
            "status": "empty",
            "brief": selected["summary"],
        }
    }
    if include_comic:
        slots["comic"] = {
            "status": "empty",
            "path": "先选定开源或闭源",
        }
    if include_game:
        slots["game"] = {
            "status": "empty",
            "path": "先定一个核心循环",
        }
    bundle = {
        "id": f"r_{uuid4().hex[:8]}",
        "world_id": world["id"],
        "choice_id": selected["id"],
        "implicit_choice": implicit,
        "brief": selected["summary"],
        "slots": slots,
        "mode": llm_mode(),
        "next": "槽位是空的。用 python -m agentic_world job new 交给对应角色；接入模型后也只填槽位，不另起一套流水线。",
        "created_at": now(),
    }
    return _append("bundles.json", bundle)


def quant_advise() -> dict:
    bundle = _latest("bundles.json", "转化结果。先运行转化。")
    report = {
        "id": f"q_{uuid4().hex[:8]}",
        "bundle_id": bundle["id"],
        "disclaimer": FINANCE_DISCLAIMER,
        "signals": [],
        "orders": [],
        "mode": llm_mode(),
        "note": "模板模式不生成信号。接入模型后也只写教育情景，不实盘下单。",
        "created_at": now(),
    }
    return _append("reports.json", report)


def latest_named(filename: str, label: str) -> dict:
    return _latest(filename, label)
