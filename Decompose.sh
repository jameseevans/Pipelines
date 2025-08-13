#!/bin/bash
#SBATCH --job-name=Decompose
#SBATCH --partition=medium
#SBATCH --output=Decompose.out
#SBATCH --error=Decompose.err
#SBATCH --mem=120GB
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --job-name=subset
#SBATCH --mail-user=james.evans@nhm.ac.uk
#SBATCH --mail-type=END,FAIL
#SBATCH --no-requeue

source activate phylogeny

mkdir subsets

python3 Decompose.py -i 500k_constrained_rooted_pruned.tre -a 500k_pruned.fasta -m 65000 -o ./subsets/
