from __future__ import annotations

from agentic_world.paths import CHARTER_FILE
from agentic_world.util import read_text, sha256_text

FINANCE_DISCLAIMER = (
    "【风险提示】本输出仅供教育与模拟，不构成投资建议，不承诺任何收益，不做实盘下单。"
)


def charter_text() -> str:
    text = read_text(CHARTER_FILE).strip()
    if "第一性原理" not in text or "正式讨论" not in text:
        raise RuntimeError("content/charter.md 缺少原则或讨论门禁")
    return text


def charter_hash() -> str:
    return sha256_text(charter_text())


def new_sensitivity_card(topic: str) -> dict:
    return {
        "topic": topic.strip(),
        "touches_real_politics": None,
        "kinds": ["政治人物", "选举", "抗议", "领土争议"],
        "decision": "needs_human",
        "reviewer": "",
        "note": "未回答视同需要人工复核。命中任一类时不得自动发布。",
    }


def decide_sensitivity(touches_real_politics: bool | None) -> str:
    if touches_real_politics is False:
        return "public"
    return "needs_human"
