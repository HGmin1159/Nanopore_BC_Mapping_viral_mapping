import pysam
import csv
import argparse

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
# FASTA → CSV
# ======================
def fasta_to_csv(fasta_path, output_csv):
    print("🔄 Converting FASTA to CSV...")
    with open(fasta_path, 'r') as fasta, open(output_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['read_id', 'sequence'])
        read_id = None
        sequence = []
        for line in fasta:
            line = line.strip()
            if line.startswith('>'):
                if read_id:
                    writer.writerow([read_id, ''.join(sequence)])
                read_id = line[1:]
                sequence = []
            else:
                sequence.append(line)
        if read_id:
            writer.writerow([read_id, ''.join(sequence)])
    print("✅ Finished! Saved to", output_csv)

# ======================
# FASTQ → CSV
# ======================
def fastq_to_csv(fastq_path, output_csv):
    print("🔄 Converting FASTQ to CSV...")
    with open(fastq_path, 'r') as fastq, open(output_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['read_id', 'sequence', 'quality'])

        while True:
            read_id = fastq.readline().strip()
            if not read_id:
                break
            sequence = fastq.readline().strip()
            plus = fastq.readline().strip()
            quality = fastq.readline().strip()

            if read_id.startswith('@') and plus == '+':
                writer.writerow([read_id[1:], sequence, quality])

    print("✅ Finished! Saved to", output_csv)

# ======================
# Entry Point
# ======================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_type', type=str, required=True, choices=["bam", "fasta", "fastq"],
                        help="Input file type: bam / fasta / fastq")
    parser.add_argument('--input_path', type=str, required=True)
    parser.add_argument('--output_path', type=str, required=True)
    args = parser.parse_args()

    if args.input_type == "bam":
        turn_sam_into_csv(args.input_path, args.output_path)
    elif args.input_type == "fasta":
        fasta_to_csv(args.input_path, args.output_path)
    elif args.input_type == "fastq":
        fastq_to_csv(args.input_path, args.output_path)
    else:
        raise ValueError("❌ Invalid input type. Use one of: bam, fasta, fastq.")