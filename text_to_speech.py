import os
import sys
import subprocess
import tempfile


# VOICE_MODEL = "voices/pt_PT-tug%C3%A3o-medium.onnx"
VOICE_MODEL = "voices/dii_pt-PT.onnx"


def falar(texto):
    if not texto:
        return

    ficheiro = tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False
    )

    caminho_audio = ficheiro.name
    ficheiro.close()

    try:
        # Gera o áudio usando o Piper instalado
        # no mesmo ambiente virtual do Python.
        subprocess.run(
            [
                sys.executable,
                "-m",
                "piper",
                "--model",
                VOICE_MODEL,
                "--length_scale",
                "1.0",
                "--output_file",
                caminho_audio
            ],
            input=texto,
            text=True,
            check=True
        )

        # Reproduz o áudio
        subprocess.run(
            [
                "aplay",
                caminho_audio
            ],
            check=True
        )

    except subprocess.CalledProcessError as erro:
        print(
            f"[Erro no Text-to-Speech: {erro}]"
        )

    except FileNotFoundError as erro:
        print(
            f"[Programa não encontrado: {erro}]"
        )

    finally:
        # Apaga o áudio temporário
        if os.path.exists(caminho_audio):
            os.remove(caminho_audio)


def main():
    falar(
        "Olá. Eu sou Baghdad."
    )


if __name__ == "__main__":
    main()

