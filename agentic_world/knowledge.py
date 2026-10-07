from __future__ import annotations

import yaml
from pydantic import BaseModel, Field, field_validator

from agentic_world.paths import KNOWLEDGE_DIR, ROOT
from agentic_world.registry import known_categories, load_registry
from agentic_world.util import AgenticWorldError, read_text

LAYERS = {"foundation", "frontier", "compound"}


class Source(BaseModel):
    title: str
    url: str = ""
    date: str | None = None


class Entry(BaseModel):
    id: str
    title: str
    layer: str
    category: str
    tags: list[str] = Field(default_factory=list)
    summary: str
    bullets: list[str] = Field(default_factory=list)
    points: list[str] = Field(default_factory=list)
    misconceptions: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    updated: str
    path: str | None = None

    @field_validator("layer")
    @classmethod
    def known_layer(cls, value: str) -> str:
        if value not in LAYERS:
            raise ValueError(f"未知的层：{value}")
        return value


def _split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text.strip()
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text.strip()
    meta = yaml.safe_load(parts[1]) or {}
    if not isinstance(meta, dict):
        raise AgenticWorldError("知识条目的文首必须是映射")
    return meta, parts[2].strip()


class KnowledgeIndex:
    def __init__(self) -> None:
        self._entries: list[Entry] | None = None

    def reload(self) -> int:
        registry = load_registry()
        allowed = known_categories(registry)
        entries: list[Entry] = []
        seen: set[str] = set()
        for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
            meta, body = _split_frontmatter(read_text(path))
            meta.setdefault("id", path.stem)
            meta.pop("owner", None)
            meta.pop("secondary", None)
            if meta["category"] not in allowed:
                raise AgenticWorldError(f"{path.name} 的分类未登记：{meta['category']}")
            points = list(meta.get("points") or [])
            bullets = list(meta.get("bullets") or points)
            meta["points"] = points or bullets
            meta["bullets"] = bullets or points
            meta["path"] = str(path.relative_to(ROOT))
            if body:
                meta["summary"] = meta.get("summary") or body.splitlines()[0]
            try:
                entry = Entry.model_validate(meta)
            except Exception as exc:
                raise AgenticWorldError(f"{path.name} 无法读取：{exc}") from exc
            if entry.id in seen:
                raise AgenticWorldError(f"知识 id 重复：{entry.id}")
            seen.add(entry.id)
            entries.append(entry)
        self._entries = entries
        return len(entries)

    def entries(self) -> list[Entry]:
        if self._entries is None:
            self.reload()
        return list(self._entries or [])

    def meta(self) -> dict:
        items = self.entries()
        layers: dict[str, int] = {}
        categories: dict[str, int] = {}
        tags: dict[str, int] = {}
        for entry in items:
            layers[entry.layer] = layers.get(entry.layer, 0) + 1
            categories[entry.category] = categories.get(entry.category, 0) + 1
            for tag in entry.tags:
                tags[tag] = tags.get(tag, 0) + 1
        ordered_tags = dict(sorted(tags.items(), key=lambda item: (-item[1], item[0])))
        return {
            "total": len(items),
            "layers": layers,
            "categories": categories,
            "tags": ordered_tags,
        }

    def list_entries(
        self,
        *,
        layer: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        limit: int = 200,
    ) -> dict:
        items = [
            entry
            for entry in self.entries()
            if (not layer or entry.layer == layer)
            and (not category or entry.category == category)
            and (not tag or tag in entry.tags)
        ]
        items.sort(key=lambda entry: entry.updated, reverse=True)
        picked = items[:limit]
        return {"count": len(picked), "items": [entry.model_dump() for entry in picked]}

    def search(
        self,
        *,
        q: str,
        layer: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        limit: int = 50,
    ) -> dict:
        needles = [part.lower() for part in q.split() if part.strip()]
        listed = self.list_entries(layer=layer, category=category, tag=tag, limit=10_000)
        matched = []
        for item in listed["items"]:
            haystack = " ".join(
                [
                    item["title"],
                    item["summary"],
                    " ".join(item["tags"]),
                    " ".join(item["points"]),
                    " ".join(item["misconceptions"]),
                ]
            ).lower()
            if all(needle in haystack for needle in needles):
                matched.append(item)
        picked = matched[:limit]
        return {"count": len(picked), "items": picked, "query": q}

    def get(self, entry_id: str) -> dict:
        for entry in self.entries():
            if entry.id == entry_id:
                return entry.model_dump()
        raise AgenticWorldError(f"没有这条知识：{entry_id}")


INDEX = KnowledgeIndex()
