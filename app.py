from contextlib import asynccontextmanager
from pathlib import Path

import asyncio
import base64
import json
import subprocess
import sys
import tempfile
import time

import ollama

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from database import (
    criar_base_dados,
    guardar_mensagem,
    carregar_historico,
    guardar_ou_actualizar_memoria,
    procurar_memorias,
)

from speech_to_text import ouvir


# ============================================================
# CONFIGURAÇÃO
# ============================================================

ROOT = (
    Path(__file__)
    .resolve()
    .parent
)


MODEL = "gemma3:4b"


VOICE_MODEL = (
    ROOT
    / "voices"
    / "dii_pt-PT.onnx"
)


RHUBARB = (
    ROOT
    / "avatar"
    / "tools"
    / "rhubarb"
    / "rhubarb"
)


# Número máximo de mensagens recentes
# enviadas ao Gemma.
MAX_CONTEXT_MESSAGES = 12


SYSTEM_PROMPT = (
    "Seu nome é Baghdad. "
    "És um assistente pessoal. "
    "Conversa de forma natural e amigável. "
    "Responde de forma clara e relativamente curta. "
    "Quando receberes memórias sobre o utilizador, "
    "usa-as apenas quando forem relevantes para a conversa. "
    "Não inventes informações que não estejam no contexto "
    "ou nas memórias fornecidas."
)


# ============================================================
# ESTADO GLOBAL
# ============================================================

messages = []


# Apenas um turno de conversa de cada vez.
conversation_lock = asyncio.Lock()


# Evita processar o mesmo clique/pedido duas vezes.
processed_request_ids = set()


# ============================================================
# UTILITÁRIO DE TEMPO
# ============================================================

def mostrar_tempo(
    nome,
    inicio,
):

    duracao = (
        time.perf_counter()
        - inicio
    )

    print(
        f"[TEMPO] "
        f"{nome:<25} "
        f"{duracao:.2f} s"
    )

    return duracao


# ============================================================
# STARTUP / SHUTDOWN
# ============================================================

@asynccontextmanager
async def lifespan(app):

    criar_base_dados()


    messages.clear()


    messages.append(
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    )


    history = (
        carregar_historico()
    )


    if history:

        # Não carregamos toda a vida
        # da conversa para o contexto activo.

        messages.extend(
            history[
                -MAX_CONTEXT_MESSAGES:
            ]
        )


    print()
    print(
        "=========================================="
    )
    print(
        "Baghdad Backend iniciado"
    )
    print(
        "=========================================="
    )

    print(
        "Modelo:",
        MODEL
    )

    print(
        "Histórico activo:",
        len(messages) - 1,
        "mensagens"
    )

    print(
        "Piper:",
        VOICE_MODEL.exists(),
        VOICE_MODEL
    )

    print(
        "Rhubarb:",
        RHUBARB.exists(),
        RHUBARB
    )

    print(
        "=========================================="
    )
    print()


    yield


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Baghdad",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# STATUS
# ============================================================

@app.get("/")
def status():

    return {
        "status": "ok",

        "model": MODEL,

        "voice":
            VOICE_MODEL.name,

        "voice_exists":
            VOICE_MODEL.exists(),

        "rhubarb_exists":
            RHUBARB.exists(),

        "context_messages":
            len(messages),
    }


# ============================================================
# MEMÓRIAS RELEVANTES
# ============================================================

def preparar_memorias(
    pergunta
):

    inicio = (
        time.perf_counter()
    )


    memorias = (
        procurar_memorias(
            pergunta,
            limite=5,
        )
    )


    mostrar_tempo(
        "Memória / embedding",
        inicio,
    )


    if not memorias:

        return ""


    linhas = []


    for memoria in memorias:

        linhas.append(
            f"- "
            f"[{memoria['categoria']}] "
            f"{memoria['content']}"
        )


    return "\n".join(
        linhas
    )


# ============================================================
# GERAR RESPOSTA COM GEMMA
# ============================================================

