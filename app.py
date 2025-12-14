import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import os
import sys

# Ensure local modules can be imported
sys.path.append(os.path.dirname(__file__))

from llm_verification.collector import collect_openai
from llm_verification.analyzer_benford import extract_numbers_from_text, first_digits, benford_chi_squared
from llm_verification.analyzer_zipf import zipf_stats

st.set_page_config(page_title="LLM Verifier", layout="wide")

st.title("LLM Verification Dashboard")
st.markdown("""
This dashboard verifies whether LLM-generated outputs conform to natural statistical laws:
- **Benford's Law**: Leading digits of numerical data often follow a logarithmic distribution.
- **Zipf's Law**: The frequency of words in natural language is inversely proportional to their rank.
""")

with st.sidebar:
    st.header("Configuration")
    
    # API Key handling
    env_key = os.getenv("OPENAI_API_KEY")
    api_key_input = st.text_input("OpenAI API Key", type="password", value=env_key if env_key else "", help="Required for data collection")
    if api_key_input:
        os.environ["OPENAI_API_KEY"] = api_key_input
    
    model = st.selectbox("Model", ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
    
    # Temperature is now supported
    temperature = st.slider("Temperature", 0.0, 2.0, 1.0, help="Values > 1.2 may cause hallucinations or formatting errors.")
    
    st.subheader("Prompt Input")
    
    prompt_type = st.radio("Prompt Type", ["Numeric (Benford Focus)", "Text (Zipf Focus)", "Custom"], horizontal=True)
    
    if prompt_type == "Numeric (Benford Focus)":
        default_prompt = "Generate a list of 120 fictional invoice amounts for a hardware store, ranging from $5 to $500."
    elif prompt_type == "Text (Zipf Focus)":
        default_prompt = "Write a 500-word science fiction story about a robot discovering a flower."
    else:
        default_prompt = ""

    prompt = st.text_area("Enter Prompt", value=default_prompt, height=150)
    
    run_btn = st.button("Generate & Verify", type="primary")

if run_btn:
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("Please provide an OpenAI API Key in the sidebar.")
    else:
        with st.spinner(f"Requesting data from {model}..."):
            try:
                # Collect data with temperature
                results = collect_openai([prompt], model=model, temperature=temperature)
                
                if not results:
                    st.error("No results returned.")
                else:
                    record = results[0]
                    if record.get('error'):
                        st.error(f"API Error: {record['error']}")
                    else:
                        response_text = record.get('response', '')
                        
                        # --- Display Response ---
                        st.subheader("Generated Output")
                        st.text_area("Raw Response", response_text, height=200)
                        
                        # --- Analysis Section ---
                        stats_col1, stats_col2 = st.columns(2)
                        
                        # BENFORD ANALYSIS
                        with stats_col1:
                            st.markdown("### Benford's Law Analysis")
                            nums = extract_numbers_from_text(response_text)
                            st.caption(f"Found {len(nums)} numbers")
                            
                            if len(nums) < 10:
                                st.warning("Not enough numbers for reliable Benford analysis (need > 10).")
                            else:
                                fd = first_digits(nums)
                                chi2, p, counts, expected = benford_chi_squared(fd)
                                
                                # Metrics
                                m1, m2 = st.columns(2)
                                m1.metric("Chi-Square", f"{chi2:.2f}")
                                m2.metric("P-value", f"{p:.4f}", delta="Significant Deviation" if p < 0.05 else "Pass", delta_color="inverse")
                                
                                if p < 0.05:
                                    st.error("⚠️ **Significant Deviation Detected**: The generated numbers do not follow Benford's Law naturally.")
                                else:
                                    st.success("✅ **Pass**: The distribution conforms to Benford's Law.")
                                
                                # Plot
                                df_b = pd.DataFrame({
                                    "Digit": list(range(1, 10)),
                                    "Observed": counts,
                                    "Expected": expected
                                })
                                
                                fig_b = go.Figure()
                                fig_b.add_trace(go.Bar(x=df_b["Digit"], y=df_b["Observed"], name="Observed", marker_color='#636EFA'))
                                fig_b.add_trace(go.Scatter(x=df_b["Digit"], y=df_b["Expected"], name="Expected", line=dict(color='red', width=3)))
                                fig_b.update_layout(
                                    title="Leading Digit Distribution",
                                    xaxis_title="First Digit",
                                    yaxis_title="Count",
                                    height=400
                                )
                                st.plotly_chart(fig_b, use_container_width=True)

                        # ZIPF ANALYSIS
                        with stats_col2:
                            st.markdown("### Zipf's Law Analysis")
                            ranks, freqs, slope = zipf_stats([response_text])
                            
                            st.metric("Zipf Slope", f"{slope:.2f}", delta="Low Complexity" if slope > -0.8 else "Natural", delta_color="normal")
                            
                            if slope > -0.8:
                                st.info("ℹ️ **Flat Slope**: The text lacks natural language variety (likely a structured list).")
                            elif slope < -1.2:
                                st.info("ℹ️ **Steep Slope**: Vocabulary is very repetitive.")
                            else:
                                st.success("✅ **Natural**: Matches typical human language patterns.")
                            
                            if len(ranks) > 1:
                                df_z = pd.DataFrame({
                                    "Rank": ranks,
                                    "Frequency": freqs,
                                    "LogRank": np.log(ranks),
                                    "LogFreq": np.log(freqs)
                                })
                                
                                fig_z = px.scatter(df_z, x="LogRank", y="LogFreq", title="Word Frequency (Log-Log)", trendline="ols")
                                fig_z.update_layout(height=400)
                                st.plotly_chart(fig_z, use_container_width=True)
                            else:
                                st.warning("Not enough text for Zipf analysis.")

            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
