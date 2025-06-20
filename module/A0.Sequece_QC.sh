#!/bin/bash

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --seq_dir) seq_dir="$2"; shift ;;
        --out_dir) out_dir="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

module load fastqc
module load multiqc


mkdir -p $out_dir
export _JAVA_OPTIONS="-Xmx128G"
fastqc -t 16 -o $out_dir $seq_dir
multiqc $out_dir