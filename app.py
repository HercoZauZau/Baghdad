import ollama

from database import (
    criar_base_dados,
    guardar_mensagem,
    carregar_historico,
    guardar_ou_actualizar_memoria,
    procurar_memorias
)


MODEL = "gemma3:4b"


def extrair_memoria(texto):
    prompt = f"""
Analisa a mensagem do utilizador.

Decide se contém uma informação que possa ser útil
recordar numa conversa futura.

As categorias possíveis são:

preferencia
facto
objectivo
projecto
outro

Se não houver nada relevante para memorizar,
responde exactamente:

NAO_MEMORIZAR

Se houver, responde exactamente neste formato:

CATEGORIA|MEMORIA

Exemplo:

preferencia|O utilizador prefere Toyota Land Cruiser.

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


def preparar_memorias(pergunta):
    memorias_relevantes = procurar_memorias(
        pergunta,
        limite=5
    )

    if not memorias_relevantes:
        return "Nenhuma memória relevante encontrada."

    return "\n".join(
        f"- [{memoria['categoria']}] {memoria['content']}"
        for memoria in memorias_relevantes
    )


def processar_memoria(pergunta):
    resultado = extrair_memoria(pergunta)

    if resultado == "NAO_MEMORIZAR":
        return

    try:
        categoria, memoria = resultado.split(
            "|",
            1
        )

        categoria = categoria.strip()
        memoria = memoria.strip()

        if not memoria:
            return

        guardar_ou_actualizar_memoria(
            memoria,
            categoria
        )

    except ValueError:
        pass


def main():
    criar_base_dados()

    messages = [
        {
            "role": "system",
            "content": (
                "Seu nome é Baghdad. "
                "És um assistente pessoal. "
                "Conversa de forma natural e amigável. "
                "Responde de forma clara e relativamente curta. "
                "Quando receberes memórias sobre o utilizador, "
                "usa-as apenas quando forem relevantes para a conversa. "
                "Não inventes informações que não estejam no contexto "
                "ou nas memórias fornecidas."
            )
        }
    ]

    # Recupera o histórico persistente
    messages.extend(
        carregar_historico()
    )

    print("Assistente iniciado.")
    print("Escreve 'sair' para terminar.\n")

    while True:
        pergunta = input("Tu: ").strip()

        if not pergunta:
            continue

        if pergunta.lower() in [
            "sair",
            "exit",
            "quit"
        ]:
            print("\nAssistente terminado.")
            break

        # ---------------------------------
        # 1. Procurar memórias relevantes
        # ---------------------------------

        texto_memorias = preparar_memorias(
            pergunta
        )

        # ---------------------------------
        # 2. Criar mensagem para o modelo
        # ---------------------------------

        mensagem_para_modelo = f"""
Memórias potencialmente relevantes sobre o utilizador:

{texto_memorias}

Mensagem actual do utilizador:

{pergunta}
"""

        messages.append(
            {
                "role": "user",
                "content": mensagem_para_modelo
            }
        )

        # ---------------------------------
        # 3. Guardar mensagem real
        # ---------------------------------

        guardar_mensagem(
            "user",
            pergunta
        )

        # ---------------------------------
        # 4. Enviar conversa para Gemma
        # ---------------------------------

        try:
            response = ollama.chat(
                model=MODEL,
                messages=messages
            )

            resposta = response[
                "message"
            ][
                "content"
            ].strip()

        except Exception as erro:
            print(
                "\nErro ao comunicar com Ollama:",
                erro,
                "\n"
            )

            # Remove a mensagem adicionada ao contexto,
            # porque não houve resposta válida.
            messages.pop()

            continue

        # ---------------------------------
        # 5. Guardar resposta no contexto
        # ---------------------------------

        messages.append(
            {
                "role": "assistant",
                "content": resposta
            }
        )

        guardar_mensagem(
            "assistant",
            resposta
        )

        # ---------------------------------
        # 6. Verificar se há algo a memorizar
        # ---------------------------------

        try:
            processar_memoria(
                pergunta
            )

        except Exception as erro:
            # Uma falha na memória não deve
            # interromper a conversa.
            print(
                f"[Aviso: memória não processada: {erro}]"
            )

        # ---------------------------------
        # 7. Mostrar resposta
        # ---------------------------------

        print(
            "\nAssistente:",
            resposta,
            "\n"
        )


if __name__ == "__main__":
    main()
