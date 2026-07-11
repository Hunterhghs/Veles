"""Use Fable's memory store directly (no LLM required).

The same store is read and written by the orchestrator and by external
agents connected through the MCP server, so anything you save here is
available to all of them.
"""

from fable_agent.memory import create_memory


def main() -> None:
    memory = create_memory("sqlite", ".fable/memory")

    memory.remember(
        "This repo deploys via GitHub Actions; the workflow lives in .github/workflows/ci.yml",
        category="project-fact",
        tags=["ci", "deploy"],
    )
    memory.remember("Decided to keep the public API synchronous for v1", category="decision")

    print("Recent memories:")
    for entry in memory.recent(limit=10):
        print(f"  [{entry.category}] {entry.content}")

    print("\nSearch for 'deploy':")
    for entry in memory.search("deploy"):
        print(f"  {entry.content}")


if __name__ == "__main__":
    main()
