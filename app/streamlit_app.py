import sys
import os
from pathlib import Path

# Automatically add the project root directory (parent of 'app') to Python's path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st
import json

# Import your actual backend agent class
from app.agent import PhraseCutAgent

st.set_page_config(
    page_title="Stateful Phrase Cutter Agent",
    page_icon="🎬",
    layout="wide"
)

# Sidebar Configuration
st.sidebar.title("⚙️ Agent Controls")
st.sidebar.markdown("Configure alignment strictness and conflict arbitration policies.")

confidence_threshold = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.85, 0.05)
enable_stateful_memory = st.sidebar.checkbox("Enable Stateful Memory & Learning", value=True)
debug_mode = st.sidebar.checkbox("Verbose Audit Logging", value=True)

st.title("🎬 Stateful Phrase Cutter Agent")
st.markdown(
    "An intelligent multi-source alignment agent that reconciles speech timing data and transcripts "
    "to isolate precise video phrases, resolving contractions, filler words, and timing drift."
)

tabs = st.tabs(["🚀 Live Execution", "📂 Pre-loaded Test Cases", "📊 Architecture & Logs"])

with tabs[0]:
    st.header("Interactive Video Phrase Cutter")
    
    col1, col2 = st.columns(2)
    
    with col2:
        st.markdown("### Quick Preset Loader")
        preset_choice = st.selectbox(
            "Select Evaluation Test Case",
            ["Test Case 1: Filler Words ('I think we should wait here')"]
        )
        
    # Determine default values based on preset choice *before* rendering the text input widget
    default_phrase = ""
    default_video_path = None
        
    if "Test Case 1" in preset_choice:
        default_phrase = "I think we should wait here"
        default_video_path = "data/sample_case_1/filler.mp4"
    elif "Test Case 2" in preset_choice:
        default_phrase = "this is"
        default_video_path = "data/sample_case_2/contraction.mp4"

    with col1:
        uploaded_video = st.file_uploader("Upload Source Video (.mp4)", type=["mp4"])
        target_phrase = st.text_input("Target Phrase to Isolate", value=default_phrase, placeholder="e.g., can't stop")

    if st.button("✂️ Run Agent Alignment & Cut Video", type="primary"):
        # Determine video path and associated test case files
        if uploaded_video is not None:
            os.makedirs("outputs", exist_ok=True)
            temp_video_path = os.path.join("outputs", uploaded_video.name)
            with open(temp_video_path, "wb") as f:
                f.write(uploaded_video.getbuffer())
            video_source = temp_video_path
            raw_phrase = target_phrase
            
            transcript_path = "data/sample_case_1/transcript.json"
            timing_path = "data/sample_case_1/timings.json"
        else:
            video_source = default_video_path
            raw_phrase = target_phrase
            if "Test Case 1" in preset_choice:
                case_dir = "data/sample_case_1"
            else:
                case_dir = "data/sample_case_2"
            transcript_path = os.path.join(case_dir, "transcript.json")
            timing_path = os.path.join(case_dir, "timings.json")
        
        # Sanitize phrase to prevent smart quote or spacing desyncs between UI and backend
        phrase_to_cut = raw_phrase.strip().replace("’", "'").replace("‘", "'")
        
        if not video_source or not phrase_to_cut:
            st.error("Please provide a valid video file and target phrase.")
        else:
            with st.spinner("Agent running multi-source alignment, conflict arbitration, and video slicing..."):
                try:
                    # Load transcript and timing data files
                    with open(transcript_path, "r", encoding="utf-8") as f:
                        transcript_data = json.load(f)
                    with open(timing_path, "r", encoding="utf-8") as f:
                        timing_data = json.load(f)
                        
                    # Initialize agent with safe memory handling
                    memory_path = "state/memory.json"
                    memory = {"preferences": {}}
                    if os.path.exists(memory_path):
                        try:
                            from app.memory import load_memory
                            memory = load_memory(memory_path)
                        except Exception:
                            pass
                            
                    agent = PhraseCutAgent(memory=memory)
                    
                    # Define dynamic output path for the cut clip
                    safe_filename = phrase_to_cut.lower().replace(" ", "_").replace("'", "")
                    output_clip_path = os.path.join("outputs", f"isolated_{safe_filename}.mp4")
                    
                    # Execute actual agent run pipeline
                    result = agent.run(
                        phrase=phrase_to_cut,
                        transcript_data=transcript_data,
                        timing_data=timing_data,
                        video_path=video_source,
                        output_path=output_clip_path
                    )
                    
                    st.success("✅ Alignment successful! Cut video generated successfully.")
                    
                    # Display metrics from actual result
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Match Confidence", f"{result.log['boundary_decision']['confidence']*100:.1f}%")
                    m2.metric("Edge Source", result.log['boundary_decision']['trusted_source_for_edges'])
                    m3.metric("Output Duration", f"{result.end_time - result.start_time:.2f}s", f"Frames: {result.start_frame} - {result.end_frame}")
                    
                    # Playback the actual cut video output!
                    st.markdown("### 🎬 Isolated Video Output")
                    if result.output_path and os.path.exists(result.output_path):
                        st.video(result.output_path)
                        with open(result.output_path, "rb") as file:
                            st.download_button(
                                label="📥 Download Cut MP4 Clip",
                                data=file,
                                file_name=os.path.basename(result.output_path),
                                mime="video/mp4"
                            )
                    else:
                        st.warning("Video cutting completed, but output file path could not be resolved.")
                        
                    st.markdown("### 📋 Agent Decision & Conflict Log")
                    st.json(result.log)
                    
                except Exception as e:
                    st.error(f"An error occurred during agent execution: {e}")

with tabs[1]:
    st.header("Built-in Edge Case Test Suite")
    st.markdown("Review how the agent handles complex linguistic and timing anomalies out of the box.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Test Case 1: Filler Words")
        st.markdown("**Input:** `Hi everyone, um... I think we should wait here.`")
        st.info("Agent successfully filters conversational fillers from the timing stream to prevent dead air in the final clip.")
        if os.path.exists("data/sample_case_1/filler.mp4"):
            st.video("data/sample_case_1/filler.mp4")
            
    with col_b:
        st.subheader("Test Case 2: Split Contractions")
        st.markdown("**Input:** `We can't stop here. This is backcountry`")
        st.info("Agent resolves token splitting across timing boundaries (`[ ca ]` and `[ n't ]`) for high-confidence matching.")
        if os.path.exists("data/sample_case_2/contraction.mp4"):
            st.video("data/sample_case_2/contraction.mp4")

with tabs[2]:
    st.header("Architecture & Audit Logs")
    st.markdown("Inspect persistent JSON audit logs generated by the agent during past executions.")
    logs_dir = Path("logs")
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.json"))
        if log_files:
            selected_log = st.selectbox("Select Log File", log_files)
            if selected_log:
                with open(selected_log, "r") as f:
                    st.json(json.load(f))
        else:
            st.info("No audit logs found yet. Run an agent execution to generate logs.")
    else:
        st.info("Logs directory not initialized.")