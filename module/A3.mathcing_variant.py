# %%
import pandas as pd
import numpy as np
import dask.dataframe as dd
import logging
from finding_ref_seq import Finding_Reference_Seq
import argparse

# ============================
# Logging 설정 (SLURM-friendly)
# ============================
logging.basicConfig(
    filename="variant_matching.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ============================
# Argument parser
# ============================
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", type=str, required=True)
    parser.add_argument("--variant_dict_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    return parser.parse_args()

# ============================
# Prepare variant dictionary
# ============================
def prepare_variant(variant_dict_path):
    variant_df = pd.read_table(variant_dict_path)
    variant_df = variant_df.dropna(subset=['seq'])
    variant_df = variant_df[variant_df['seq'].apply(lambda x: isinstance(x, str))]
    variant_df["seq"] = variant_df["seq"].apply(lambda x: x[25:175])
    return variant_df

# ============================
# Levenshtein matching logic
# ============================
def find_reference_seq(var, finder):
    try:
        founded_dict = finder.find_similar_sequences(var)
        sorted_items = sorted(founded_dict.items(), key=lambda x: x[1])
        first_key, first_val = sorted_items[0]
        if len(sorted_items) > 1 and sorted_items[1][1] == first_val:
            return np.nan, np.nan
        else:
            return first_key, first_val
    except Exception as e:
        logging.warning(f"Failed to match variant: {var} — {e}")
        return np.nan, np.nan

def process_partition(df, finder, name_dict):
    df = df.copy()
    df[["matched_var", "matched_score"]] = df["var"].apply(lambda x: pd.Series(find_reference_seq(x, finder)))
    df["var_name"] = df["matched_var"].map(name_dict)
    return df

# ============================
# Main logic
# ============================
def main():
    args = parse_args()
    logging.info("🔍 Starting variant matching pipeline...")

    # Load variant reference
    logging.info(f"📂 Loading variant dictionary from {args.variant_dict_path}")
    variant_df = prepare_variant(args.variant_dict_path)
    name_dict = dict(zip(variant_df["seq"], variant_df["names"]))

    # Load reference sequences
    logging.info("📌 Loading reference sequences into matcher")
    finder = Finding_Reference_Seq()
    finder.load_reference_sequences(variant_df.seq.values)

    # Load input CSV using Dask
    logging.info(f"📥 Reading input data from {args.data_path}")
    ddf = dd.read_csv(args.data_path, blocksize="32MB")

    # Define Dask meta to avoid progress bar inference
    meta = pd.DataFrame({
        "read_id": pd.Series(dtype="str"),
        "var": pd.Series(dtype="str"),
        "bc": pd.Series(dtype="str"),
        "var_len": pd.Series(dtype="float"),
        "bc_len": pd.Series(dtype="float"),
        "matched_var": pd.Series(dtype="str"),
        "matched_score": pd.Series(dtype="float"),
        "var_name": pd.Series(dtype="str")
    })

    # Process with Dask
    logging.info("⚙️  Processing partitions...")
    result_ddf = ddf.map_partitions(
        lambda df: process_partition(df, finder, name_dict),
        meta=meta
    )

    result_df = result_ddf.compute()
    logging.info("✅ Dask computation complete")

    # Save to output
    logging.info(f"💾 Saving result to {args.output_path}")
    result_df.to_csv(args.output_path, index=False)

    logging.info("🎉 Processing completed successfully.")

# ============================
# Entry point
# ============================
if __name__ == "__main__":
    main()