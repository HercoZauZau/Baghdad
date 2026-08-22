import ollama

messages = [
    {
        "role": "system",
        "content": (
            "És um assistente pessoal. "
            "Seu nome é Baghdad. "
            "Conversa de maneira natural e amigável. "
            "Responde de forma clara e relativamente curta."
        )
    }
]

while True:
    pergunta = input("Tu: ")

    if pergunta.lower() in ["sair", "exit", "quit"]:
        break

    messages.append({
        "role": "user",
        "content": pergunta
    })

    response = ollama.chat(
        model="gemma3:4b",
        messages=messages
    )

    resposta = response["message"]["content"]

    messages.append({
        "role": "assistant",
        "content": resposta
    })

    print("\nAssistente:", resposta, "\n")
