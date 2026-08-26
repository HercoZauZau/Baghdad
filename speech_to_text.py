import os
import tempfile

import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel


SAMPLE_RATE = 16000
DURATION = 5
MODEL_SIZE = "small"


print("A carregar modelo Whisper...")

model = WhisperModel(
    MODEL_SIZE,
    device="cpu",
    compute_type="int8"
)


def gravar_audio(duracao=DURATION):
    print("\nA ouvir...")

    audio = sd.rec(
        int(duracao * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    return audio


def guardar_audio_temporario(audio):
    ficheiro = tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False
    )

    caminho = ficheiro.name
    ficheiro.close()

    write(
        caminho,
        SAMPLE_RATE,
        audio
    )

    return caminho


def transcrever_audio(caminho):
    segments, info = model.transcribe(
        caminho,
        language="pt"
    )

    texto = " ".join(
        segment.text.strip()
        for segment in segments
    )

    return texto.strip()


def ouvir():
    audio = gravar_audio()

    caminho = guardar_audio_temporario(
        audio
    )

    try:
        texto = transcrever_audio(
            caminho
        )

        return texto

    finally:
        if os.path.exists(caminho):
            os.remove(caminho)


def main():
    texto = ouvir()

    if texto:
        print("\nTranscrição:")
        print(texto)
    else:
        print("\nNão foi possível reconhecer nenhuma fala.")


if __name__ == "__main__":
    main()
