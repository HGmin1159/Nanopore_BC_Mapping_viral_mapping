# main.py
import pysam
import csv
import pandas as pd
import argparse
from dask.distributed import Client, LocalCluster
from dask.diagnostics import ProgressBar
from functools import partial

import dask.dataframe as dd

# ======================
# Sequence utilities
# ======================
def rev_comp_seq(seq):
    comp = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
    return ''.join(comp.get(b, 'N') for b in reversed(seq))

def extracting_seq(sequence, ref_seq1, ref_seq2, length):
    for seq in [ref_seq1, ref_seq2, rev_comp_seq(ref_seq1), rev_comp_seq(ref_seq2)]:
        if seq in sequence:
            splitted = sequence.split(seq, 1)
            if len(splitted) > 1:
                target_set = splitted[1][:length] if seq in [ref_seq1, rev_comp_seq(ref_seq2)] else splitted[0][-length:]
                if seq in [rev_comp_seq(ref_seq1), rev_comp_seq(ref_seq2)]:
                    target_set = rev_comp_seq(target_set)
                return target_set
    return None

def split_sequence(sequence, ref_seqs):
    seq1, seq2, seq3, seq4 = ref_seqs
    B = extracting_seq(sequence, seq1, seq2, 150)
    if B is None:
        return False, [None, None]
    D = extracting_seq(sequence, seq3, seq4, 20)
    if D is None:
        return False, [None, None]
    return True, [B, D]

# ======================
# BAM → CSV
# ======================
def turn_sam_into_csv(bam_path, output_csv):
    print("🔄 Converting BAM to CSV...")
    with pysam.AlignmentFile(bam_path, "rb", check_sq=False) as bam:
        with open(output_csv, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["read_id", "sequence"])
            for read in bam.fetch(until_eof=True):
                if read.query_sequence:
                    writer.writerow([read.query_name, read.query_sequence])
    print("✅ Finished! Saved to", output_csv)

# ======================
# Barcode parsing with Dask
# ======================
def process_reads(df_partition, ref_seqs):
    result = []
    for idx, row in df_partition.iterrows():
        seq = row["sequence"]
        success, [var, bc] = split_sequence(seq, ref_seqs)
        if success:
            result.append([row["read_id"], var, bc, len(var), len(bc)])
    return pd.DataFrame(result, columns=["read_id", "var", "bc", "var_len", "bc_len"])

def parse_csv_with_dask(input_csv, output_csv,ref_seqs, n_workers=16, mem_per_worker='6GB'):
    print("🚀 Starting barcode/variant extraction with Dask...")
    cluster = LocalCluster(n_workers=n_workers, threads_per_worker=1, memory_limit=mem_per_worker)
    client = Client(cluster)
    print("🔧 Dask dashboard:", client.dashboard_link)

    ddf = dd.read_csv(input_csv, blocksize="32MB")
    with ProgressBar():
        mapper = partial(process_reads, ref_seqs=ref_seqs)
        result_ddf = ddf.map_partitions(mapper)
        result_df = result_ddf.compute()

    result_df.to_csv(output_csv, index=False)
    print("✅ Finished! Saved to", output_csv)

# ======================
# Main CLI
# ======================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw_csv', type=str, default="/path/to/raw_reads.csv")
    parser.add_argument('--output_csv', type=str, default="/path/to/parsed_reads.csv")
    parser.add_argument('--n_workers', type=int, default=16)
    parser.add_argument('--mem_per_worker', type=str, default='6GB')
    parser.add_argument('--ref_seqs', type=str,help="Comma-separated reference sequences, e.g. 'SEQ1,SEQ2,SEQ3,SEQ4'")
    args = parser.parse_args()

    ref_seqs = args.ref_seqs.split(",")
    if len(ref_seqs) != 4:
        raise ValueError("You must provide exactly 4 reference sequences.")
    parse_csv_with_dask(args.raw_csv, args.output_csv, ref_seqs, args.n_workers, args.mem_per_worker)