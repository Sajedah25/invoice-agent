from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from src import db
from src.extract import extract_invoice
from src.llm import LLMUnavailable
from src.qr import read_qr
from src.read_invoice import read_invoice
from src.validate import decide, validate_invoice


class InvoiceState(TypedDict, total=False):
    path: str
    method: str
    text: str
    invoice: Any
    qr: dict | None
    results: list
    status: str
    reason: str
    invoice_id: int


def read_node(state):
    result = read_invoice(state["path"])
    return {"text": result["text"], "method": result["method"]}


def extract_node(state):
    try:
        return {"invoice": extract_invoice(state["text"])}
    except LLMUnavailable:
        return {"status": "pending", "reason": "AI unavailable, retry later"}
    except ValidationError as e:
        return {"status": "needs_review", "reason": f"{e.error_count()} field error(s)"}


def route_after_extract(state):
    return "save_unread" if state.get("status") else "read_qr"


def read_qr_node(state):
    return {"qr": read_qr(state["path"])}


def validate_node(state):
    inv = state["invoice"]
    exists = db.is_duplicate(inv.supplier_vat_number, inv.invoice_number)
    results = validate_invoice(inv, state["qr"], exists)
    return {"results": results, "status": decide(results)}


def save_node(state):
    invoice_id = db.save_invoice(
        state["invoice"], state["path"], state["method"], state["status"], state["results"]
    )
    return {"invoice_id": invoice_id}


def save_unread_node(state):
    invoice_id = db.save_unread(state["path"], state["method"], state["status"], state["reason"])
    return {"invoice_id": invoice_id}


def build_agent():
    graph = StateGraph(InvoiceState)

    graph.add_node("read", read_node)
    graph.add_node("extract", extract_node)
    graph.add_node("read_qr", read_qr_node)
    graph.add_node("validate", validate_node)
    graph.add_node("save", save_node)
    graph.add_node("save_unread", save_unread_node)

    graph.add_edge(START, "read")
    graph.add_edge("read", "extract")
    graph.add_conditional_edges(
        "extract", route_after_extract, {"read_qr": "read_qr", "save_unread": "save_unread"}
    )
    graph.add_edge("read_qr", "validate")
    graph.add_edge("validate", "save")
    graph.add_edge("save", END)
    graph.add_edge("save_unread", END)

    return graph.compile()


agent = build_agent()

if __name__ == "__main__":
    print(agent.get_graph().draw_mermaid())