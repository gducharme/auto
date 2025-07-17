"""Quick experiment for the dspy LLM wrapper."""

import dspy


def main() -> None:
    """Run a simple dspy prompt."""
    lm = dspy.LM("ollama_chat/gemma3:4b", api_base="http://localhost:11434", api_key="")
    dspy.configure(lm=lm)

    task = """
    The task is to create a prompt for an AI agent.

    The main task is to act as an observer.
    If there are no pending tasks in the existing TODO.md file, then new objective is to examine the entire project and populate the TODO sections with new priorities. Do not add new sections, instead reuse the empty sections.

    If there are pending tasks, then there is nothing for you to do as an observer


    """
    print(lm(messages=[{"role": "user", "content": task}]))


if __name__ == "__main__":
    main()
