#!/usr/bin/env python3
"""Render the reviewed Portuguese dialogue; never runs the statistical pipeline.

Requires the optional requirements-podcast.txt, FFmpeg and downloaded Kokoro
voice models. Synthesis is entirely local; no script is sent to a speech API.
Voices are generic, not impersonations.
Only text inside AUDIO_START/AUDIO_END is synthesized. Intermediate audio is
cached outside the repository; an actual duration check enforces <=20 minutes.

Example:
    python scripts/build_podcast.py --models /tmp/voices --audio /tmp/EAD6034_Podcast_Preparacao.mp3

Upstream: https://github.com/thewh1teagle/kokoro-onnx
"""

from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re
import subprocess
import tempfile
import wave

import numpy as np
import onnxruntime as ort
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RATE = 24000
VOICES = {
    "Apresentador": "pm_alex",
    "Interlocutor": "pf_dora",
}
SYNTHESIS = {"speed": 0.90, "lang": "pt-br", "sentence_pause": 0.25, "clause_pause": 0.1}
PAUSE_TURN = 0.32
PAUSE_CHAPTER = 1.10
PRONUNCIATIONS = {
    "ARCH-LM": "arque éle ême",
    "Box–Jenkins": "Bóks Djenkins",
    "Ljung–Box": "Iúng Bóks",
    "Yule–Walker": "Iúl Uólquer",
    "Phillips–Perron": "Fílips Perron",
    "Diebold–Mariano": "Díbold Mariano",
    "FACP": "fác pê",
    "FAC": "fác",
    "KPSS": "cá pê ésse ésse",
    "ADF": "á dê éfe",
    "GARCH": "garque",
    "ARCH": "arque",
    "ARMA": "arma",
    "OLS": "ó éle ésse",
    "BIC": "bic",
    "AIC": "á i cê",
    "MSE": "ême ésse ê",
    "MAE": "ême á ê",
    "AR": "á érre",
    "MA": "ême á",
    "WIN": "uín",
    "BTG": "bê tê gê",
    "ATS": "á tê ésse",
    "EAD": "ê á dê",
    "Alpha Lab": "Alfa Léb",
    "GitHub": "Guít Râb",
    "proxy": "próxi",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, capture_output=True, **kwargs)


def probe(path: Path) -> dict:
    return json.loads(run([
        "ffprobe", "-v", "error", "-show_format", "-show_streams",
        "-show_chapters", "-of", "json", str(path),
    ]).stdout)


def spoken(text: str) -> str:
    for source, target in PRONUNCIATIONS.items():
        text = re.sub(r"(?<!\w)" + re.escape(source) + r"(?!\w)", target, text)
    return text


def parse_dialogue(path: Path) -> tuple[list[dict], str]:
    source = path.read_text(encoding="utf-8")
    if source.count("<!-- AUDIO_START -->") != 1 or source.count("<!-- AUDIO_END -->") != 1:
        raise ValueError("Expected exactly one delimited dialogue.")
    dialogue = source.split("<!-- AUDIO_START -->")[1].split("<!-- AUDIO_END -->")[0]
    turns: list[dict] = []
    chapter = None
    for block in re.split(r"\n\s*\n", dialogue.strip()):
        if block.startswith("## "):
            chapter = block.removeprefix("## ").strip()
            continue
        match = re.fullmatch(r"\*\*(Apresentador|Interlocutor):\*\*\s*(.+)", block, flags=re.S)
        if not match or chapter is None:
            raise ValueError(f"Unparsed dialogue block: {block[:80]!r}")
        speaker, text = match.groups()
        turns.append({"speaker": speaker, "text": text.strip(), "chapter": chapter})
    if not turns:
        raise ValueError("Empty dialogue.")
    return turns, source


def synthesize_all(turns: list[dict], cache: Path, models: Path) -> dict:
    ort.set_seed(42)
    model_file = models / "kokoro-v1.0.onnx"
    voice_file = models / "voices-v1.0.bin"
    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(model_file), sess_options=options,
                                   providers=["CPUExecutionProvider"])
    engine = Kokoro.from_session(session, str(voice_file))
    hashes = {"model_sha256": digest(model_file), "voices_sha256": digest(voice_file)}
    for i, turn in enumerate(turns):
        voice_name = VOICES[turn["speaker"]]
        text = spoken(turn["text"])
        key = hashlib.sha256(json.dumps([text, voice_name, SYNTHESIS, hashes,
                                       version("kokoro-onnx")]).encode()).hexdigest()[:20]
        target = cache / f"{i:03d}_{key}.wav"
        if not target.exists():
            temporary = target.with_suffix(".part.wav")
            samples, sample_rate = engine.create(text, voice=voice_name, **SYNTHESIS)
            sf.write(str(temporary), samples, sample_rate, subtype="PCM_16")
            with wave.open(str(temporary)) as wav:
                if wav.getnframes() / wav.getframerate() < 0.25:
                    raise ValueError("Empty speech segment.")
            temporary.replace(target)
        turn["segment_file"] = str(target)
        turn["spoken_text"] = text
        turn["voice"] = voice_name
        print(f"speech {i + 1}/{len(turns)}: ready", flush=True)
    return hashes


