#!/bin/bash
#SBATCH -t 11-00:00:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --mail-user=mhg@unc.edu
#SBATCH --mail-type=end,fail,begin
#SBATCH --job-name=snakemake
#SBATCH --export=ALL

module purge
module add anaconda
conda activate anaconda_env
module del anaconda

output_dir=$(python -c "import yaml; print(yaml.safe_load(open('config/config.yaml'))['output_dir'])")
mkdir -p $output_dir

snakemake --unlock --configfile config/config.yaml

snakemake --dag\
          --configfile config/config.yaml | dot -Tpng > dag.png

snakemake --configfile config/config.yaml \
          --cluster 'sbatch --nodes=1 --ntasks={cluster.threads} --mem={cluster.mem} -t {cluster.time} -p {cluster.queue} -o {cluster.output}' \
          --jobs 45 \
          --cluster-config config/sbatch.yaml \
          --rerun-incomplete
          --dryrun
