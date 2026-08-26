import ollama

from database import (
    criar_base_dados,
    guardar_mensagem,
    carregar_historico,
    guardar_ou_actualizar_memoria,
    procurar_memorias
)

from speech_to_text import ouvir
from text_to_speech import falar


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


def escolher_modo():
    while True:
        print("\nEscolhe o modo de conversa:")
        print("[E] Escrever")
        print("[F] Falar")
        print("[S] Sair")

        modo = input("> ").strip().lower()

        if modo in ["e", "escrever"]:
            return "texto"

        if modo in ["f", "falar"]:
            return "voz"

        if modo in ["s", "sair", "exit", "quit"]:
            return None

        print("\nOpção inválida.")


def obter_pergunta(modo):
    if modo == "voz":
        pergunta = ouvir()

        if pergunta:
            print(
                "\nTu:",
                pergunta
            )

        return pergunta

    return input("\nTu: ").strip()


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

    messages.extend(
        carregar_historico()
    )

    print("\nBaghdad iniciado.")

    modo = escolher_modo()

    if modo is None:
        print("\nBaghdad terminado.")
        return

    print(
        f"\nModo seleccionado: "
        f"{'voz' if modo == 'voz' else 'texto'}"
    )

    if modo == "texto":
        print("Escreve 'sair' para terminar.")

    while True:
        pergunta = obter_pergunta(modo)

        if not pergunta:
            continue

        # No modo texto podemos sair escrevendo "sair".
        if (
            modo == "texto"
            and pergunta.lower() in [
                "sair",
                "exit",
                "quit"
            ]
        ):
            break

        # No modo voz, também permitimos dizer "sair".
        if (
            modo == "voz"
            and pergunta.lower() in [
                "sair",
                "sair.",
                "terminar",
                "terminar."
            ]
        ):
            break

        # --------------------------------
        # 1. Procurar memórias relevantes
        # --------------------------------

        try:
            texto_memorias = preparar_memorias(
                pergunta
            )

        except Exception as erro:
            print(
                f"[Aviso: erro ao procurar memórias: {erro}]"
            )

            texto_memorias = (
                "Nenhuma memória disponível."
            )

        # --------------------------------
        # 2. Preparar contexto para Gemma
        # --------------------------------

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

        # --------------------------------
        # 3. Guardar mensagem real
        # --------------------------------

        guardar_mensagem(
            "user",
            pergunta
        )

        # --------------------------------
        # 4. Gerar resposta
        # --------------------------------

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
                erro
            )

            messages.pop()

            continue

        # --------------------------------
        # 5. Guardar resposta
        # --------------------------------

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

        # --------------------------------
        # 6. Processar possível memória
        # --------------------------------

        try:
            processar_memoria(
                pergunta
            )

        except Exception as erro:
            print(
                f"[Aviso: memória não processada: {erro}]"
            )

        # --------------------------------
        # 7. Mostrar resposta
        # --------------------------------

        print(
            "\nBaghdad:",
            resposta
        )

        if modo == "voz":
            falar(resposta)

    print("\nBaghdad terminado.")


if __name__ == "__main__":
    main()
