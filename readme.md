

# 🔬 MPRA Barcode-Element Mapping (Long-read Nanopore)

This repository contains a pipeline to generate a **barcode-to-element mapping table** from **long-read sequencing** data generated in **Massively Parallel Reporter Assays (MPRA)**. It was developed for use with Nanopore data and customized MPRA libraries.

---

## ⚙️ Environment

The pipeline has been tested with the following versions:

| Package       | Version   |
|---------------|-----------|
| Python        | 3.8.19    |
| Snakemake     | 5.5.4     |
| pysam         | 0.21.0    |
| pandas        | 2.0.3     |
| dask          | 2023.5.0  |
| faiss         | 1.8.0     |
| Levenshtein   | 0.25.1    |

---

## 🧬 Configuration (`config/config.yaml`)

Example YAML configuration for running the pipeline:

```yaml
input_seq: "/your/pathto/read.fastq"
input_format: "fastq" # Options: "bam" (not aligned), "fastq", "fasta"
anchor_seq: # sequences surrounding the target element and barcode
  - "TATATGGAGTTCCGACGCGT"
  - "GGTACCGTGATGCGGTTTTG"
  - "AGATCGCCGTGTAATCTAGA"
  - "ACTAGTGATACCGAGCGCTG"
output_dir: "/your/pathto/output_dir/"
variant_dict: "/your/pathto/variant_dict.csv"
```
---


🚀 Running the Pipeline
	1.	Install dependencies (recommended: via conda):

conda create -n mpra_env python=3.8
conda activate mpra_env

pip install pysam pandas dask faiss-cpu python-Levenshtein snakemake==5.5.4

	2.	Run the pipeline:

bash run_pipeline.sh

	3.	Dry run for debugging:

snakemake --configfile config/config.yaml -n



⸻

📊 Output Files

File	Description
result/raw_reads.csv	Raw reads converted from BAM
result/var_bc_reads.csv	Parsed reads based on anchor sequences
result/var_bc_reads_named.csv	Reads annotated with variant information
result/barcode_statistcs.csv	Barcode-level statistics
result/variant_statistcs.csv	Variant-level statistics
result/bc_mapping.csv	Final barcode-to-element mapping table



⸻

📌 Notes
	- 	This pipeline was developed by the Hyejung Won Lab at UNC Chapel Hill.
	- 	It was used in an in vivo MPRA experiment with custom reporter constructs.
    -   This script is currently tailored to a specific plasmid configuration, but we plan to update it in the future to support more general plasmid settings.
⸻

📫 Contact

For any questions, please contact:

HyungGyu Min
University of North Carolina at Chapel Hill
mhg@unc.edu

Let me know if you want it turned into a real file or need GitHub repo setup instructions!
