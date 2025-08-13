#!/bin/bash
#SBATCH --job-name=ptp
#SBATCH --partition=short
#SBATCH --array=1-24
#SBATCH --output=ptp_%a.out
#SBATCH --error=ptp_%a.err
#SBATCH --mem=8GB
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mail-user=james.evans@nhm.ac.uk
#SBATCH --mail-type=END,FAIL
#SBATCH --no-requeue

source activate ptp

IDX=${SLURM_ARRAY_TASK_ID}
TREE=./subsets/subset_${IDX}.tre

# Get minbr from .out instead of ptp output to avoid rounding
MINBR=$(grep "Minimum branch length (--minbr)" minbr_${IDX}.out | awk '{ print $NF }')

if [ -z "$MINBR" ]; then
    echo "Error: Could not extract minbr for subset $IDX"
    exit 1
fi

/mnt/shared/scratch/jevans/private/mptp/bin/mptp \
    --ml --single \
    --minbr "$MINBR" \
    --tree_file "$TREE" \
    --output_file ./ptp/single_${IDX}
