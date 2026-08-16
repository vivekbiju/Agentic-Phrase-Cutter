import json
import subprocess
from typing import Optional, Tuple


def probe_fps(video_path: str) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=r_frame_rate",
        "-of",
        "json",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    
    streams = data.get("streams", [])
    if not streams:
        raise ValueError(f"No video streams found in {video_path}")
        
    rate = streams[0].get("r_frame_rate", "30/1")
    if "/" in rate:
        num, den = rate.split("/")
        float_den = float(den)
        if float_den == 0:
            return 30.0  # Fallback default
        return float(num) / float(float_den)
    return float(rate)


def times_to_frames(start_time: float, end_time: float, fps: float) -> Tuple[int, int]:
    return round(start_time * fps), round(end_time * fps)


def has_audio_stream(video_path: str) -> bool:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=codec_type",
        "-of",
        "json",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        return len(data.get("streams", [])) > 0
    except Exception:
        return False


def cut_video(
    input_path: str,
    output_path: str,
    start_time: float,
    end_time: float,
) -> Optional[str]:
    if start_time < 0:
        raise ValueError("start_time cannot be negative")
    if end_time <= start_time:
        raise ValueError("end_time must be greater than start_time")

    has_audio = has_audio_stream(input_path)

    vf = f"trim=start={start_time:.3f}:end={end_time:.3f},setpts=PTS-STARTPTS"
    cmd = [
    "ffmpeg", "-y", "-i", input_path,
    "-vf", vf,
    "-c:v", "libx264", 
    "-preset", "veryfast", # Speeds up encoding
    "-crf", "23"           # Maintains good visual quality
]

    if has_audio:
        af = f"atrim=start={start_time:.3f}:end={end_time:.3f},asetpts=PTS-STARTPTS"
        cmd.extend(["-af", af, "-c:a", "aac"])
    else:
        cmd.append("-an")

    cmd.append(output_path)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")

    return output_path