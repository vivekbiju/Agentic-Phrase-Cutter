from typing import List, Tuple
from app.schemas import NormalizedToken, AlignmentPair, Conflict


def find_subsequence(haystack: List[str], needle: List[str]) -> Tuple[int, int]:
    n = len(needle)
    for i in range(len(haystack) - n + 1):
        if haystack[i:i+n] == needle:
            return i, i + n
    return -1, -1


def align_transcript_to_timings(
    transcript_tokens: List[NormalizedToken],
    timing_tokens: List[NormalizedToken],
) -> List[AlignmentPair]:
    pairs: List[AlignmentPair] = []
    
    # Extract normalized strings for substring lookup
    t_norms = [t.normalized for t in transcript_tokens]
    w_norms = [w.normalized for w in timing_tokens]
    
    start_idx, end_idx = find_subsequence(w_norms, t_norms)
    
    if start_idx != -1:
        # Perfect subsequence match found; align them 1-to-1
        for i, t in enumerate(transcript_tokens):
            w = timing_tokens[start_idx + i]
            pairs.append(AlignmentPair(t, w, "match"))
    else:
        # Fallback to greedy alignment if direct subsequence fails
        j = 0
        for t in transcript_tokens:
            matched = False
            while j < len(timing_tokens):
                w = timing_tokens[j]
                if t.normalized == w.normalized:
                    pairs.append(AlignmentPair(t, w, "match"))
                    j += 1
                    matched = True
                    break
                if w.is_filler:
                    pairs.append(AlignmentPair(None, w, "insertion"))
                    j += 1
                    continue
                break
            if not matched:
                pairs.append(AlignmentPair(t, None, "deletion"))

        while j < len(timing_tokens):
            pairs.append(AlignmentPair(None, timing_tokens[j], "insertion"))
            j += 1

    return pairs


def detect_conflicts(alignment: List[AlignmentPair], boundary_threshold: float = 0.12) -> List[Conflict]:
    conflicts: List[Conflict] = []

    for pair in alignment:
        if pair.relation == "insertion" and pair.timing_token:
            conflicts.append(
                Conflict(
                    type="extra_token_in_timing",
                    details={
                        "token": pair.timing_token.original,
                        "normalized": pair.timing_token.normalized,
                        "start": pair.timing_token.start,
                        "end": pair.timing_token.end,
                    },
                    decision="ignored" if pair.timing_token.is_filler else "review",
                    reason="Timing contains a token absent from transcript; filler tokens are ignored for phrase boundaries."
                    if pair.timing_token.is_filler
                    else "Non-filler token exists in timing but not transcript.",
                )
            )

        elif pair.relation == "deletion" and pair.transcript_token:
            conflicts.append(
                Conflict(
                    type="missing_token_in_timing",
                    details={
                        "token": pair.transcript_token.original,
                        "normalized": pair.transcript_token.normalized,
                    },
                    decision="fallback_to_neighboring_alignment",
                    reason="Transcript token missing in timing output.",
                )
            )

    return conflicts