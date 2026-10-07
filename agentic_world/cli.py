from __future__ import annotations

import argparse
import json
import sys

from agentic_world.jobs import accept_job, attach_review, create_job, draft_job, list_jobs, load_job
from agentic_world.knowledge import INDEX
from agentic_world.registry import load_registry
from agentic_world.scaffold import accept_proposal, create_vertical, list_proposals, propose
from agentic_world.util import AgenticWorldError


def _print(result) -> None:
    if result is None:
        return
    if isinstance(result, str):
        print(result)
        return
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_serve(args) -> None:
    import uvicorn

    uvicorn.run("agentic_world.api:app", host=args.host, port=args.port)


def cmd_registry(_args) -> str:
    registry = load_registry()
    lines = [registry.motto, "", "基础赛道"]
    for track in registry.tracks:
        lines.append(f"- {track.name}（{track.scope}）")
    lines.append("")
    lines.append("垂类（每个都有产品、技术、测试、运营）")
    for vertical in registry.verticals:
        lines.append(f"- {vertical.name}")
        lines.append(f"  {vertical.focus}")
    return "\n".join(lines)


def cmd_knowledge(_args) -> dict:
    count = INDEX.reload()
    meta = INDEX.meta()
    meta["reloaded"] = count
    return meta


def cmd_job_new(args) -> dict:
    return create_job(args.domain, args.role, args.intent, requires_gate=not args.no_gate)


def cmd_job_list(_args) -> dict:
    return list_jobs()


def cmd_job_show(args):
    job = load_job(args.job_id)
    if args.packet:
        return job["packet_md"]
    shown = {key: value for key, value in job.items() if key != "packet_md"}
    shown["packet_chars"] = len(job["packet_md"])
    return shown


def cmd_job_gate(args) -> dict:
    return attach_review(args.job_id, args.review)


def cmd_job_accept(args) -> dict:
    return accept_job(args.job_id, args.artifact)


def cmd_job_draft(args) -> dict:
    return draft_job(args.job_id)


def cmd_vertical_list(_args) -> str:
    return cmd_registry(_args)


def cmd_vertical_new(args) -> dict:
    return create_vertical(args.id, args.name, args.focus, args.category)


def cmd_evolve_propose(args) -> dict:
    return propose(args.target, args.reason, args.change, args.role)


def cmd_evolve_list(_args) -> dict:
    return list_proposals()


def cmd_evolve_accept(args) -> dict:
    return accept_proposal(args.proposal_id)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m agentic_world", description="工作室底层：原则、门禁、知识、垂类四角色")
    sub = parser.add_subparsers(dest="cmd", required=True)

    serve = sub.add_parser("serve", help="启动给现有前端用的 API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.set_defaults(func=cmd_serve)

    registry = sub.add_parser("registry", help="打印分工")
    registry.set_defaults(func=cmd_registry)

    knowledge = sub.add_parser("knowledge", help="重新读取知识文件")
    knowledge.set_defaults(func=cmd_knowledge)

    job = sub.add_parser("job", help="任务包")
    job_sub = job.add_subparsers(dest="job_cmd", required=True)
    created = job_sub.add_parser("new")
    created.add_argument("--domain", required=True, help="赛道或垂类 id，如 novel、platform")
    created.add_argument("--role", required=True, help="product、tech、test、ops")
    created.add_argument("--intent", required=True)
    created.add_argument("--no-gate", action="store_true", help="运维杂务可跳过外部输入")
    created.set_defaults(func=cmd_job_new)
    job_sub.add_parser("list").set_defaults(func=cmd_job_list)
    show = job_sub.add_parser("show")
    show.add_argument("job_id")
    show.add_argument("--packet", action="store_true", help="只打印要贴给外部模型的任务包")
    show.set_defaults(func=cmd_job_show)
    gate = job_sub.add_parser("gate")
    gate.add_argument("job_id")
    gate.add_argument("--review", required=True, help="外部模型返回的文本，或 @文件路径")
    gate.set_defaults(func=cmd_job_gate)
    accept = job_sub.add_parser("accept")
    accept.add_argument("job_id")
    accept.add_argument("--artifact", required=True, help="本次结论，或 @文件路径")
    accept.set_defaults(func=cmd_job_accept)
    draft = job_sub.add_parser("draft", help="有 OPENAI_API_KEY 时，让模型先写一版，仍不自动接受")
    draft.add_argument("job_id")
    draft.set_defaults(func=cmd_job_draft)

    vertical = sub.add_parser("vertical", help="垂类")
    vertical_sub = vertical.add_subparsers(dest="vertical_cmd", required=True)
    vertical_sub.add_parser("list").set_defaults(func=cmd_vertical_list)
    created_vertical = vertical_sub.add_parser("new")
    created_vertical.add_argument("--id", required=True)
    created_vertical.add_argument("--name", required=True)
    created_vertical.add_argument("--category", required=True)
    created_vertical.add_argument("--focus", required=True)
    created_vertical.set_defaults(func=cmd_vertical_new)

    evolve = sub.add_parser("evolve", help="自进化提案。接受不会自动改文件。")
    evolve_sub = evolve.add_subparsers(dest="evolve_cmd", required=True)
    proposed = evolve_sub.add_parser("propose")
    proposed.add_argument("--target", required=True)
    proposed.add_argument("--reason", required=True)
    proposed.add_argument("--change", required=True)
    proposed.add_argument("--role", default="ops")
    proposed.set_defaults(func=cmd_evolve_propose)
    evolve_sub.add_parser("list").set_defaults(func=cmd_evolve_list)
    accepted = evolve_sub.add_parser("accept")
    accepted.add_argument("proposal_id")
    accepted.set_defaults(func=cmd_evolve_accept)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        _print(args.func(args))
    except AgenticWorldError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0
