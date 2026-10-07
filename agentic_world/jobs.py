from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timezone
from uuid import uuid4

from agentic_world.guards import charter_hash, charter_text
from agentic_world.paths import jobs_dir
from agentic_world.registry import context_for, load_registry, render_role
from agentic_world.util import AgenticWorldError, check_slug, read_json, read_marked, write_json


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def llm_mode() -> str:
    if os.environ.get("OPENAI_API_KEY"):
        return "openai_compatible"
    return "agentic_world_template"


def _job_path(job_id: str):
    check_slug(job_id, "任务 id")
    return jobs_dir() / f"{job_id}.json"


def load_job(job_id: str) -> dict:
    path = _job_path(job_id)
    if not path.is_file():
        raise AgenticWorldError(f"没有这个任务：{job_id}")
    return read_json(path, {})


def list_jobs() -> dict:
    items = []
    for path in sorted(jobs_dir().glob("*.json")):
        job = read_json(path, {})
        items.append({key: value for key, value in job.items() if key != "packet_md"})
    items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return {"count": len(items), "items": items}


def build_packet(domain: str, role: str, intent: str) -> str:
    registry = load_registry()
    if role not in registry.roles:
        raise AgenticWorldError(f"未知角色：{role}")
    work = context_for(registry, domain)
    role_text = render_role(role, work)
    return (
        f"{charter_text()}\n\n"
        f"# 任务\n\n"
        f"- 领域：{work.name}（{work.domain_id}）\n"
        f"- 类型：{work.kind}\n"
        f"- 角色：{role}\n\n"
        f"## 提问\n\n"
        f"{intent.strip()}\n\n"
        f"# 角色说明\n\n"
        f"{role_text}\n"
    )


def create_job(domain: str, role: str, intent: str, requires_gate: bool = True) -> dict:
    if not intent.strip():
        raise AgenticWorldError("提问是空的")
    packet = build_packet(domain, role, intent)
    job = {
        "id": f"j_{uuid4().hex[:8]}",
        "domain": domain,
        "role": role,
        "intent": intent.strip(),
        "requires_gate": requires_gate,
        "status": "draft",
        "principles_sha256": charter_hash(),
        "packet_md": packet,
        "review": "",
        "draft": "",
        "artifact": "",
        "created_at": now(),
    }
    write_json(_job_path(job["id"]), job)
    return job


def attach_review(job_id: str, review: str) -> dict:
    text = read_marked(review) if review.startswith("@") else review.strip()
    if not text:
        raise AgenticWorldError("外部输入是空的，正式讨论还不能开始")
    job = load_job(job_id)
    job["review"] = text
    job["status"] = "gated"
    job["gated_at"] = now()
    write_json(_job_path(job_id), job)
    return job


def accept_job(job_id: str, artifact: str) -> dict:
    text = read_marked(artifact) if artifact.startswith("@") else artifact.strip()
    if not text:
        raise AgenticWorldError("接受任务时要写下这次的结论")
    job = load_job(job_id)
    if job["requires_gate"] and not str(job.get("review", "")).strip():
        raise AgenticWorldError("还没有外部强模型的输入，不能写下正式结论")
    job["artifact"] = text
    job["status"] = "accepted"
    job["accepted_at"] = now()
    write_json(_job_path(job_id), job)
    return job


def complete(prompt: str) -> str:
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise AgenticWorldError("没有 OPENAI_API_KEY。把任务包交给外部平台后，用 job gate 贴回。")
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    body = json.dumps(
        {"model": model, "messages": [{"role": "user", "content": prompt}]},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base}/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise AgenticWorldError(f"模型调用失败：{exc}") from exc
    try:
        return str(payload["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise AgenticWorldError("模型返回里没有正文") from exc


def draft_job(job_id: str) -> dict:
    job = load_job(job_id)
    job["draft"] = complete(job["packet_md"])
    job["drafted_at"] = now()
    write_json(_job_path(job_id), job)
    return job
