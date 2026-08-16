# app/main.py
import argparse
import json
import os

from app.agent import PhraseCutAgent
from app.memory import load_memory, save_memory, apply_correction
from app.transcribe import generate_transcripts  # Import the new module


def load_json_file(path: str, label: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise SystemExit(f"{label} file not found: {path}")
    except json.JSONDecodeError as e:
        raise SystemExit(
            f"{label} file is not valid JSON: {path} (line {e.lineno}, column {e.colno})"
        )


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    cut_parser = subparsers.add_parser("cut")
    # Make video required, and JSONs optional
    cut_parser.add_argument("--video", required=True)
    cut_parser.add_argument("--transcript", required=False)
    cut_parser.add_argument("--timings", required=False)
    cut_parser.add_argument("--phrase", required=True)
    cut_parser.add_argument("--output", required=False, default="outputs/clip.mp4")
    cut_parser.add_argument("--memory", required=False, default="state/memory.json")

    corr_parser = subparsers.add_parser("correct")
    corr_parser.add_argument("--memory", required=False, default="state/memory.json")
    corr_parser.add_argument("--phrase", required=True)
    corr_parser.add_argument("--issue", required=True)
    corr_parser.add_argument("--adjustment-ms", type=int, required=True)

    args = parser.parse_args()

    if args.command == "cut":
        # Auto-generate timings and transcript if not provided manually
        if not args.transcript or not args.timings:
            print(f"Generating transcript and timings for {args.video} using Whisper...")
            args.transcript, args.timings = generate_transcripts(args.video)

        transcript = load_json_file(args.transcript, "Transcript")
        timings = load_json_file(args.timings, "Timings")

        memory = load_memory(args.memory)
        save_memory(args.memory, memory)

        agent = PhraseCutAgent(memory)
        result = agent.run(
            phrase=args.phrase,
            transcript_data=transcript,
            timing_data=timings,
            video_path=args.video,
            output_path=args.output,
        )

        save_memory(args.memory, memory)

        # Raw JSON print and redundant summary text removed! 
        # The agent.run() method now cleanly outputs the ASCII timeline and summary table.

    elif args.command == "correct":
        memory = load_memory(args.memory)
        memory = apply_correction(memory, args.phrase, args.issue, args.adjustment_ms)
        save_memory(args.memory, memory)


if __name__ == "__main__":
    main()