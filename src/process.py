import sys

from src import db
from src.agent import agent


def process_files(paths):
    db.init_db()
    for path in paths:
        print(f"\n=== {path}")
        state = agent.invoke({"path": path})
        print(f"#{state['invoice_id']} {state['status'].upper()}")
        if state.get("reason"):
            print(f"   {state['reason']}")
        for r in state.get("results", []):
            if not r.passed:
                print(f"   FAIL {r.name}: {r.message}")


if __name__ == "__main__":
    process_files(sys.argv[1:])