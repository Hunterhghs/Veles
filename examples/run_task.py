"""Run the full Fable pipeline on a task, with live progress output.

Usage:
    export ANTHROPIC_API_KEY=...   # or OPENAI_API_KEY / FABLE_API_KEY
    python examples/run_task.py "Create a small FastAPI app with a /health endpoint"
"""

import sys

from fable_agent import FableConfig, Orchestrator


def on_event(agent: str, event: str, detail: str) -> None:
    print(f"  [{agent}] {event}: {detail[:100]}")


def main() -> None:
    task = sys.argv[1] if len(sys.argv) > 1 else "Create hello.py that prints 'Hello from Fable'"

    config = FableConfig.load(workspace=".")
    orchestrator = Orchestrator(config=config, on_event=on_event)

    result = orchestrator.run_task(task)
    print("\n=== Final report ===")
    print(result.output)


if __name__ == "__main__":
    main()
