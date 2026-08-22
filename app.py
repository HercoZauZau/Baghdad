import ollama

from database import (
    criar_base_dados,
    guardar_mensagem,
    carregar_historico
)


criar_base_dados()

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

messages.extend(carregar_historico())


while True:
    pergunta = input("Tu: ")

    if pergunta.lower() in ["sair", "exit", "quit"]:
        break

    mensagem_utilizador = {
        "role": "user",
        "content": pergunta
    }

    messages.append(mensagem_utilizador)

    guardar_mensagem("user", pergunta)

    response = ollama.chat(
        model="gemma3:4b",
        messages=messages
    )

    resposta = response["message"]["content"]

    mensagem_assistente = {
        "role": "assistant",
        "content": resposta
    }

    messages.append(mensagem_assistente)

    guardar_mensagem("assistant", resposta)

    print("\nAssistente:", resposta, "\n")