def decode_trim(path: Path) -> np.ndarray:
    raw = run([
        "ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le",
        "-ar", str(SAMPLE_RATE), "-ac", "1", "pipe:1",
    ]).stdout
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    # Remove only outer silence, with a generous 100 ms guard for consonants.
    window = SAMPLE_RATE // 100
    count = len(samples) // window
    rms = np.sqrt(np.mean(samples[:count * window].reshape(count, window) ** 2, axis=1))
    active = np.flatnonzero(rms > 10 ** (-48 / 20))
    if len(active) == 0:
        raise ValueError(f"Silent segment {path.name}")
    start = max(0, int(active[0] * window - 0.10 * SAMPLE_RATE))
    end = min(len(samples), int((active[-1] + 1) * window + 0.10 * SAMPLE_RATE))
    samples = samples[start:end].copy()
    ramp_length = int(0.003 * SAMPLE_RATE)
    ramp = np.linspace(0, 1, ramp_length)
    samples[:ramp_length] *= ramp
    samples[-ramp_length:] *= ramp[::-1]
    return samples


def stamp(seconds: float) -> str:
    seconds = int(seconds)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def assemble(turns: list[dict], cache: Path) -> tuple[Path, list[dict], float]:
    destination = cache / "dialogue.wav"
    clock = 0
    chapters: list[dict] = []
    with wave.open(str(destination), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        for i, turn in enumerate(turns):
            is_new = i == 0 or turn["chapter"] != turns[i - 1]["chapter"]
            pause = 0.45 if i == 0 else (PAUSE_CHAPTER if is_new else PAUSE_TURN)
            silence_n = int(pause * SAMPLE_RATE)
            wav.writeframes(bytes(silence_n * 2))
            clock += silence_n
            if is_new:
                if chapters:
                    chapters[-1]["end"] = clock / SAMPLE_RATE
                chapters.append({"title": turn["chapter"], "start": clock / SAMPLE_RATE})
            samples = decode_trim(Path(turn["segment_file"]))
            turn["start"] = clock / SAMPLE_RATE
            turn["decoded_duration"] = len(samples) / SAMPLE_RATE
            wav.writeframes((np.clip(samples, -1, 1) * 32767).astype(np.int16).tobytes())
            clock += len(samples)
            turn["end"] = clock / SAMPLE_RATE
        wav.writeframes(bytes(int(0.65 * SAMPLE_RATE) * 2))
        clock += int(0.65 * SAMPLE_RATE)
    duration = clock / SAMPLE_RATE
    chapters[-1]["end"] = duration
    return destination, chapters, duration


def encode(wav: Path, audio: Path, chapters: list[dict], duration: float, cache: Path) -> tuple[float, dict]:
    # Only speed up if required to keep generous margin under the requested cap.
    factor = max(1.0, duration / 1170.0)
    if factor > 1.12:
        raise ValueError("Revise the script rather than accelerate dense material excessively.")
    for chapter in chapters:
        chapter["start"] /= factor
        chapter["end"] /= factor
    metadata = [
        ";FFMETADATA1", "title=EAD6034 — Preparação para o seminário",
        "artist=Duas vozes sintéticas — material de estudo de Renan de Luca Avila",
        "album=Entregas cumulativas de 31/08, 14/09 e 21/09/2026",
        "comment=Roteiro e código: https://github.com/avilarenan/EAD6034",
        "language=por",
    ]
    for chapter in chapters:
        metadata.extend([
            "[CHAPTER]", "TIMEBASE=1/1000",
            f"START={round(chapter['start'] * 1000)}", f"END={round(chapter['end'] * 1000)}",
            "title=" + chapter["title"],
        ])
    metadata_file = cache / "chapters.ffmeta"
    metadata_file.write_text("\n".join(metadata) + "\n", encoding="utf-8")
    base_filter = f"atempo={factor:.8f}," if factor != 1 else ""
    measurement = run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(wav), "-af",
        base_filter + "loudnorm=I=-18:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-",
    ]).stderr.decode()
    loudness = json.loads(measurement[measurement.rfind("{"):])
    normalizer = (
        "loudnorm=I=-18:TP=-1.5:LRA=11:linear=true:"
        f"measured_I={loudness['input_i']}:measured_TP={loudness['input_tp']}:"
        f"measured_LRA={loudness['input_lra']}:measured_thresh={loudness['input_thresh']}:"
        f"offset={loudness['target_offset']}"
    )
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(wav), "-i", str(metadata_file),
        "-map", "0:a", "-map_metadata", "1", "-map_chapters", "1",
        "-af", base_filter + normalizer, "-ar", str(SAMPLE_RATE), "-ac", "1",
        "-codec:a", "libmp3lame", "-b:a", "96k", "-id3v2_version", "3", str(audio),
    ])
    return factor, loudness


