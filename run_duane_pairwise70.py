import os
import glob
from pathlib import Path
import numpy as np
import pandas as pd
import pyreadr

# Repo root = this file's directory. Keeps data/output paths portable (no
# hardcoded C:/ drive); override with the PAIRWISE70_ROOT env var if needed.
_ROOT = Path(os.environ.get("PAIRWISE70_ROOT", Path(__file__).resolve().parent))

def run_duane_analysis():
    rda_dir = _ROOT / "data"
    rda_files = sorted(glob.glob(str(rda_dir / "*.rda")))
    
    print(f"Found {len(rda_files)} RDA files in {rda_dir}")
    
    results = []
    
    for idx, rda_file in enumerate(rda_files):
        filename = Path(rda_file).name
        review_id = filename.replace("_data.rda", "").replace(".rda", "")
        
        try:
            r_data = pyreadr.read_r(rda_file)
            obj_name = list(r_data.keys())[0]
            df = r_data[obj_name]
            
            # Ensure required columns exist
            required = ['Experimental.cases', 'Experimental.N', 'Study.year']
            if not all(col in df.columns for col in required):
                continue
                
            # Filter and clean
            df = df.copy()
            df['Experimental.cases'] = pd.to_numeric(df['Experimental.cases'], errors='coerce')
            df['Experimental.N'] = pd.to_numeric(df['Experimental.N'], errors='coerce')
            df['Study.year'] = pd.to_numeric(df['Study.year'], errors='coerce')
            
            # Group by Analysis.number (and name if present)
            group_cols = []
            if 'Analysis.number' in df.columns:
                group_cols.append('Analysis.number')
            if 'Analysis.name' in df.columns:
                group_cols.append('Analysis.name')
                
            if not group_cols:
                # If no analysis grouping, treat whole file as one meta-analysis
                df['Analysis.number'] = 1
                df['Analysis.name'] = 'Overall'
                group_cols = ['Analysis.number', 'Analysis.name']
            elif len(group_cols) == 1:
                df['Analysis.name'] = 'Analysis ' + df['Analysis.number'].astype(str)
                group_cols = ['Analysis.number', 'Analysis.name']
                
            grouped = df.groupby(group_cols)
            
            for (analysis_num, analysis_name), group in grouped:
                # Clean group
                group = group.dropna(subset=['Experimental.cases', 'Experimental.N', 'Study.year'])
                group = group[group['Experimental.N'] > 0]
                
                if len(group) < 3:
                    continue
                
                # Sort chronologically
                group = group.sort_values('Study.year')
                
                # Compute cumulative metrics
                group['cum_N'] = group['Experimental.N'].cumsum()
                group['cum_cases'] = group['Experimental.cases'].cumsum()
                
                # Compute cumulative rate
                group['cum_rate'] = group['cum_cases'] / group['cum_N']
                
                # Filter out points with 0 events to allow log transforms
                valid_points = group[group['cum_cases'] > 0]
                
                if len(valid_points) < 3:
                    continue
                
                # Duane Regression: ln(cum_rate) = ln(lambda) - alpha * ln(cum_N)
                ln_X = np.log(valid_points['cum_N'].values)
                ln_Y = np.log(valid_points['cum_rate'].values)
                
                n = len(ln_X)
                sumX = np.sum(ln_X)
                sumY = np.sum(ln_Y)
                sumXY = np.sum(ln_X * ln_Y)
                sumXX = np.sum(ln_X * ln_X)
                
                denom = n * sumXX - sumX * sumX
                if abs(denom) < 1e-8:
                    continue
                    
                slope = (n * sumXY - sumX * sumY) / denom
                intercept = (sumY - slope * sumX) / n
                
                alpha = -slope
                beta = 1.0 - alpha
                lambd = np.exp(intercept)
                
                # R^2 calculation
                y_pred = slope * ln_X + intercept
                y_mean = np.mean(ln_Y)
                ss_tot = np.sum((ln_Y - y_mean) ** 2)
                ss_res = np.sum((ln_Y - y_pred) ** 2)
                r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
                
                results.append({
                    'review_id': review_id,
                    'analysis_number': analysis_num,
                    'analysis_name': analysis_name,
                    'k': len(group),
                    'total_N': group['cum_N'].iloc[-1],
                    'total_cases': group['cum_cases'].iloc[-1],
                    'beta': beta,
                    'lambda': lambd,
                    'r2': r2
                })
                
        except Exception as e:
            # Silently continue or print minimal details
            print(f"Error processing {filename}: {str(e)}")
            
    # Convert to DataFrame
    res_df = pd.DataFrame(results)
    out_path = _ROOT / "analysis" / "output" / "duane_pairwise70_results.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    res_df.to_csv(out_path, index=False)
    print(f"\nSaved {len(res_df)} Duane analysis results to {out_path}")
    
    # Print key insights
    if not res_df.empty:
        growth = res_df[res_df['beta'] < 1.0]
        deterioration = res_df[res_df['beta'] > 1.0]
        stable = res_df[res_df['beta'] == 1.0]
        
        print("\n=== Duane Reliability Growth Insights ===")
        print(f"Total Meta-Analyses analyzed: {len(res_df)}")
        print(f"Reliability Growth (beta < 1): {len(growth)} ({len(growth)/len(res_df)*100:.1f}%)")
        print(f"Safety Worsening   (beta > 1): {len(deterioration)} ({len(deterioration)/len(res_df)*100:.1f}%)")
        print(f"Stable/No growth   (beta = 1): {len(stable)} ({len(stable)/len(res_df)*100:.1f}%)")
        
        # Display top 5 safety growth and top 5 safety worsening reviews
        print("\n--- Top 5 Safety Growth Meta-Analyses (Lowest Beta) ---")
        print(growth.sort_values('beta').head(5)[['review_id', 'analysis_name', 'k', 'beta', 'r2']].to_string(index=False))
        
        print("\n--- Top 5 Safety Deterioration Meta-Analyses (Highest Beta) ---")
        print(deterioration.sort_values('beta', ascending=False).head(5)[['review_id', 'analysis_name', 'k', 'beta', 'r2']].to_string(index=False))

if __name__ == "__main__":
    run_duane_analysis()
