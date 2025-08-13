#!/bin/bash
#SBATCH --job-name=minbr
#SBATCH --partition=medium
#SBATCH --array=1-24
#SBATCH --output=minbr_%a.out
#SBATCH --error=minbr_%a.err
#SBATCH --mem=10GB
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mail-user=james.evans@nhm.ac.uk
#SBATCH --mail-type=END,FAIL
#SBATCH --no-requeue

source activate ptp

mkdir ptp

IDX=$(printf "%d" ${SLURM_ARRAY_TASK_ID})

FASTA=./subsets/subset_${IDX}.fasta
TREE=./subsets/subset_${IDX}.tre
OUTPUT=./ptp/minbr_${IDX}

mptp \
    --minbr_auto "$FASTA" \
    --tree_file "$TREE" \
    --output_file "$OUTPUT"