def gerar_resposta(
    pergunta
):

    # --------------------------------------------------------
    # MEMÓRIAS
    # --------------------------------------------------------

    memorias = (
        preparar_memorias(
            pergunta
        )
    )


    # --------------------------------------------------------
    # GUARDAR PERGUNTA REAL
    # --------------------------------------------------------

    messages.append(
        {
            "role": "user",
            "content": pergunta,
        }
    )


    guardar_mensagem(
        "user",
        pergunta,
    )


    # --------------------------------------------------------
    # PROMPT ENRIQUECIDO
    # --------------------------------------------------------

    if memorias:

        pergunta_llm = (
            "Memórias relevantes sobre "
            "o utilizador:\n\n"
            f"{memorias}\n\n"
            "Mensagem actual do utilizador:\n\n"
            f"{pergunta}"
        )

    else:

        pergunta_llm = (
            pergunta
        )


    # --------------------------------------------------------
    # CONTEXTO LIMITADO
    # --------------------------------------------------------

    contexto_recente = (
        messages[
            -MAX_CONTEXT_MESSAGES:
        ]
    )


    llm_messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]


    for mensagem in contexto_recente:

        if (
            mensagem.get(
                "role"
            )
            == "system"
        ):
            continue


        llm_messages.append(
            {
                "role":
                    mensagem[
                        "role"
                    ],

                "content":
                    mensagem[
                        "content"
                    ],
            }
        )


    # A última mensagem é a pergunta actual.
    # Substituímos pela versão enriquecida
    # com as memórias relevantes.

    if (
        llm_messages
        and
        llm_messages[-1][
            "role"
        ]
        == "user"
    ):

        llm_messages[-1] = {
            "role": "user",
            "content": pergunta_llm,
        }


    # --------------------------------------------------------
    # GEMMA
    # --------------------------------------------------------

    inicio_gemma = (
        time.perf_counter()
    )


    response = (
        ollama.chat(
            model=MODEL,
            messages=llm_messages,
        )
    )


    mostrar_tempo(
        "Gemma",
        inicio_gemma,
    )


    resposta = (
        response[
            "message"
        ][
            "content"
        ]
        .strip()
    )


    # --------------------------------------------------------
    # GUARDAR RESPOSTA
    # --------------------------------------------------------

    messages.append(
        {
            "role": "assistant",
            "content": resposta,
        }
    )


    guardar_mensagem(
        "assistant",
        resposta,
    )


    # Mantemos uma margem no array
    # interno sem perder a DB persistente.

    if (
        len(messages)
        > 100
    ):

        system = (
            messages[0]
        )

        recentes = (
            messages[
                -MAX_CONTEXT_MESSAGES:
            ]
        )

        messages.clear()

        messages.append(
            system
        )

        messages.extend(
            recentes
        )


    return resposta


# ============================================================
# EXTRAIR MEMÓRIA
# ============================================================

