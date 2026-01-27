#!/bin/bash
#SBATCH --job-name=Decompose
#SBATCH --partition=medium
#SBATCH --output=Decompose.out
#SBATCH --error=Decompose.err
#SBATCH --mem=120GB
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --job-name=subset
#SBATCH --mail-type=END,FAIL
#SBATCH --no-requeue

source activate phylogeny

mkdir subsets

python3 Decompose.py -i tree.tre -a alignment.fasta -m 65000 -o ./subsets/
