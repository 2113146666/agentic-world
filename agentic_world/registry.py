from __future__ import annotations

from typing import Literal

import yaml
from pydantic import BaseModel, Field

from agentic_world.paths import REGISTRY_FILE, ROLES_DIR, TRACK_WORKFLOW, VERTICALS_DIR
from agentic_world.util import AgenticWorldError, read_text

Kind = Literal["vertical", "track"]


class Track(BaseModel):
    id: str
    name: str
    scope: str
    layer: str
    category: str


class Stage(BaseModel):
    id: str
    name: str
    agent: str
    done_when: str


class Vertical(BaseModel):
    id: str
    name: str
    focus: str
    category: str
    constraints: list[str] = Field(default_factory=list)
    stages: list[Stage]


class Registry(BaseModel):
    motto: str
    tracks: list[Track]
    roles: list[str]
    verticals: list[Vertical] = Field(default_factory=list)


class WorkContext(BaseModel):
    kind: Kind
    domain_id: str
    name: str
    focus: str
    constraints: list[str]
    stages: list[Stage]
    category: str
    layer: str


def load_registry() -> Registry:
    raw = yaml.safe_load(read_text(REGISTRY_FILE)) or {}
    registry = Registry.model_validate(raw)
    verticals: list[Vertical] = []
    for path in sorted(VERTICALS_DIR.glob("*.yaml")):
        data = yaml.safe_load(read_text(path)) or {}
        verticals.append(Vertical.model_validate(data))
    registry.verticals = verticals
    _validate(registry)
    return registry


def _validate(registry: Registry) -> None:
    roles = set(registry.roles)
    if roles != {"product", "tech", "test", "ops"}:
        raise AgenticWorldError("垂类角色必须是 product、tech、test、ops")
    for role in registry.roles:
        path = ROLES_DIR / f"{role}.md"
        if not path.is_file():
            raise AgenticWorldError(f"缺少角色说明：{path}")

    seen_ids: set[str] = set()
    for track in registry.tracks:
        if track.id in seen_ids:
            raise AgenticWorldError(f"赛道 id 重复：{track.id}")
        seen_ids.add(track.id)
    for vertical in registry.verticals:
        if vertical.id in seen_ids:
            raise AgenticWorldError(f"id 与赛道或其他垂类重复：{vertical.id}")
        seen_ids.add(vertical.id)
        agents = {stage.agent for stage in vertical.stages}
        missing = roles - agents
        if missing:
            raise AgenticWorldError(f"{vertical.name} 缺少角色：{', '.join(sorted(missing))}")
        unknown = agents - roles
        if unknown:
            raise AgenticWorldError(f"{vertical.name} 有未登记角色：{', '.join(sorted(unknown))}")
    track_stages = _track_stages()
    track_agents = {stage.agent for stage in track_stages}
    if roles - track_agents:
        raise AgenticWorldError("基础赛道工作流没有覆盖四个角色")


def _track_stages() -> list[Stage]:
    raw = yaml.safe_load(read_text(TRACK_WORKFLOW)) or {}
    stages = [Stage.model_validate(item) for item in raw.get("stages", [])]
    if not stages:
        raise AgenticWorldError("基础赛道工作流是空的")
    return stages


def known_categories(registry: Registry) -> set[str]:
    categories = {track.category for track in registry.tracks}
    categories.update(vertical.category for vertical in registry.verticals)
    categories.add("venues")
    return categories


def context_for(registry: Registry, domain_id: str) -> WorkContext:
    for vertical in registry.verticals:
        if vertical.id == domain_id:
            return WorkContext(
                kind="vertical",
                domain_id=vertical.id,
                name=vertical.name,
                focus=vertical.focus,
                constraints=list(vertical.constraints),
                stages=vertical.stages,
                category=vertical.category,
                layer="compound",
            )
    for track in registry.tracks:
        if track.id == domain_id:
            return WorkContext(
                kind="track",
                domain_id=track.id,
                name=track.name,
                focus=track.scope,
                constraints=[],
                stages=_track_stages(),
                category=track.category,
                layer=track.layer,
            )
    names = [item.id for item in registry.tracks] + [item.id for item in registry.verticals]
    raise AgenticWorldError(f"未知领域：{domain_id}。可选：{', '.join(names)}")


def render_role(role: str, work: WorkContext) -> str:
    if role not in {"product", "tech", "test", "ops"}:
        raise AgenticWorldError(f"未知角色：{role}")
    template = read_text(ROLES_DIR / f"{role}.md")
    constraints = "\n".join(f"- {item}" for item in work.constraints) or "- 无额外约束"
    stages = "\n".join(f"- {stage.name}（{stage.agent}）：完成标准是{stage.done_when}" for stage in work.stages)
    replacements = {
        "{{name}}": work.name,
        "{{focus}}": work.focus,
        "{{constraints}}": constraints,
        "{{stages}}": stages,
    }
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace(key, value)
    return rendered.strip()
