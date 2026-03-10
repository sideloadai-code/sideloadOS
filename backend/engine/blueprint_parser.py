"""
Blueprint Parser — Dynamic LangGraph compiler from YAML definitions.

Reads a Sideload Blueprint YAML file, validates it against the Pydantic
schema, dynamically imports handler functions via importlib, and assembles
a compiled LangGraph StateGraph at runtime.

This is the engine that separates Platform (SideloadOS) from Logic
(The Blueprints). Drop a new YAML file into /app/blueprints and the OS
instantly learns a new workflow — no code changes, no server restarts.
"""

import functools
import importlib

import yaml
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from engine.blueprint_schema import BlueprintDef
from engine.state import SideloadState


@functools.lru_cache(maxsize=128)
def _load_handler(handler_path: str):
    """Dynamically import and return a Python function from a dotted path.

    Example: "engine.graph.supervisor_node" →
             importlib.import_module("engine.graph").supervisor_node

    Cached via @lru_cache so each handler is imported exactly once into
    memory, keeping the orchestrator blazingly fast while the YAML itself
    is read fresh on every request.
    """
    if "." not in handler_path:
        raise ValueError(
            f"Blueprint Logic Error: Handler path '{handler_path}' is invalid. "
            f"Expected a dotted Python path like 'engine.graph.supervisor_node'."
        )

    module_path, attr_name = handler_path.rsplit(".", 1)

    try:
        module = importlib.import_module(module_path)
        return getattr(module, attr_name)
    except Exception as e:
        raise ValueError(
            f"Blueprint Logic Error: Could not load handler '{handler_path}'. "
            f"Details: {str(e)}"
        )


def compile_blueprint(yaml_path: str, checkpointer) -> CompiledStateGraph:
    """Read a YAML blueprint and compile it into a live LangGraph.

    Args:
        yaml_path: Absolute path to the blueprint YAML file.
        checkpointer: LangGraph checkpointer instance for state persistence.

    Returns:
        A compiled StateGraph ready for .ainvoke() or .astream_events().
    """
    # 1. Read and validate the YAML
    with open(yaml_path, "r") as f:
        yaml_data = yaml.safe_load(f)

    blueprint = BlueprintDef.model_validate(yaml_data)

    # 2. Initialize the graph
    graph = StateGraph(SideloadState)

    # 3. Register all nodes via dynamic import
    for node in blueprint.nodes:
        func = _load_handler(node.handler)
        graph.add_node(node.name, func)

    # 4. Set entry point
    graph.add_edge(START, blueprint.entry_point)

    # 5. Add standard edges (__end__ → physical END sentinel)
    for edge in blueprint.edges:
        target = END if edge.target == "__end__" else edge.target
        graph.add_edge(edge.source, target)

    # 6. Add conditional edges with resolved path maps
    for edge in blueprint.conditional_edges:
        router_func = _load_handler(edge.router)
        resolved_path_map = {
            k: (END if v == "__end__" else v)
            for k, v in edge.path_map.items()
        }
        graph.add_conditional_edges(edge.source, router_func, resolved_path_map)

    # 7. Compile with checkpointer and HITL interrupts
    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=blueprint.interrupt_before,
    )
