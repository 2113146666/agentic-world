from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

SLUG = re.compile(r"^[a-z][a-z0-9_-]{0,80}$")


class AgenticWorldError(Exception):
    pass


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def check_slug(value: str, label: str) -> str:
    if not SLUG.match(value):
        raise AgenticWorldError(f"{label} 只能用小写字母、数字、连字符：{value}")
    return value


def read_marked(value: str) -> str:
    """CLI 里以 @ 开头的参数表示从文件读取。"""
    if value.startswith("@"):
        path = Path(value[1:])
        if not path.is_file():
            raise AgenticWorldError(f"找不到文件：{path}")
        return read_text(path).strip()
    return value.strip()
