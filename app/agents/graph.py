from langgraph.graph import StateGraph, END
from app.agents.state import CandidateState
from app.agents.nodes.parser import parser_node
from app.agents.nodes.screener import screener_node
from app.agents.nodes.assessment import assessment_node
from app.agents.nodes.coordinator import coordinator_node

def route_after_screening(state: CandidateState) -> str:
    """
    Conditional router:
    - If match_score >= 65.0 -> Go to Assessment Agent to generate technical questions.
    - If match_score < 65.0  -> Skip assessment and go straight to Coordinator for rejection email.
    """
    if state.get("match_score", 0.0) >= 65.0:
        return "assessment"
    return "coordinator"

def build_recruitment_graph():
    """Compiles the multi-agent state machine."""
    workflow = StateGraph(CandidateState)

    # 1. Register all 4 Agent Nodes
    workflow.add_node("parser", parser_node)
    workflow.add_node("screener", screener_node)
    workflow.add_node("assessment", assessment_node)
    workflow.add_node("coordinator", coordinator_node)

    # 2. Define the Execution Flow
    workflow.set_entry_point("parser")
    workflow.add_edge("parser", "screener")

    # 3. Conditional Branching after Screener Agent
    workflow.add_conditional_edges(
        "screener",
        route_after_screening,
        {
            "assessment": "assessment",
            "coordinator": "coordinator"
        }
    )

    # 4. Assessment connects to Coordinator, and Coordinator finishes the run
    workflow.add_edge("assessment", "coordinator")
    workflow.add_edge("coordinator", END)

    return workflow.compile()

# Singleton compiled graph instance ready to be invoked by FastAPI
recruitment_graph = build_recruitment_graph()