# %%
import dask.dataframe as dd
import logging
import dask.dataframe as dd
import argparse
from collections import Counter


args = argparse.ArgumentParser(description="Process and filter barcode data.")
args.add_argument("--input_path", type=str, required=True, help="Path to the input CSV file.")
args.add_argument("--output_barcode_path", type=str, required=True, help="Path to save the barcode statistics CSV file.")
args.add_argument("--output_variant_path", type=str, required=True, help="Path to save the variant statistics CSV file.")
args.add_argument("--output_bcmapping_path", type=str, required=True, help="Path to save the barcode mapping CSV file.")
args = args.parse_args()

# Configure logging
working_dir = "/proj/hyejunglab/MPRA/RNAseq/SCZ/scMPRA/Alejandro_Nanopore_BC_Mapping_viral_mapping"
log_file = f"{working_dir}/result/log_file.txt"
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

# Load data
data = dd.read_csv(args.input_path, dtype={"var_name": str, "bc": str, "matched_score": float})

# Initial number of rows
n0 = data.shape[0].compute()
logging.info(f"Initial number of rows: {n0}")

# Filter: matched_score < 15
data = data[data["matched_score"] < 5]
n1 = data.shape[0].compute()
logging.info(f"Number of rows after filtering Levenshtein Distance < 15: {n1}")

# Barcode statistics
bc_stat = data.groupby("bc")["var_name"].agg(list).reset_index().compute()
bc_stat["num_unique"] = bc_stat["var_name"].apply(lambda x: len(set(x)))
bc_stat["num_total"] = bc_stat["var_name"].apply(lambda x: len(x))
bc_stat["most_common"] = bc_stat["var_name"].apply(lambda x: Counter(x).most_common(1)[0][0] if x else None)
bc_stat["most_common_count"] = bc_stat["var_name"].apply(lambda x: Counter(x).most_common(1)[0][1] if x else 0)
bc_stat["most_common_count"] = bc_stat["most_common_count"].astype(int)
bc_stat["second_most_common"] = bc_stat["var_name"].apply(lambda x: Counter(x).most_common(2)[1][0] if len(Counter(x).most_common(2)) > 1 else None)
bc_stat["second_most_common_count"] = bc_stat["var_name"].apply(lambda x: Counter(x).most_common(2)[1][1] if len(Counter(x).most_common(2)) > 1 else 0)
bc_stat["second_most_common_count"] = bc_stat["second_most_common_count"].astype(int)
bc_stat["most_common_percent"] = bc_stat["most_common_count"] / bc_stat["num_total"]
bc_stat["second_most_common_percent"] = bc_stat["second_most_common_count"] / bc_stat["num_total"]
bc_stat["helper"] = bc_stat["most_common_count"]/bc_stat["second_most_common_count"]
bc_stat_filtered = bc_stat[(bc_stat["helper"]>=3.0) & bc_stat["num_total"] >= 3]
bc_stat_filtered.to_csv(args.output_barcode_path, index=False)
bc_stat_filtered[["bc","most_common"]].to_csv(args.output_bcmapping_path, index=False)
logging.info("Saved barcode statistics")

# Variant statistics
var_stat = bc_stat_filtered[["bc","most_common"]].groupby("most_common").agg(list).compute()
var_stat["num_barcodes_unique"] = var_stat["bc"].apply(lambda x: len(set(x)))
var_stat.to_csv(args.output_variant_path, index=False)
logging.info("Saved variant statistics")

