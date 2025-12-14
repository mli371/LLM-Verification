import sys
import os
import argparse
from typing import List

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from llm_verification.collector import collect_openai, save_jsonl
from llm_verification.analyzer_benford import extract_numbers_from_text, first_digits, benford_chi_squared

def main():
    parser = argparse.ArgumentParser(description="Run temperature comparison experiment")
    parser.add_argument('--prompts', type=str, default='prompts/finance_prompts.txt', help='Path to prompts file')
    parser.add_argument('--model', type=str, default='gpt-4o', help='Model to use')
    parser.add_argument('--out', type=str, default='outputs/temperature_experiment.csv', help='Output CSV summary')
    parser.add_argument('--dry-run', action='store_true', help='Dry run without API calls')
    args = parser.parse_args()

    # Define temperatures to test
    temperatures = [0.1, 0.7, 1.5]
    
    # Load prompts (using a few hardcoded defaults if file not present/empty for demo)
    prompts = [
        "Generate a list of 100 random transaction amounts for a grocery store.",
        "Create a table of 50 fictional stock prices.",
        "List the populations of 50 imaginary cities."
    ]
    
    if os.path.exists(args.prompts):
        with open(args.prompts, 'r') as f:
            file_prompts = [l.strip() for l in f if l.strip()]
        if file_prompts:
            prompts = file_prompts

    print(f"Starting experiment with {len(prompts)} prompts across temperatures: {temperatures}")
    
    all_results = []
    
    import pandas as pd
    
    for temp in temperatures:
        print(f"Collecting for temperature={temp}...")
        results = collect_openai(prompts, model=args.model, temperature=temp, dry_run=args.dry_run)
        
        # Analyze immediately
        for res in results:
            text = res.get('response')
            if not text:
                continue
                
            nums = extract_numbers_from_text(text)
            fd = first_digits(nums)
            chi2 = None
            p_val = None
            if len(fd) >= 10:
                chi2, p_val, _, _ = benford_chi_squared(fd)
            
            all_results.append({
                "temperature": temp,
                "prompt": res['prompt'][:50] + "...",
                "n_numbers": len(nums),
                "chi2": chi2,
                "p_value": p_val
            })

    # Save summary
    df = pd.DataFrame(all_results)
    print("\nExperiment Results Summary:")
    print(df.groupby("temperature")[["chi2", "p_value"]].mean())
    
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"\nSaved detailed results to {args.out}")

if __name__ == "__main__":
    main()
