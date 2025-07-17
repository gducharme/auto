"""Quick experiment for the dspy LLM wrapper."""

import dspy


def main() -> None:
    """Run a simple dspy prompt."""
    lm = dspy.LM("ollama_chat/llama3.2:1b", api_base="http://localhost:11434", api_key="")
    dspy.configure(lm=lm)

    print(lm("Say this is a test!", temperature=0.7))
    print(
        lm(messages=[{"role": "user", "content": "Say this is a test!"}])
    )


if __name__ == "__main__":
    main()
