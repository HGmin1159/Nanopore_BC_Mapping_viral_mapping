configfile: "config/config.yaml"

rule all:
    input:
        f"{config['output_dir']}/result/raw_reads.csv",
        f"{config['output_dir']}/result/var_bc_reads.csv",
        f"{config['output_dir']}/result/var_bc_reads_named.csv",
        f"{config['output_dir']}/result/barcode_statistcs.csv",
        f"{config['output_dir']}/result/variant_statistcs.csv",
        f"{config['output_dir']}/result/bc_mapping.csv"


rule transform_to_csv:
    input:
        bam=config["input_seq"]
    output:
        csv=f"{config['output_dir']}/result/raw_reads.csv"
    shell:
        """
        module load anaconda
        conda activate anaconda_env
        module del anaconda

        python module/A1.transform_to_csv.py \
            --input_type {config[input_format]} \
            --input_path {input.bam} \
            --output_path {output.csv}
        """

rule split_reads_dask:
    input:
        raw_csv=f"{config['output_dir']}/result/raw_reads.csv"
    output:
        parsed_csv=f"{config['output_dir']}/result/var_bc_reads.csv"
    params:
        ref_seqs=",".join(config["anchor_seq"]),
        n_workers=32,
        mem_per_worker="9GB"
    shell:
        """
        module load anaconda
        conda activate anaconda_env
        module del anaconda

        python module/A2.Split_Reads_Dask.py \
            --raw_csv {input.raw_csv} \
            --output_csv {output.parsed_csv} \
            --ref_seqs "{params.ref_seqs}" \
            --n_workers {params.n_workers} \
            --mem_per_worker {params.mem_per_worker}
        """

rule match_variant:
    input:
        var_csv=f"{config['output_dir']}/result/var_bc_reads.csv"
    output:
        named_csv=f"{config['output_dir']}/result/var_bc_reads_named.csv"
    params:
        variant_dict=config["variant_dict"]
    shell:
        """
        module load anaconda
        conda activate anaconda_env
        module del anaconda

        python module/A3.mathcing_variant.py \
            --data_path {input.var_csv} \
            --variant_dict_path {params.variant_dict} \
            --output_path {output.named_csv}
        """

rule analysis:
    input:
        named_csv=f"{config['output_dir']}/result/var_bc_reads_named.csv"
    output:
        output_barcode_path=f"{config['output_dir']}/result/barcode_statistcs.csv",
        output_variant_path=f"{config['output_dir']}/result/variant_statistcs.csv",
        output_bcmapping_path=f"{config['output_dir']}/result/bc_mapping.csv"
    shell:
        """
        module load anaconda
        conda activate anaconda_env
        module del anaconda

        python module/A4.analysis.py \
            --named_csv {input.named_csv} \
            --output_barcode_path {output.output_barcode_path} \
            --output_variant_path {output.output_variant_path} \
            --output_bcmapping_path {output.output_bcmapping_path}
        """