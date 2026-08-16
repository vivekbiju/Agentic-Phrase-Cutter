# app/transcribe.py
import whisper
import json
import os
from typing import Tuple
import warnings

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

def generate_transcripts(video_path: str, output_dir: str = "outputs") -> Tuple[str, str]:
    """
    Extracts audio from video and uses a local Whisper model to generate
    both the plain text transcript and word-level timings.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the base model (good balance of speed and accuracy for local CPU/GPU execution)
    model = whisper.load_model("base")
    
    # Run inference with word-level timestamps enabled
    result = model.transcribe(video_path, word_timestamps=True)
    
    # 1. Format and save the plain transcript
    transcript_data = {
        "text": result["text"].strip()
    }
    transcript_path = os.path.join(output_dir, "transcript.json")
    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump(transcript_data, f, indent=2)
        
    # 2. Format and save the word-level timings
    words_data = []
    for segment in result.get("segments", []):
        for word in segment.get("words", []):
            words_data.append({
                "word": word["word"].strip(),
                "start": word["start"],
                "end": word["end"],
                "confidence": word.get("probability", 1.0)
            })
            
    timings_data = {"words": words_data}
    timings_path = os.path.join(output_dir, "timings.json")
    with open(timings_path, "w", encoding="utf-8") as f:
        json.dump(timings_data, f, indent=2)
        
    return transcript_path, timings_path