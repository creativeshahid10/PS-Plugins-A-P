#!/usr/bin/env python3


















import argparse
import json
import os
import sys
import typing




















_BACKPORTED = [
    "TypeGuard", "TypeAlias", "ParamSpec", "ParamSpecArgs", "ParamSpecKwargs",
    "Concatenate", "Self", "Never", "Unpack", "TypeVarTuple", "LiteralString",
    "NotRequired", "Required", "assert_never", "override", "dataclass_transform",
]

_missing = [n for n in _BACKPORTED if not hasattr(typing, n)]
if _missing:
    try:
        import typing_extensions
    except ImportError:
        typing_extensions = None

    if typing_extensions is None:
        print(
            "ERROR: This Python (%d.%d, %s) is too old for Whisper's dependencies, "
            "and typing_extensions is not installed to bridge the gap.\n"
            "  Fix A (best): install Python 3.11 or 3.12 and run Install / Fix "
            "Dependencies again — Whisper's dependencies target 3.10 and newer.\n"
            "  Fix B (quick): \"%s\" -m pip install typing_extensions"
            % (sys.version_info[0], sys.version_info[1], sys.executable, sys.executable)
        )
        sys.exit(1)

    _unbridged = []
    for _name in _missing:
        if hasattr(typing_extensions, _name):
            setattr(typing, _name, getattr(typing_extensions, _name))
        else:
            _unbridged.append(_name)

    if _unbridged:
        print(
            "ERROR: Python %d.%d is missing %s, and the installed typing_extensions "
            "cannot supply %s.\n"
            "  Fix A (best): install Python 3.11 or 3.12 and run Install / Fix Dependencies again.\n"
            "  Fix B: \"%s\" -m pip install --upgrade typing_extensions"
            % (sys.version_info[0], sys.version_info[1], ", ".join(_missing),
               ", ".join(_unbridged), sys.executable)
        )
        sys.exit(1)


def log(message):

    print(message, flush=True)


def fail(message):
    print("ERROR: " + message, flush=True)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Flex transcript cleanup")
    parser.add_argument("--input", required=True, help="Audio/video file to transcribe")
    parser.add_argument("--output", required=True, help="Where to write the word JSON")
    parser.add_argument("--model", default="turbo", help="Whisper model: turbo, medium or large-v3")
    parser.add_argument("--language", default="auto", help="Language code or 'auto'")
    parser.add_argument("--initial-prompt", default="", dest="initial_prompt")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        fail("Input file not found: " + args.input)

    try:
        import whisper
    except Exception as import_error:
        fail("Whisper is not installed: " + str(import_error))

    log("Loading Whisper model '%s' (first run downloads it)..." % args.model)
    try:
        retired = {'tiny': 'turbo', 'tiny.en': 'turbo', 'base': 'turbo', 'base.en': 'turbo',
                   'small': 'turbo', 'small.en': 'turbo', 'medium.en': 'medium'}
        model = whisper.load_model(retired.get(args.model, args.model))
    except Exception as load_error:
        fail("Could not load Whisper model: " + str(load_error))


    transcribe_args = {"word_timestamps": True, "verbose": False, "condition_on_previous_text": False}
    if args.language and args.language != "auto":
        transcribe_args["language"] = args.language
    if args.initial_prompt:
        transcribe_args["initial_prompt"] = args.initial_prompt

    log("Transcribing with word-level timestamps...")
    try:
        result = model.transcribe(args.input, **transcribe_args)
    except Exception as transcribe_error:
        fail("Transcription failed: " + str(transcribe_error))

    words = []
    for segment in result.get("segments", []) or []:
        for word in segment.get("words", []) or []:
            raw = word.get("word", "")
            text = raw.strip()
            if not text:
                continue
            try:
                start = float(word.get("start", segment.get("start", 0.0)))
                end = float(word.get("end", segment.get("end", 0.0)))
            except (TypeError, ValueError):
                continue
            if end <= start:
                continue
            words.append({
                "word": text,
                "start": round(start, 4),
                "end": round(end, 4),
                "prob": round(float(word.get("probability", 0.0) or 0.0), 4),
            })

    if not words:


        log("WARNING: no word-level timestamps were returned.")
        log("Update Whisper (pip install -U openai-whisper) for word timing support.")

    payload = {
        "language": result.get("language", args.language),
        "duration": round(float(words[-1]["end"]), 4) if words else 0.0,
        "words": words,
    }

    try:
        out_dir = os.path.dirname(os.path.abspath(args.output))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False)
    except Exception as write_error:
        fail("Could not write output JSON: " + str(write_error))

    log("Transcribed %d words." % len(words))
    log("DONE")


if __name__ == "__main__":
    main()