def write_transcript(source: str, turns: list[dict], chapters: list[dict], duration: float, destination: Path) -> None:
    introduction, rest = source.split("<!-- AUDIO_START -->")
    notes = rest.split("<!-- AUDIO_END -->")[1]
    lines = [introduction.rstrip(), "", f"**Duração medida do MP3: {stamp(duration)}.**", "",
             "## Índice do áudio", "", "| Início | Assunto |", "| --- | --- |"]
    lines += [f"| {stamp(c['start'])} | {c['title']} |" for c in chapters]
    current = None
    for turn in turns:
        if turn["chapter"] != current:
            current = turn["chapter"]
            lines += ["", f"## {current}"]
        lines += ["", f"**[{stamp(turn['start'])}] {turn['speaker']}:** {turn['text']}"]
    lines += ["", notes.strip(), "", "## Produção do áudio", "",
              "Duas vozes sintéticas genéricas em português brasileiro: Alex e Dora. "
              "Síntese local com [Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx), montagem em Python e FFmpeg, "
              "sem trilha musical. Siglas e nomes técnicos recebem adaptações de pronúncia; "
              "a transcrição conserva a grafia acadêmica.", "",
              "[Modelo Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) · "
              "[Catálogo de vozes](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md). "
              "Modelo sob licença Apache 2.0; a biblioteca kokoro-onnx usa licença MIT.", "",
              "[Roteiro-fonte](https://github.com/avilarenan/EAD6034/blob/main/docs/PODCAST_PREPARACAO_21_09.md) · "
              "[Gerador Python](https://github.com/avilarenan/EAD6034/blob/main/scripts/build_podcast.py)", ""]
    destination.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", type=Path, default=ROOT / "docs/PODCAST_PREPARACAO_21_09.md")
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--results", type=Path, default=ROOT / "results/entrega_21_09")
    parser.add_argument("--models", type=Path, required=True, help="Directory with kokoro-v1.0.onnx and voices-v1.0.bin")
    args = parser.parse_args()
    cache = args.cache or Path(tempfile.mkdtemp(prefix="ead6034_podcast_"))
    cache.mkdir(parents=True, exist_ok=True)
    args.audio.parent.mkdir(parents=True, exist_ok=True)
    args.results.mkdir(parents=True, exist_ok=True)
    turns, source = parse_dialogue(args.script)
    voice_hashes = synthesize_all(turns, cache, args.models)
    wav, chapters, raw_duration = assemble(turns, cache)
    factor, loudness = encode(wav, args.audio, chapters, raw_duration, cache)
    for turn in turns:
        turn["start"] /= factor
        turn["end"] /= factor
    measured = probe(args.audio)
    duration = float(measured["format"]["duration"])
    if not (60 < duration <= 1200):
        raise ValueError(f"Duration outside requested limit: {duration:.3f}s")
    # Decode every frame; reject corrupt outputs before publication.
    run(["ffmpeg", "-v", "error", "-xerror", "-i", str(args.audio), "-f", "null", "-"])
    write_transcript(source, turns, chapters, duration, args.results / "PODCAST_TRANSCRICAO.md")
    manifest = {
        "title": "EAD6034 — Preparação para o seminário",
        "language": "pt-BR", "synthetic_voices": VOICES, "kokoro_onnx_version": version("kokoro-onnx"),
        "synthesis": SYNTHESIS, "voice_hashes": voice_hashes,
        "audio_file": args.audio.name, "audio_sha256": digest(args.audio),
        "script_sha256": digest(args.script), "generator_sha256": digest(Path(__file__)),
        "duration_seconds": duration, "duration_mmss": stamp(duration),
        "maximum_duration_seconds": 1200, "turn_count": len(turns),
        "spoken_script_word_count": sum(len(t["text"].split()) for t in turns),
        "tempo_factor": factor, "sample_rate": SAMPLE_RATE, "channels": 1, "bitrate": 96000,
        "chapters": chapters, "loudness_first_pass": loudness,
        "decode_validation": "All frames decoded without error by FFmpeg",
        "source_results_commit": "e64cd0870a379c0064f3b0ebbd307266ecd9733c",
        "scientific_code_ref": "f63a1048db3c36d2aeece3c8806be49f1be1a63c",
        "scope": "Didactic rendering of existing results; no model re-estimation",
    }
    (args.results / "podcast_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (cache / "turns_timing.json").write_text(json.dumps(turns, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"audio": str(args.audio), "duration": stamp(duration), "seconds": duration,
                      "chapters": len(chapters), "turns": len(turns), "tempo_factor": factor}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
