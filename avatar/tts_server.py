import os
import tempfile

import numpy as np
import sounddevice as sd

from scipy.io.wavfile import write
from faster_whisper import WhisperModel


# ============================================================
# CONFIGURAÇÃO
# ============================================================

SAMPLE_RATE = 16000

CHANNELS = 1

BLOCK_DURATION = 0.1

BLOCK_SIZE = int(
    SAMPLE_RATE * BLOCK_DURATION
)


# Este valor já estava bem ajustado
VOICE_THRESHOLD = 500


# Depois de começar a falar,
# 1.2 segundos de silêncio terminam a gravação.
SILENCE_SECONDS = 1.2


SILENCE_BLOCKS = int(
    SILENCE_SECONDS
    / BLOCK_DURATION
)


# Limite máximo DEPOIS
# de começar a falar.
MAX_DURATION = 20


MAX_BLOCKS = int(
    MAX_DURATION
    / BLOCK_DURATION
)


# ============================================================
# WHISPER
# ============================================================

model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8",
)


# ============================================================
# OUVIR
# ============================================================

def ouvir():

    print("\nA ouvir...")


    audio_blocks = []


    voz_detectada = False


    blocos_silencio = 0


    blocos_depois_da_voz = 0


    try:

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=BLOCK_SIZE,
        ) as stream:


            while True:

                audio, _ = stream.read(
                    BLOCK_SIZE
                )


                audio = audio.copy()


                amplitude = np.mean(
                    np.abs(
                        audio.astype(
                            np.int32
                        )
                    )
                )


                # ============================================
                # AINDA NÃO COMEÇOU A FALAR
                # ============================================

                if not voz_detectada:

                    if (
                        amplitude
                        >= VOICE_THRESHOLD
                    ):

                        voz_detectada = True

                        audio_blocks.append(
                            audio
                        )

                        blocos_depois_da_voz = 1


                    # Importante:
                    # NÃO existe timeout aqui.
                    # Espera até o utilizador falar.

                    continue


                # ============================================
                # JÁ COMEÇOU A FALAR
                # ============================================

                audio_blocks.append(
                    audio
                )


                blocos_depois_da_voz += 1


                if (
                    amplitude
                    < VOICE_THRESHOLD
                ):

                    blocos_silencio += 1

                else:

                    blocos_silencio = 0


                # --------------------------------------------
                # Silêncio após a fala
                # --------------------------------------------

                if (
                    blocos_silencio
                    >= SILENCE_BLOCKS
                ):

                    break


                # --------------------------------------------
                # Protecção contra fala demasiado longa
                # --------------------------------------------

                if (
                    blocos_depois_da_voz
                    >= MAX_BLOCKS
                ):

                    break


    except KeyboardInterrupt:

        print(
            "\nEscuta interrompida."
        )

        return ""


    # ========================================================
    # JUNTAR ÁUDIO
    # ========================================================

    if not audio_blocks:

        return ""


    audio_final = np.concatenate(
        audio_blocks,
        axis=0,
    )


    # ========================================================
    # WAV TEMPORÁRIO
    # ========================================================

    temp = tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False,
    )


    audio_path = temp.name

    temp.close()


    try:

        write(
            audio_path,
            SAMPLE_RATE,
            audio_final,
        )


        # ====================================================
        # WHISPER
        # ====================================================

        segments, _ = model.transcribe(
            audio_path,
            language="pt",
            vad_filter=True,
        )


        texto = " ".join(
            segment.text.strip()
            for segment in segments
        ).strip()


        return texto


    finally:

        try:

            os.remove(
                audio_path
            )

        except FileNotFoundError:

            pass