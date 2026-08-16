def print_ascii_timeline(phrase: str, timing_tokens, matched_start_idx: int, matched_end_idx: int, confidence: float):
    """
    Generates a clean, aligned ASCII timeline visualization without emojis for the terminal demo.
    """
    print("\n" + "=" * 65)
    print(f" AGENT ALIGNMENT & TIMING TIMELINE: '{phrase}'")
    print("=" * 65)
    
    if not timing_tokens:
        print("No timing tokens available for visualization.")
        return

    # Slice a clean display window around the matched tokens
    window_start = max(0, matched_start_idx - 1)
    window_end = min(len(timing_tokens), matched_end_idx + 2)
    
    # Build aligned strings neatly
    tokens_row = "Words:    "
    times_row =  "Time(s):  "
    
    for i in range(window_start, window_end):
        tok = timing_tokens[i]
        word = tok.normalized
        timestamp_str = f"{tok.start:.2f}s"
        
        # Pad columns dynamically so they align cleanly
        max_len = max(len(word), len(timestamp_str))
        padded_word = word.center(max_len + 2)
        padded_time = timestamp_str.center(max_len + 2)
        
        if matched_start_idx <= i < matched_end_idx:
            tokens_row += f"[{padded_word}] "
        else:
            tokens_row += f" {padded_word}  "
            
        times_row += f" {padded_time}  "

    print(times_row)
    print(tokens_row)
    print("-" * 65)
    print(f" Confidence Score : {confidence * 100:.0f}%")
    status_text = "High Confidence Match" if confidence >= 0.7 else "Fallback Triggered"
    print(f" Status           : {status_text}")
    print("=" * 65 + "\n")

def print_decision_table(start_time: float, end_time: float, start_word: str, end_word: str, start_frame: int, end_frame: int, output_path: str, reasoning: str):
    """
    Prints a clean, perfectly aligned summary table of the agent's decision metrics.
    """
    print("┌───────────────────────────────────────────────────────────┐")
    print("│               AGENT EXECUTION & CUT SUMMARY               │")
    print("├───────────────────────────────────────────────────────────┤")
    
    rows = [
        f"Target Boundaries : {start_time:.3f}s -> {end_time:.3f}s",
        f"Matched Words     : '{start_word}' -> '{end_word}'",
        f"Frame Range       : Frames {start_frame} to {end_frame}",
        f"Output Path       : {output_path}"
    ]
    
    for row in rows:
        print(f"│ {row:<57} │")
        
    print("├───────────────────────────────────────────────────────────┤")
    print("│ Decision Logic:                                           │")
    
    # Wrap long reasoning text cleanly within the box width
    words = reasoning.split()
    line = "  "
    for word in words:
        if len(line) + len(word) + 1 > 55:
            print(f"│ {line:<57} │")
            line = "  " + word + " "
        else:
            line += word + " "
    if line.strip() != "":
        print(f"│ {line:<57} │")
        
    print("└───────────────────────────────────────────────────────────┘\n")