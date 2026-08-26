import os
import queue
import tempfile

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel


SAMPLE_RATE = 16000
CHANNELS = 1

MODEL_SIZE = "small"

# Sensibilidade do microfone.
# Quanto menor, mais sensível.
VOICE_THRESHOLD = 500

# Tempo de silêncio necessário para terminar.
SILENCE_SECONDS = 1.2

# Tempo máximo permitido para uma fala.
MAX_DURATION = 20


print("A carregar modelo Whisper...")

model = WhisperModel(
    MODEL_SIZE,
    device="cpu",
    compute_type="int8"
)


def ouvir_audio():
    fila_audio = queue.Queue()

    blocos = []

    voz_detectada = False

    blocos_silencio = 0

    block_duration = 0.1

    blocksize = int(
        SAMPLE_RATE * block_duration
    )

    max_blocos = int(
        MAX_DURATION / block_duration
    )

    silencio_max_blocos = int(
        SILENCE_SECONDS / block_duration
    )

    def callback(indata, frames, time, status):
        if status:
            print(status)

        fila_audio.put(
            indata.copy()
        )

    print("\nA ouvir...")

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        blocksize=blocksize,
        callback=callback
    ):

        for _ in range(max_blocos):
            bloco = fila_audio.get()

            volume = np.abs(
                bloco
            ).mean()

            if volume > VOICE_THRESHOLD:
                voz_detectada = True
                blocos_silencio = 0

            elif voz_detectada:
                blocos_silencio += 1

            if voz_detectada:
                blocos.append(
                    bloco
                )

            if (
                voz_detectada
                and blocos_silencio >= silencio_max_blocos
            ):
                break

    if not blocos:
        return None

    audio = np.concatenate(
        blocos,
        axis=0
    )

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
        language="pt",
        vad_filter=True
    )

    texto = " ".join(
        segment.text.strip()
        for segment in segments
    )

    return texto.strip()


def ouvir():
    audio = ouvir_audio()

    if audio is None:
        return ""

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
        print(
            "\nTranscrição:"
        )

        print(
            texto
        )

    else:
        print(
            "\nNenhuma fala detectada."
        )


if __name__ == "__main__":
    main()