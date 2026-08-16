import re
from typing import List, Dict, Any
from app.schemas import NormalizedToken, WordTiming

FILLER_WORDS = {"um", "uh", "erm", "ah", "mm", "hmm"}

CONTRACTION_MAP = {
    "don't": ["do", "n't"],
    "can't": ["ca", "n't"],
    "won't": ["wo", "n't"],
    "i'm": ["i", "'m"],
    "it's": ["it", "'s"],
    "we're": ["we", "'re"],
    "they're": ["they", "'re"],
    "didn't": ["did", "n't"],
    "isn't": ["is", "n't"],
    "that's": ["that", "'s"],
}


def normalize_token(token: str) -> str:
    token = token.lower().strip()
    token = token.replace("’", "'")
    token = re.sub(r"^[^\w']+|[^\w']+$", "", token)
    return token


def tokenize_text(text: str) -> List[str]:
    text = text.replace("’", "'")
    raw = re.findall(r"\b[\w']+\b", text.lower())
    return raw


def expand_contraction(token: str) -> List[str]:
    t = normalize_token(token)
    return CONTRACTION_MAP.get(t, [t])


def normalize_query(phrase: str) -> List[NormalizedToken]:
    tokens = []
    idx = 0
    for raw in tokenize_text(phrase):
        for part in expand_contraction(raw):
            tokens.append(
                NormalizedToken(
                    original=raw,
                    normalized=part,
                    source="query",
                    index=idx,
                    is_filler=part in FILLER_WORDS,
                )
            )
            idx += 1
    return tokens


def normalize_transcript(transcript_data: Dict[str, Any]) -> List[NormalizedToken]:
    if "text" in transcript_data:
        text = transcript_data["text"]
    elif "segments" in transcript_data:
        text = " ".join(seg["text"] for seg in transcript_data["segments"])
    else:
        raise ValueError("Transcript must contain 'text' or 'segments'.")

    tokens = []
    idx = 0
    for raw in tokenize_text(text):
        for part in expand_contraction(raw):
            tokens.append(
                NormalizedToken(
                    original=raw,
                    normalized=part,
                    source="transcript",
                    index=idx,
                    is_filler=part in FILLER_WORDS,
                )
            )
            idx += 1
    return tokens


def normalize_timings(words: List[Dict[str, Any] | WordTiming]) -> List[NormalizedToken]:
    tokens = []
    idx = 0
    for item in words:
        word = item.word if hasattr(item, "word") else item["word"]
        start = item.start if hasattr(item, "start") else item["start"]
        end = item.end if hasattr(item, "end") else item["end"]
        conf = item.confidence if hasattr(item, "confidence") else item.get("confidence")

        raw_norm = normalize_token(word)
        parts = expand_contraction(raw_norm)

        if len(parts) == 1:
            tokens.append(
                NormalizedToken(
                    original=word,
                    normalized=parts[0],
                    source="timing",
                    index=idx,
                    start=float(start),
                    end=float(end),
                    confidence=conf,
                    is_filler=parts[0] in FILLER_WORDS,
                )
            )
            idx += 1
        else:
            span = float(end) - float(start)
            part_len = span / len(parts)
            for i, part in enumerate(parts):
                tokens.append(
                    NormalizedToken(
                        original=word,
                        normalized=part,
                        source="timing",
                        index=idx,
                        start=float(start) + i * part_len,
                        end=float(start) + (i + 1) * part_len,
                        confidence=conf,
                        is_filler=part in FILLER_WORDS,
                    )
                )
                idx += 1

    return tokens
