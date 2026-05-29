import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import briefs, health, missions, schedules

log = logging.getLogger(__name__)

app = FastAPI(
    title="War Room AI API",
    description="Autonomous market intelligence — 5-agent LangGraph engine powered by Bright Data",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8288"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(missions.router, prefix="/missions")
app.include_router(schedules.router)
app.include_router(briefs.router)

# Inngest serve endpoint — handles webhook delivery from Inngest cloud/dev server.
# Dev: npx inngest-cli@latest dev -u http://localhost:8000/api/inngest
try:
    import inngest.fast_api
    from app.inngest_client import FUNCTIONS, client as inngest_client
    inngest.fast_api.serve(app, inngest_client, FUNCTIONS)
    log.warning("Inngest: endpoint mounted at /api/inngest (%d functions)", len(FUNCTIONS))
except Exception as exc:
    log.warning("Inngest: endpoint NOT mounted — %s: %s", type(exc).__name__, exc)
