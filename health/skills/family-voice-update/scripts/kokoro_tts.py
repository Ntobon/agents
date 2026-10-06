"""Text -> .wav with Kokoro-82M, locally (ONNX). The text never leaves the computer.

Usage:
    python kokoro_tts.py script.txt out.wav [voice] [speed] [lang]

Defaults: voice em_alex, speed 1.0, lang es. Spanish voices: em_alex (male), ef_dora (female).
Model files (kokoro-v1.0.onnx, voices-v1.0.bin) are read from KOKORO_MODEL / KOKORO_VOICES,
or from ~/.cache/kokoro/ when those are not set.
Each paragraph (separated by a blank line) is synthesized on its own and joined with a short pause.
"""
import os
import sys

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

CACHE = os.path.join(os.path.expanduser("~"), ".cache", "kokoro")
MODEL = os.environ.get("KOKORO_MODEL", os.path.join(CACHE, "kokoro-v1.0.onnx"))
VOICES = os.environ.get("KOKORO_VOICES", os.path.join(CACHE, "voices-v1.0.bin"))
PAUSE_S = 0.45


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else "em_alex"
    speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    lang = sys.argv[5] if len(sys.argv) > 5 else "es"

    k = Kokoro(MODEL, VOICES)
    text = open(src, encoding="utf-8").read()
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    parts, sr = [], 24000
    for p in paragraphs:
        audio, sr = k.create(p, voice=voice, speed=speed, lang=lang)
        parts += [audio, np.zeros(int(sr * PAUSE_S), dtype=audio.dtype)]
    out = np.concatenate(parts)
    tmp = dst + ".tmp.wav"
    sf.write(tmp, out, sr)
    os.replace(tmp, dst)  # atomic: never leaves a half-written file
    print(f"ok {len(out) / sr:.1f} s -> {dst}")


if __name__ == "__main__":
    main()
