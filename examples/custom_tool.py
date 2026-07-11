"""Register a custom tool and use it in an agent.

Shows the extension point: subclass Tool, give it a JSON schema, and add
it to a registry. Works the same for the MCP server.
"""

from fable_agent.llm.base import LLMResponse, ToolCall
from fable_agent.tools import default_registry
from fable_agent.tools.base import Tool, ToolResult


class WordCountTool(Tool):
    name = "word_count"
    description = "Count the words in a piece of text."
    parameters = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "The text to count words in."},
        },
        "required": ["text"],
    }

    def execute(self, text: str) -> ToolResult:
        return ToolResult(output=f"{len(text.split())} words")


def main() -> None:
    registry = default_registry(".")
    registry.register(WordCountTool())

    result = registry.execute("word_count", {"text": "the quick brown fox"})
    print(result.output)  # -> 4 words

    # The registry produces provider-agnostic specs for the LLM:
    for spec in registry.specs():
        print(f"- {spec.name}")


if __name__ == "__main__":
    main()
