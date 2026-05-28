"""LangGraph mission graph: planner → researcher → skeptic → verifier → commander."""

from langgraph.graph import END, START, StateGraph

from app.agents.commander import run_commander
from app.agents.planner import run_planner
from app.agents.researcher import run_researcher
from app.agents.skeptic import run_skeptic
from app.agents.state import MissionState
from app.agents.verifier import run_verifier


def build_graph():
    g = StateGraph(MissionState)
    g.add_node("planner", run_planner)
    g.add_node("researcher", run_researcher)
    g.add_node("skeptic", run_skeptic)
    g.add_node("verifier", run_verifier)
    g.add_node("commander", run_commander)
    g.add_edge(START, "planner")
    g.add_edge("planner", "researcher")
    g.add_edge("researcher", "skeptic")
    g.add_edge("skeptic", "verifier")
    g.add_edge("verifier", "commander")
    g.add_edge("commander", END)
    return g.compile()


# Module-level compiled graph — import this in routes/missions.py
mission_graph = build_graph()
