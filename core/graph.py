from langgraph.graph import StateGraph, START, END
from core.state import MicrogridState
from agents.forecaster import forecaster_node
from agents.demand_manager import demand_manager_node
from agents.storage_strategist import storage_strategist_node
from agents.grid_broker import grid_broker_node


def build_graph():
    graph = StateGraph(MicrogridState)

    graph.add_node("forecaster", forecaster_node)
    graph.add_node("demand_manager", demand_manager_node)
    graph.add_node("storage_strategist", storage_strategist_node)
    graph.add_node("grid_broker", grid_broker_node)

    # Sequential chain: forecast → demand → storage → broker
    graph.add_edge(START, "forecaster")
    graph.add_edge("forecaster", "demand_manager")
    graph.add_edge("demand_manager", "storage_strategist")
    graph.add_edge("storage_strategist", "grid_broker")
    graph.add_edge("grid_broker", END)

    return graph.compile()


microgrid_graph = build_graph()
