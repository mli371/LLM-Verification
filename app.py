import streamlit as st
import pandas as pd
import json
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
    
    st.markdown("---")
    with st.expander("ℹ️ About the Laws"):
        st.markdown("""
        **Benford's Law**: 
        In organic numerical datasets, the leading digit $d$ ($d \\in \\{1, \dots, 9\\}$) occurs with probability:
        $$P(d) = \\log_{10}(1 + \\frac{1}{d})$$
        
        **Zipf's Law**:
        In natural language using a consistent vocabulary, the frequency of a word is inversely proportional to its rank:
        $$f(r) \\propto \\frac{1}{r}$$
        """)

    st.subheader("Prompt Input")
    
    prompt_type = st.radio("Prompt Type", ["Numeric (Benford Focus)", "Text (Zipf Focus)", "Custom"], horizontal=True)
    
    if prompt_type == "Numeric (Benford Focus)":
        default_prompt = "Generate a list of 500 fictional invoice amounts for a hardware store, including a mix of single-digit, double-digit, and triple-digit values ($1 to $999). Do NOT use numbered lists. Just output the amounts separated by spaces or commas."
    elif prompt_type == "Text (Zipf Focus)":
        default_prompt = "Write a 2000-word science fiction story about a robot discovering a flower."
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
                        
                        # Define flags for which analysis to run
                        run_benford = (prompt_type == "Numeric (Benford Focus)" or prompt_type == "Custom")
                        run_zipf = (prompt_type == "Text (Zipf Focus)" or prompt_type == "Custom")
                        
                        # Initialize report data
                        benford_data = None
                        zipf_data = None

                        if run_benford:
                            st.markdown("### Benford's Law Analysis")
                            nums = extract_numbers_from_text(response_text)
                            st.caption(f"Found {len(nums)} numbers")
                            
                            if len(nums) == 0:
                                st.error("No numbers found in the text.")
                            else:
                                fd = first_digits(nums)
                                chi2, p, counts, expected = benford_chi_squared(fd)
                                
                                # Store for report
                                benford_data = {"chi2": float(chi2), "p_value": float(p)}

                                if len(nums) < 50:
                                    st.warning(f"⚠️ **Inconclusive (Small Sample)**: Found only {len(nums)} numbers. Benford's Law requires N > 50 for valid results.")
                                    m1, m2 = st.columns(2)
                                    m1.metric("Chi-Square", f"{chi2:.2f}")
                                    m2.metric("P-value", f"{p:.4f}", help="Low confidence due to small sample size")
                                else:
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

                        if run_zipf:
                            if run_benford: st.markdown("---") # Separator if both are shown
                            st.markdown("### Zipf's Law Analysis")
                            
                            # Check if text has enough words
                            words = response_text.split()
                            if len(words) < 50:
                                st.warning("Not enough text content for Zipf analysis (mostly numbers).")
                                slope, r2 = 0.0, 0.0 # Default dummy values
                            else:
                                ranks, freqs, slope, r2 = zipf_stats([response_text])
                                total_words = sum(freqs)
                                
                                # Store for report
                                zipf_data = {"slope": float(slope), "r_squared": float(r2)}
                                
                                c1, c2, c3 = st.columns(3)
                                c1.metric("Zipf Slope", f"{slope:.2f}")
                                c2.metric("Fit (R²)", f"{r2:.2f}")
                                c3.metric("Word Count", f"{len(words)}")

                                if total_words < 500:
                                    st.warning(f"⚠️ **Inconclusive**: Text too short ({total_words} words). Need >500 words.")
                                elif r2 < 0.90:
                                    st.warning(f"⚠️ **Weak Power-Law Fit**: The distribution isn't Zipfian (R²={r2:.2f} < 0.90).")
                                elif slope > -0.8:
                                    st.info("ℹ️ **Flat Slope**: Lack of vocabulary hierarchy (too uniform).")
                                elif slope < -1.2:
                                    st.info("ℹ️ **Steep Slope**: Vocabulary is too repetitive.")
                                else:
                                    st.success("✅ **Pass**: Natural linguistic structure detected.")
                                
                                if len(ranks) > 1:
                                    df_z = pd.DataFrame({
                                        "LogRank": np.log(ranks),
                                        "LogFreq": np.log(freqs)
                                    })
                                    
                                    fig_z = px.scatter(df_z, x="LogRank", y="LogFreq", title="Word Frequency (Log-Log)")
                                    
                                    # Add regression line
                                    x_range = np.linspace(min(df_z["LogRank"]), max(df_z["LogRank"]), 100)
                                    y_pred = slope * x_range + (np.mean(df_z["LogFreq"]) - slope * np.mean(df_z["LogRank"]))
                                    fig_z.add_trace(go.Scatter(x=x_range, y=y_pred, mode='lines', name='Fit'))
                                    
                                    st.plotly_chart(fig_z, use_container_width=True)
                                else:
                                    st.warning("Not enough text for Zipf analysis.")
                        
                        # --- Export Section ---
                        st.markdown("---")
                        report_data = {
                            "model": model,
                            "temperature": temperature,
                            "prompt_preview": prompt[:50] + "...",
                            "benford_stats": benford_data,
                            "zipf_stats": zipf_data,
                            "generated_text_length": len(response_text)
                        }
                        st.download_button(
                            label="📥 Download Analysis Report (JSON)",
                            data=json.dumps(report_data, indent=4),
                            file_name="llm_verification_report.json",
                            mime="application/json"
                        )

            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