def extrair_memoria(
    texto
):

    prompt = f"""
Analisa a mensagem abaixo e decide se contém uma informação
útil sobre o utilizador que deverá ser lembrada a longo prazo.

Categorias possíveis:

preferencia
facto
objectivo
projecto
outro

Se não houver nada que valha a pena memorizar, responde apenas:

NAO_MEMORIZAR

Caso exista algo relevante, responde exactamente no formato:

CATEGORIA|MEMORIA

Não inventes informação.
Mantém a memória curta e objectiva.

Mensagem:

{texto}
"""


    inicio = (
        time.perf_counter()
    )


    response = (
        ollama.chat(
            model=MODEL,

            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
    )


    mostrar_tempo(
        "Extracção de memória",
        inicio,
    )


    return (
        response[
            "message"
        ][
            "content"
        ]
        .strip()
    )


# ============================================================
# PROCESSAR MEMÓRIA
# ============================================================

def processar_memoria(
    texto
):

    try:

        resultado = (
            extrair_memoria(
                texto
            )
        )


        if (
            resultado
            == "NAO_MEMORIZAR"
        ):

            return


        if "|" not in resultado:

            return


        categoria, memoria = (
            resultado.split(
                "|",
                1,
            )
        )


        categoria = (
            categoria
            .strip()
            .lower()
        )


        memoria = (
            memoria.strip()
        )


        categorias_validas = {
            "preferencia",
            "facto",
            "objectivo",
            "projecto",
            "outro",
        }


        if (
            categoria
            not in categorias_validas
        ):

            categoria = (
                "outro"
            )


        if not memoria:

            return


        inicio = (
            time.perf_counter()
        )


        guardar_ou_actualizar_memoria(
            memoria,
            categoria,
        )


        mostrar_tempo(
            "Guardar memória",
            inicio,
        )


    except Exception as error:

        print(
            "[MEMÓRIA] Erro:",
            error
        )


# ============================================================
# GERAR VOZ + LIP-SYNC
# ============================================================

def gerar_fala(
    texto
):

    if not VOICE_MODEL.exists():

        raise FileNotFoundError(
            f"Modelo Piper não encontrado: "
            f"{VOICE_MODEL}"
        )


    if not RHUBARB.exists():

        raise FileNotFoundError(
            f"Rhubarb não encontrado: "
            f"{RHUBARB}"
        )


    with tempfile.TemporaryDirectory() as temp_dir:

        temp_dir = (
            Path(temp_dir)
        )


        audio_path = (
            temp_dir
            / "baghdad.wav"
        )


        lipsync_path = (
            temp_dir
            / "lipsync.json"
        )


        dialog_path = (
            temp_dir
            / "dialog.txt"
        )


        # ----------------------------------------------------
        # TEXTO PARA RHUBARB
        # ----------------------------------------------------

        dialog_path.write_text(
            texto,
            encoding="utf-8",
        )


        # ----------------------------------------------------
        # PIPER
        # ----------------------------------------------------

        inicio_piper = (
            time.perf_counter()
        )


        subprocess.run(
            [
                sys.executable,
                "-m",
                "piper",

                "--model",
                str(
                    VOICE_MODEL
                ),

                "--output_file",
                str(
                    audio_path
                ),
            ],

            input=texto,

            text=True,

            check=True,
        )


        mostrar_tempo(
            "Piper",
            inicio_piper,
        )


        # ----------------------------------------------------
        # RHUBARB
        # ----------------------------------------------------

        inicio_rhubarb = (
            time.perf_counter()
        )


        result = (
            subprocess.run(
                [
                    str(
                        RHUBARB
                    ),

                    "-r",
                    "phonetic",

                    "-f",
                    "json",

                    "--extendedShapes",
                    "GHX",

                    "--dialogFile",
                    str(
                        dialog_path
                    ),

                    "-o",
                    str(
                        lipsync_path
                    ),

                    str(
                        audio_path
                    ),
                ],

                check=True,

                capture_output=True,

                text=True,
            )
        )


        mostrar_tempo(
            "Rhubarb",
            inicio_rhubarb,
        )


        if result.stderr:

            print(
                result.stderr
            )


        # ----------------------------------------------------
        # LER JSON
        # ----------------------------------------------------

        with open(
            lipsync_path,
            "r",
            encoding="utf-8",
        ) as file:

            lipsync = (
                json.load(
                    file
                )
            )


        # ----------------------------------------------------
        # WAV → BASE64
        # ----------------------------------------------------

        audio_bytes = (
            audio_path.read_bytes()
        )


        audio_base64 = (
            base64.b64encode(
                audio_bytes
            ).decode(
                "ascii"
            )
        )


        return {
            "audio": (
                "data:audio/wav;base64,"
                + audio_base64
            ),

            "mouthCues":
                lipsync.get(
                    "mouthCues",
                    [],
                ),

            "duration":
                lipsync
                .get(
                    "metadata",
                    {},
                )
                .get(
                    "duration",
                    0,
                ),

            "text":
                texto,
        }


# ============================================================
# PROCESSAR UM TURNO COMPLETO
# ============================================================

async def processar_turno(
    websocket,
    request_id,
):

    async with conversation_lock:

        inicio_turno = (
            time.perf_counter()
        )


        try:

            print()
            print(
                "=========================================="
            )

            print(
                "Pedido aceite:",
                request_id
            )

            print(
                "=========================================="
            )


            # =================================================
            # LISTENING
            # =================================================

            await websocket.send_json(
                {
                    "type": "state",

                    "value":
                        "listening",

                    "requestId":
                        request_id,
                }
            )


            inicio_whisper = (
                time.perf_counter()
            )


            pergunta = (
                await asyncio.to_thread(
                    ouvir
                )
            )


            mostrar_tempo(
                "Escuta + Whisper",
                inicio_whisper,
            )


            pergunta = (
                pergunta
                or ""
            ).strip()


            # =================================================
            # SEM TRANSCRIÇÃO
            # =================================================

            if not pergunta:

                print(
                    "Nenhuma fala reconhecida."
                )


                await websocket.send_json(
                    {
                        "type": "state",

                        "value": "idle",

                        "requestId":
                            request_id,
                    }
                )


                return


            print()
            print(
                "Utilizador:",
                pergunta
            )


            await websocket.send_json(
                {
                    "type":
                        "user_text",

                    "text":
                        pergunta,

                    "requestId":
                        request_id,
                }
            )


            # A partir daqui medimos
            # a latência real de resposta.
            inicio_resposta = (
                time.perf_counter()
            )


            # =================================================
            # THINKING
            # =================================================

            await websocket.send_json(
                {
                    "type": "state",

                    "value":
                        "thinking",

                    "requestId":
                        request_id,
                }
            )


            # =================================================
            # GEMMA + MEMÓRIA RELEVANTE
            # =================================================

            resposta = (
                await asyncio.to_thread(
                    gerar_resposta,
                    pergunta,
                )
            )


            print()
            print(
                "Baghdad:",
                resposta
            )


            # Mostrar texto antes da voz
            # ficar pronta.

            await websocket.send_json(
                {
                    "type":
                        "response",

                    "text":
                        resposta,

                    "emotion":
                        "neutral",

                    "requestId":
                        request_id,
                }
            )


            # =================================================
            # PIPER + RHUBARB
            # =================================================

            inicio_voz = (
                time.perf_counter()
            )


            speech = (
                await asyncio.to_thread(
                    gerar_fala,
                    resposta,
                )
            )


            mostrar_tempo(
                "Piper + Rhubarb total",
                inicio_voz,
            )


            # =================================================
            # SPEAKING
            # =================================================

            await websocket.send_json(
                {
                    "type": "state",

                    "value":
                        "speaking",

                    "requestId":
                        request_id,
                }
            )


            await websocket.send_json(
                {
                    "type":
                        "speech",

                    "audio":
                        speech[
                            "audio"
                        ],

                    "mouthCues":
                        speech[
                            "mouthCues"
                        ],

                    "duration":
                        speech[
                            "duration"
                        ],

                    "text":
                        resposta,

                    "emotion":
                        "neutral",

                    "requestId":
                        request_id,
                }
            )


            # =================================================
            # TEMPO DE RESPOSTA
            # =================================================

            mostrar_tempo(
                "TOTAL até começar fala",
                inicio_resposta,
            )


            mostrar_tempo(
                "Turno completo",
                inicio_turno,
            )


            print(
                "=========================================="
            )
            print()


            # =================================================
            # MEMÓRIA DE LONGO PRAZO
            # =================================================

            # Só começamos isto depois de:
            # Gemma responder,
            # Piper terminar,
            # Rhubarb terminar,
            # e o áudio já ter sido enviado ao avatar.

            asyncio.create_task(
                asyncio.to_thread(
                    processar_memoria,
                    pergunta,
                )
            )


        except Exception as error:

            print(
                "Erro durante conversa:",
                error
            )


            try:

                await websocket.send_json(
                    {
                        "type":
                            "error",

                        "message":
                            str(error),

                        "requestId":
                            request_id,
                    }
                )


                await websocket.send_json(
                    {
                        "type":
                            "state",

                        "value":
                            "idle",

                        "requestId":
                            request_id,
                    }
                )


            except Exception:

                pass


# ============================================================
# WEBSOCKET
# ============================================================

@app.websocket(
    "/ws/avatar"
)
async def avatar_websocket(
    websocket: WebSocket
):

    await websocket.accept()


    print(
        "Avatar ligado."
    )


    await websocket.send_json(
        {
            "type": "state",
            "value": "idle",
        }
    )


    try:

        while True:

            raw = (
                await websocket.receive_text()
            )


            try:

                message = (
                    json.loads(
                        raw
                    )
                )


            except json.JSONDecodeError:

                print(
                    "Mensagem WebSocket inválida."
                )

                continue


            message_type = (
                message.get(
                    "type"
                )
            )


            # =================================================
            # FRONTEND PRONTO
            # =================================================

            if (
                message_type
                == "avatar_ready"
            ):

                print(
                    "Frontend pronto."
                )

                continue


            # =================================================
            # COMEÇAR ESCUTA
            # =================================================

            if (
                message_type
                == "start_listening"
            ):

                request_id = (
                    message.get(
                        "requestId"
                    )
                )


                print(
                    "Pedido de escuta recebido:",
                    request_id
                )


                # --------------------------------------------
                # REQUEST ID obrigatório
                # --------------------------------------------

                if not request_id:

                    print(
                        "Pedido sem requestId ignorado."
                    )

                    continue


                # --------------------------------------------
                # DUPLICADO
                # --------------------------------------------

                if (
                    request_id
                    in processed_request_ids
                ):

                    print(
                        "Pedido duplicado ignorado:",
                        request_id
                    )

                    continue


                processed_request_ids.add(
                    request_id
                )


                # Evitar crescimento infinito.

                if (
                    len(
                        processed_request_ids
                    )
                    > 500
                ):

                    processed_request_ids.clear()

                    processed_request_ids.add(
                        request_id
                    )


                # --------------------------------------------
                # OCUPADO
                # --------------------------------------------

                if (
                    conversation_lock.locked()
                ):

                    await websocket.send_json(
                        {
                            "type":
                                "busy",

                            "requestId":
                                request_id,
                        }
                    )

                    continue


                # --------------------------------------------
                # PROCESSAR
                # --------------------------------------------

                await processar_turno(
                    websocket,
                    request_id,
                )

                continue


            # =================================================
            # FALA TERMINOU
            # =================================================

            if (
                message_type
                == "speech_ended"
            ):

                print(
                    "Avatar terminou de falar."
                )


                await websocket.send_json(
                    {
                        "type":
                            "state",

                        "value":
                            "idle",
                    }
                )

                continue


    except WebSocketDisconnect:

        print(
            "Avatar desligado."
        )


    except Exception as error:

        print(
            "Erro WebSocket:",
            error
        )