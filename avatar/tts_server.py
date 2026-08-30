from pathlib import Path
import base64
import json
import subprocess
import sys
import tempfile

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI()


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


# Baghdad/
ROOT = Path(__file__).resolve().parent.parent

# Baghdad/avatar/
AVATAR_DIR = Path(__file__).resolve().parent


VOICE_MODEL = (
    ROOT
    / "voices"
    / "dii_pt-PT.onnx"
)


RHUBARB = (
    AVATAR_DIR
    / "tools"
    / "rhubarb"
    / "rhubarb"
)


class SpeakRequest(BaseModel):
    text: str


@app.get("/")
def root():
    return {
        "status": "ok",
        "voice": VOICE_MODEL.name,
        "rhubarb": RHUBARB.exists(),
    }


@app.post("/speak")
def speak(request: SpeakRequest):

    texto = request.text.strip()

    if not texto:
        raise HTTPException(
            status_code=400,
            detail="Texto vazio.",
        )

    if not VOICE_MODEL.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                "Modelo Piper não encontrado: "
                f"{VOICE_MODEL}"
            ),
        )

    if not RHUBARB.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                "Rhubarb não encontrado: "
                f"{RHUBARB}"
            ),
        )


# ------------------------------------------------------------------

    try:

        with tempfile.TemporaryDirectory() as temp_dir:

            temp_dir = Path(temp_dir)

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


            # ---------------------------------
            # TEXTO PARA AJUDAR O RHUBARB
            # ---------------------------------

            dialog_path.write_text(
                texto,
                encoding="utf-8",
            )


            # ---------------------------------
            # PIPER
            # ---------------------------------

            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "piper",

                    "--model",
                    str(VOICE_MODEL),

                    "--output_file",
                    str(audio_path),
                ],
                input=texto,
                text=True,
                check=True,
            )


            # ---------------------------------
            # RHUBARB
            # ---------------------------------

            subprocess.run(
                [
                    str(RHUBARB),

                    "-r",
                    "phonetic",

                    "-f",
                    "json",

                    "--extendedShapes",
                    "GHX",

                    "-d",
                    str(dialog_path),

                    "-o",
                    str(lipsync_path),

                    str(audio_path),
                ],
                check=True,
            )


            # ---------------------------------
            # LER LIP SYNC
            # ---------------------------------

            with open(
                lipsync_path,
                "r",
                encoding="utf-8",
            ) as file:

                lipsync = json.load(
                    file
                )


            # ---------------------------------
            # LER WAV
            # ---------------------------------

            audio_bytes = (
                audio_path.read_bytes()
            )


            audio_base64 = (
                base64.b64encode(
                    audio_bytes
                ).decode("ascii")
            )


            return {
                "audio": (
                    "data:audio/wav;base64,"
                    + audio_base64
                ),

                "mouthCues": (
                    lipsync.get(
                        "mouthCues",
                        [],
                    )
                ),

                "duration": (
                    lipsync
                    .get(
                        "metadata",
                        {},
                    )
                    .get(
                        "duration",
                        0,
                    )
                ),
            }


    except subprocess.CalledProcessError as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Erro ao gerar voz "
                "ou lip-sync."
            ),
        ) from error