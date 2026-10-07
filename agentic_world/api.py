from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agentic_world import __version__
from agentic_world.guards import decide_sensitivity, new_sensitivity_card
from agentic_world.jobs import accept_job, attach_review, create_job, list_jobs, llm_mode, load_job
from agentic_world.knowledge import INDEX
from agentic_world.paths import ROOT
from agentic_world.pipeline import (
    inspire_add,
    inspire_export,
    inspire_list,
    inspire_seed,
    latest_named,
    quant_advise,
    select_choice,
    transform_run,
    world_build,
    world_list,
)
from agentic_world.registry import load_registry
from agentic_world.util import AgenticWorldError

app = FastAPI(title="Agentic World", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AgenticWorldError)
async def handle_error(_, exc: AgenticWorldError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


class InspireIn(BaseModel):
    raw: str
    tags: list[str] = Field(default_factory=list)


class ExportIn(BaseModel):
    title: str = "web-batch"
    theme: str | None = None


class WorldIn(BaseModel):
    name: str | None = None


class SelectIn(BaseModel):
    choice_id: str
    card_name: str = ""
    card_want: str = ""
    note: str = ""


class TransformIn(BaseModel):
    include_comic: bool = True
    include_game: bool = True


class JobIn(BaseModel):
    domain: str
    role: str
    intent: str
    requires_gate: bool = True


class ReviewIn(BaseModel):
    review: str


class AcceptIn(BaseModel):
    artifact: str


class TopicIn(BaseModel):
    topic: str


class DecideIn(BaseModel):
    touches_real_politics: bool | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/status")
def status():
    registry = load_registry()
    return {
        "root": str(ROOT),
        "llm_mode": llm_mode(),
        "knowledge_entries": len(INDEX.entries()),
        "verticals": len(registry.verticals),
    }


@app.get("/api/registry")
def registry_view():
    registry = load_registry()
    return {
        "motto": registry.motto,
        "roles": registry.roles,
        "tracks": [track.model_dump() for track in registry.tracks],
        "verticals": [vertical.model_dump() for vertical in registry.verticals],
    }


@app.get("/api/knowledge/meta")
def knowledge_meta():
    return INDEX.meta()


@app.get("/api/knowledge/list")
def knowledge_list(layer: str | None = None, category: str | None = None, tag: str | None = None, limit: int = 200):
    return INDEX.list_entries(layer=layer, category=category, tag=tag, limit=limit)


@app.get("/api/knowledge/search")
def knowledge_search(
    q: str,
    layer: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    limit: int = 50,
):
    return INDEX.search(q=q, layer=layer, category=category, tag=tag, limit=limit)


@app.get("/api/knowledge/get/{entry_id}")
def knowledge_get(entry_id: str):
    return INDEX.get(entry_id)


@app.post("/api/knowledge/ingest")
def knowledge_ingest():
    count = INDEX.reload()
    return {"count": count}


@app.post("/api/inspire/add")
def api_inspire_add(body: InspireIn):
    return inspire_add(body.raw, body.tags)


@app.post("/api/inspire/seed")
def api_inspire_seed():
    return inspire_seed()


@app.get("/api/inspire/list")
def api_inspire_list():
    return inspire_list()


@app.post("/api/inspire/export")
def api_inspire_export(body: ExportIn):
    return inspire_export(body.title, body.theme)


@app.post("/api/world/build")
def api_world_build(body: WorldIn):
    return world_build(body.name)


@app.get("/api/world/latest")
def api_world_latest():
    return latest_named("worlds.json", "世界观。先构建。")


@app.get("/api/world/list")
def api_world_list():
    return world_list()


@app.post("/api/select/choose")
def api_select(body: SelectIn):
    return select_choice(body.choice_id, body.card_name, body.card_want, body.note)


@app.get("/api/select/latest")
def api_select_latest():
    return latest_named("selections.json", "选择。先选定一条支线。")


@app.post("/api/transform/run")
def api_transform(body: TransformIn):
    return transform_run(body.include_comic, body.include_game)


@app.get("/api/transform/latest")
def api_transform_latest():
    return latest_named("bundles.json", "转化结果。先运行转化。")


@app.post("/api/quant/advise")
def api_quant():
    return quant_advise()


@app.get("/api/quant/latest")
def api_quant_latest():
    return latest_named("reports.json", "量化报告。先生成建议。")


@app.post("/api/jobs")
def api_job_create(body: JobIn):
    return create_job(body.domain, body.role, body.intent, body.requires_gate)


@app.get("/api/jobs")
def api_job_list():
    return list_jobs()


@app.get("/api/jobs/{job_id}")
def api_job_get(job_id: str):
    return load_job(job_id)


@app.post("/api/jobs/{job_id}/gate")
def api_job_gate(job_id: str, body: ReviewIn):
    return attach_review(job_id, body.review)


@app.post("/api/jobs/{job_id}/accept")
def api_job_accept(job_id: str, body: AcceptIn):
    return accept_job(job_id, body.artifact)


@app.post("/api/hotspot/card")
def api_hotspot_card(body: TopicIn):
    if not body.topic.strip():
        raise AgenticWorldError("热点题目是空的")
    return new_sensitivity_card(body.topic)


@app.post("/api/hotspot/decide")
def api_hotspot_decide(body: DecideIn):
    decision = decide_sensitivity(body.touches_real_politics)
    return {
        "touches_real_politics": body.touches_real_politics,
        "decision": decision,
        "publish": decision == "public",
    }
