"""
Blueprint Schema — Pydantic models for Sideload Blueprint YAML validation.

These models define the data contracts for the declarative YAML files
that describe LangGraph topologies. The compiler reads YAML, validates
it against these schemas, and dynamically builds a StateGraph in RAM.
"""

from pydantic import BaseModel, Field


class NodeDef(BaseModel):
    name: str
    handler: str  # dotted Python path, e.g. "engine.graph.supervisor_node"


class EdgeDef(BaseModel):
    source: str
    target: str  # use "__end__" for LangGraph's terminal node


class ConditionalEdgeDef(BaseModel):
    source: str
    router: str  # dotted Python path to the router function
    path_map: dict[str, str]  # decision_value -> node_name (or "__end__")


class BlueprintDef(BaseModel):
    name: str
    entry_point: str
    interrupt_before: list[str] = Field(default_factory=list)
    nodes: list[NodeDef] = Field(default_factory=list)
    edges: list[EdgeDef] = Field(default_factory=list)
    conditional_edges: list[ConditionalEdgeDef] = Field(default_factory=list)
