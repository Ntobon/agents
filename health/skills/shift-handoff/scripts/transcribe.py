"""Transcribe voice notes locally with faster-whisper (nothing leaves the machine).

Usage:
    python transcribe.py AUDIO [AUDIO ...] [--model large-v3] [--language es] [--out transcript.md]

- Tries GPU (CUDA) and, if a library is missing or encoding fails, falls back to CPU (int8).
- Reads .ogg/.opus/.m4a/.mp3 directly (no ffmpeg needed).
- Always writes UTF-8; without --out, prints UTF-8 to stdout.
- Install: python -m pip install faster-whisper
"""
import argparse
import os
import sys


def load(model, device):
    from faster_whisper import WhisperModel
    if device == "cuda":
        return WhisperModel(model, device="cuda", compute_type="float16")
    return WhisperModel(model, device="cpu", compute_type="int8")


def run(m, path, language):
    segs, info = m.transcribe(path, language=language, beam_size=5, vad_filter=True)
    text = " ".join(s.text.strip() for s in segs)  # decoding happens here
    return text, info.duration


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audios", nargs="+")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--language", default="es")
    ap.add_argument("--out")
    a = ap.parse_args()

    device = "cuda"
    try:
        m = load(a.model, device)
    except Exception:
        device = "cpu"
        m = load(a.model, device)

    blocks = []
    for path in a.audios:
        try:
            text, dur = run(m, path, a.language)
        except RuntimeError:
            if device == "cpu":
                raise
            device = "cpu"
            m = load(a.model, device)
            text, dur = run(m, path, a.language)
        mins, secs = divmod(int(round(dur)), 60)
        blocks.append(f"## {os.path.basename(path)} ({mins}:{secs:02d})\n\n> {text}\n")

    body = f"<!-- Whisper {a.model}, {device}, local -->\n\n" + "\n".join(blocks)
    if a.out:
        tmp = a.out + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(body)
        os.replace(tmp, a.out)
        print(f"ok: {a.out} ({device})")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(body)


if __name__ == "__main__":
    main()
