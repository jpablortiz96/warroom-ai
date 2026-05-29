from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import briefs, health, missions, schedules

app = FastAPI(
    title="War Room AI API",
    description="Autonomous market intelligence — 5-agent LangGraph engine powered by Bright Data",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
except Exception:
    pass  # Inngest optional — app works without it
