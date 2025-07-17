import dspy

lm = dspy.LM("ollama_chat/llama3.2:1b", api_base="http://localhost:11434", api_key="")
dspy.configure(lm=lm)

lm("Say this is a test!", temperature=0.7)  # => ['This is a test!']
lm(
    messages=[{"role": "user", "content": "Say this is a test!"}]
)  # => ['This is a test!']
