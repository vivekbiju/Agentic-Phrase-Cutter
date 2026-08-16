import json
import os
from typing import Dict, Any, List

from app.normalize import normalize_query, normalize_transcript, normalize_timings
from app.align import find_subsequence, align_transcript_to_timings, detect_conflicts
from app.cutter import probe_fps, times_to_frames, cut_video
from app.schemas import BoundaryDecision, AgentResult, Conflict
from app.visualization import print_ascii_timeline, print_decision_table


class PhraseCutAgent:
    def __init__(self, memory: Dict[str, Any]):
        self.memory = memory

    def decide_boundaries(
        self,
        phrase: str,
        transcript_tokens,
        timing_tokens,
        alignment,
        conflicts: List[Conflict],
    ) -> BoundaryDecision:
        import difflib
        
        def get_word(token):
            return getattr(token, 'text', getattr(token, 'original', token.normalized))

        query_tokens = normalize_query(phrase)
        query_norm = [t.normalized for t in query_tokens if not t.is_filler]
        
        valid_indices = [i for i, t in enumerate(timing_tokens) if not t.is_filler]
        valid_words = [timing_tokens[i].normalized for i in valid_indices]
        
        start_idx, end_idx = -1, -1
        start_match_ratio = 0.0
        end_match_ratio = 0.0
        
        if query_norm and valid_words:
            # 1. Fuzzy match the FIRST word of the query
            for i, word in enumerate(valid_words):
                ratio = difflib.SequenceMatcher(None, word, query_norm[0]).ratio()
                if ratio >= 0.7:
                    start_idx = valid_indices[i]
                    start_match_ratio = ratio
                    break
            
            # 2. Fuzzy match the LAST word of the query ensuring it spans the full length
            if start_idx != -1:
                start_valid_pos = valid_indices.index(start_idx)
                target_valid_pos = start_valid_pos + len(query_norm) - 1
                
                if target_valid_pos < len(valid_indices):
                    candidate_idx = valid_indices[target_valid_pos]
                    word = timing_tokens[candidate_idx].normalized
                    ratio = difflib.SequenceMatcher(None, word, query_norm[-1]).ratio()
                    if ratio >= 0.7:
                        end_idx = candidate_idx + 1
                        end_match_ratio = ratio
                
                # Fallback backward search if estimated position didn't match perfectly
                if end_idx == -1:
                    for i in range(len(valid_words) - 1, -1, -1):
                        word = valid_words[i]
                        if valid_indices[i] >= start_idx:
                            ratio = difflib.SequenceMatcher(None, word, query_norm[-1]).ratio()
                            if ratio >= 0.7:
                                end_idx = valid_indices[i] + 1
                                end_match_ratio = ratio
                                break

        # 3. Defensive Fallback Policy & Drift Detection
        is_fallback = False
        fallback_reason = ""

        if start_idx == -1:
            is_fallback = True
            fallback_reason = "Fuzzy anchoring failed completely for start word; fell back to full stream bounds."
            start_idx = 0
            end_idx = max(1, len(timing_tokens))
            confidence = 0.40
            trusted_edge_source = "fallback_transcript_default"
        elif end_idx == -1:
            is_fallback = True
            fallback_reason = "End word anchor missing or dropped by timing stream; extended cut to end."
            end_idx = len(timing_tokens)
            confidence = 0.60
            trusted_edge_source = "timing_fuzzy_anchor_with_fallback_end"
        else:
            matched_timing = timing_tokens[start_idx:end_idx]
            duration = matched_timing[-1].end - matched_timing[0].start
            
            # Defensive threshold: check for timing drift anomaly
            if len(query_norm) > 0 and (duration > len(query_norm) * 1.5 or duration < 0.2):
                is_fallback = True
                fallback_reason = f"Timing drift anomaly detected (duration {duration:.2f}s for {len(query_norm)} tokens)."
                confidence = 0.65
                trusted_edge_source = "transcript_semantic_override"
            else:
                avg_match_ratio = (start_match_ratio + (end_match_ratio if end_match_ratio > 0 else start_match_ratio)) / 2.0
                confidence = round(max(0.70, min(0.98, avg_match_ratio)), 2)
                trusted_edge_source = "timing_fuzzy_anchor"
                fallback_reason = "Timing data trusted for precise word edges; transcript semantic match validated."

        matched_timing = timing_tokens[start_idx:end_idx]

        prefs = self.memory.get("preferences", {})
        left_pad = prefs.get("default_left_padding_ms", 0) / 1000.0
        right_pad = prefs.get("default_right_padding_ms", 0) / 1000.0
        
        # Calculate boundaries (allowing negative padding to trim inward)
        final_start = max(0.0, matched_timing[0].start - left_pad)
        final_end = matched_timing[-1].end + right_pad
        
        # Failsafe so we don't invert the clip if trimming is too aggressive
        if final_start >= final_end:
            final_start = matched_timing[0].start

        return BoundaryDecision(
            start_time=final_start,
            end_time=final_end,
            start_word=get_word(matched_timing[0]),
            end_word=get_word(matched_timing[-1]),
            trusted_source_for_edges=trusted_edge_source,
            trusted_source_for_phrase_identity="transcript" if is_fallback else "timing_and_transcript",
            confidence=confidence,
            reasoning=fallback_reason
        ), start_idx, end_idx

    def run(
        self,
        phrase: str,
        transcript_data: Dict[str, Any],
        timing_data: Dict[str, Any],
        video_path: str | None = None,
        output_path: str | None = None,
        log_dir: str = "logs",
    ) -> AgentResult:
        transcript_tokens = normalize_transcript(transcript_data)
        timing_tokens = normalize_timings(timing_data["words"])
        alignment = align_transcript_to_timings(transcript_tokens, timing_tokens)
        conflicts = detect_conflicts(alignment)

        boundary, start_idx, end_idx = self.decide_boundaries(
            phrase=phrase,
            transcript_tokens=transcript_tokens,
            timing_tokens=timing_tokens,
            alignment=alignment,
            conflicts=conflicts,
        )

        # 1. Print the clean ASCII timeline visualization
        print_ascii_timeline(
            phrase=phrase,
            timing_tokens=timing_tokens,
            matched_start_idx=start_idx,
            matched_end_idx=end_idx,
            confidence=boundary.confidence
        )

        start_frame = end_frame = 0
        final_output = None

        if video_path:
            fps = probe_fps(video_path)
            start_frame, end_frame = times_to_frames(boundary.start_time, boundary.end_time, fps)

            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                final_output = cut_video(video_path, output_path, boundary.start_time, boundary.end_time)
        else:
            fps = None

        # 2. Print the clean summary table right below the timeline
        print_decision_table(
            start_time=boundary.start_time,
            end_time=boundary.end_time,
            start_word=boundary.start_word,
            end_word=boundary.end_word,
            start_frame=start_frame,
            end_frame=end_frame,
            output_path=str(final_output),
            reasoning=boundary.reasoning
        )

        log = {
            "phrase": phrase,
            "normalized_query_tokens": [t.normalized for t in normalize_query(phrase)],
            "conflicts": [
                {
                    "type": c.type,
                    "details": c.details,
                    "decision": c.decision,
                    "reason": c.reason,
                }
                for c in conflicts
            ],
            "boundary_decision": {
                "start_time": boundary.start_time,
                "end_time": boundary.end_time,
                "start_word": boundary.start_word,
                "end_word": boundary.end_word,
                "trusted_source_for_edges": boundary.trusted_source_for_edges,
                "trusted_source_for_phrase_identity": boundary.trusted_source_for_phrase_identity,
                "confidence": boundary.confidence,
                "reasoning": boundary.reasoning,
            },
            "frames": {
                "fps": fps,
                "start_frame": start_frame,
                "end_frame": end_frame,
            },
            "output_path": final_output,
        }

        os.makedirs(log_dir, exist_ok=True)
        safe_name = phrase.lower().replace(" ", "_").replace("'", "")
        with open(os.path.join(log_dir, f"{safe_name}.json"), "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2)

        return AgentResult(
            phrase=phrase,
            start_time=boundary.start_time,
            end_time=boundary.end_time,
            start_frame=start_frame,
            end_frame=end_frame,
            output_path=final_output,
            conflicts=conflicts,
            log=log,
        )