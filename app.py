import ollama

from database import (
    criar_base_dados,
    guardar_mensagem,
    carregar_historico,
    guardar_memoria,
    procurar_memorias
)


MODEL = "gemma3:4b"


def extrair_memoria(texto):
    prompt = f"""
Analisa a mensagem abaixo.

Se contiver uma informação pessoal, preferência,
objectivo ou facto sobre o utilizador que possa ser
útil recordar em conversas futuras, devolve apenas
esse facto de forma curta.

Se não houver nada importante para memorizar,
responde exactamente:

NAO_MEMORIZAR

Mensagem:
{texto}
"""

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"].strip()


criar_base_dados()


messages = [
    {
        "role": "system",
        "content": (
            "És um assistente pessoal. "
            "Seu nome é Baghdad. "
            "Conversa de maneira natural e amigável. "
            "Responde de forma clara e relativamente curta. "
            "Podes receber memórias relevantes sobre o utilizador "
            "juntamente com algumas mensagens."
        )
    }
]


messages.extend(carregar_historico())


while True:
    pergunta = input("Tu: ")

    if pergunta.lower() in ["sair", "exit", "quit"]:
        break

    # --------------------------------
    # Procurar memórias relevantes
    # --------------------------------

    memorias_relevantes = procurar_memorias(
        pergunta,
        limite=5
    )

    if memorias_relevantes:
        texto_memorias = "\n".join(
            f"- {memoria}"
            for memoria in memorias_relevantes
        )
    else:
        texto_memorias = "Nenhuma memória relevante."


    # --------------------------------
    # Adicionar mensagem ao contexto
    # --------------------------------

    mensagem_para_modelo = f"""
Memórias potencialmente relevantes:

{texto_memorias}

Mensagem do utilizador:

{pergunta}
"""

    messages.append({
        "role": "user",
        "content": mensagem_para_modelo
    })


    # Guardamos no histórico apenas
    # aquilo que o utilizador realmente escreveu.

    guardar_mensagem(
        "user",
        pergunta
    )


    # --------------------------------
    # Gerar resposta
    # --------------------------------

    response = ollama.chat(
        model=MODEL,
        messages=messages
    )

    resposta = response["message"]["content"]

    messages.append({
        "role": "assistant",
        "content": resposta
    })

    guardar_mensagem(
        "assistant",
        resposta
    )


    # --------------------------------
    # Verificar se devemos memorizar
    # --------------------------------

    memoria = extrair_memoria(pergunta)

    if memoria != "NAO_MEMORIZAR":
        guardar_memoria(memoria)


    print(
        "\nAssistente:",
        resposta,
        "\n"
    )
