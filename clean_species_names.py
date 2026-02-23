#!/usr/bin/env python3
"""
Species Name Cleanup Script
============================

Cleans species names in metadata to contain only canonical Linnaean binomials.
Extracts specimen identifiers, BOLD IDs, and other suffixes to a separate column.

Input:  metadata.csv (with messy species names)
Output: metadata_cleaned.csv (with cleaned species names)
"""

import pandas as pd
import re
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clean_species_name(species_value, genus_value=None):
    """
    Clean a species name to contain only the canonical binomial or trinomial.
    
    Args:
        species_value: The value from the species column
        genus_value: The value from the genus column (for building binomial)
    
    Returns:
        tuple: (cleaned_species, cleaned_subspecies, extracted_suffix)
    
    The species column should contain the full Linnaean binomial: "Genus species"
    The subspecies column should contain trinomial: "Genus species subspecies"
    
    Examples:
        "Onthophagus incensus" → ("Onthophagus incensus", None, None)
        "Onthophagus incensusASolis02" → ("Onthophagus incensus", None, "ASolis02")
        "Onthophagus sp." → (None, None, "sp.")
        "Onthophagus sp._13YB" → (None, None, "sp._13YB")
        "Onthophagus incensus auratus" → ("Onthophagus incensus", "Onthophagus incensus auratus", None)
    """
    if pd.isna(species_value) or species_value == '':
        return None, None, None
    
    species_str = str(species_value).strip()
    
    # Remove genus prefix if it's duplicated at the start
    # e.g., "Onthophagus Onthophagus incensus" → "Onthophagus incensus"
    if genus_value and pd.notna(genus_value):
        genus_str = str(genus_value).strip()
        # Check for doubled genus
        doubled_pattern = f"^{genus_str}\\s+{genus_str}\\s+"
        if re.match(doubled_pattern, species_str):
            species_str = re.sub(f"^{genus_str}\\s+", "", species_str, count=1)
    
    # Split into parts
    parts = species_str.split()
    
    if len(parts) == 0:
        return None, None, None
    
    # Determine genus and species parts
    # Expected format: "Genus species [subspecies] [suffix]"
    
    # If first part looks like a genus (capitalized)
    if parts[0][0].isupper():
        genus_part = parts[0]
        remaining_parts = parts[1:]
    elif genus_value and pd.notna(genus_value):
        # Use provided genus
        genus_part = str(genus_value).strip()
        remaining_parts = parts
    else:
        # No genus available
        return None, None, species_str
    
    if len(remaining_parts) == 0:
        # Only genus provided, no species
        return None, None, species_str
    
    # Check first part of remaining - should be species epithet
    species_epithet = remaining_parts[0]
    
    # Pattern 1: "sp." or "sp" variants - NOT a valid species
    if re.match(r'^sp\.?$', species_epithet, re.IGNORECASE):
        # Everything is suffix
        return None, None, species_str
    
    if re.match(r'^sp[._]', species_epithet, re.IGNORECASE):
        # e.g., "sp._13YB", "sp_BOLD"
        return None, None, species_str
    
    # Pattern 2: "aff." or "cf." - uncertain identification
    if species_epithet.lower() in ['aff.', 'cf.']:
        return None, None, species_str
    
    # Pattern 3: Valid species epithet
    # Extract canonical species name (lowercase letters only at start)
    match = re.match(r'^([a-z]+)', species_epithet)
    
    if not match:
        # Doesn't look like valid species epithet
        return None, None, species_str
    
    canonical_species = match.group(1)
    suffix_from_species = species_epithet[len(canonical_species):]
    
    # Build binomial
    binomial = f"{genus_part} {canonical_species}"
    
    # Check if there are more parts (potential subspecies or suffix)
    if len(remaining_parts) > 1:
        # Could be trinomial or suffix
        next_part = remaining_parts[1]
        
        # Check if it looks like a subspecies (lowercase, letters only)
        if re.match(r'^[a-z]+$', next_part):
            # Trinomial
            trinomial = f"{binomial} {next_part}"
            
            # Any remaining parts are suffix
            if len(remaining_parts) > 2:
                suffix = ' '.join(remaining_parts[2:])
                return binomial, trinomial, suffix
            else:
                return binomial, trinomial, None
        else:
            # Not a valid subspecies - treat as suffix
            suffix = ' '.join(remaining_parts[1:])
            if suffix_from_species:
                suffix = suffix_from_species + ' ' + suffix
            elif suffix_from_species:
                suffix = suffix_from_species
            return binomial, None, suffix if suffix else None
    else:
        # No subspecies, but might have suffix attached to species epithet
        if suffix_from_species:
            return binomial, None, suffix_from_species
        else:
            return binomial, None, None


def analyze_species_column(metadata_path='metadata.csv'):
    """Analyze species column and show what would be cleaned."""
    
    logger.info("=" * 70)
    logger.info("SPECIES NAME ANALYSIS")
    logger.info("=" * 70)
    
    df = pd.read_csv(metadata_path)
    logger.info(f"Loaded {len(df)} records from {metadata_path}\n")
    
    if 'species' not in df.columns:
        logger.error("No 'species' column found in metadata!")
        return
    
    # Analyze cleaning
    results = {
        'total': 0,
        'empty': 0,
        'sp_variants': 0,
        'with_suffix': 0,
        'trinomials': 0,
        'clean': 0,
        'examples': {
            'sp_variants': [],
            'with_suffix': [],
            'trinomials': [],
            'clean': []
        }
    }
    
    for _, row in df.iterrows():
        species = row.get('species')
        genus = row.get('genus')
        results['total'] += 1
        
        if pd.isna(species) or species == '':
            results['empty'] += 1
            continue
        
        cleaned_binomial, cleaned_trinomial, suffix = clean_species_name(species, genus)
        
        if cleaned_binomial is None:
            # sp. variant or invalid
            results['sp_variants'] += 1
            if len(results['examples']['sp_variants']) < 10:
                results['examples']['sp_variants'].append(str(species))
        elif suffix:
            # Has suffix
            results['with_suffix'] += 1
            if len(results['examples']['with_suffix']) < 10:
                results['examples']['with_suffix'].append(
                    f"{species} → binomial='{cleaned_binomial}' + suffix='{suffix}'"
                )
        elif cleaned_trinomial:
            # Trinomial (subspecies)
            results['trinomials'] += 1
            if len(results['examples']['trinomials']) < 5:
                results['examples']['trinomials'].append(
                    f"{species} → binomial='{cleaned_binomial}', trinomial='{cleaned_trinomial}'"
                )
        else:
            # Clean binomial
            results['clean'] += 1
            if len(results['examples']['clean']) < 5:
                results['examples']['clean'].append(str(species))
    
    # Print report
    logger.info("Summary:")
    logger.info(f"  Total species values: {results['total']}")
    logger.info(f"  Empty/NaN: {results['empty']} ({results['empty']/results['total']*100:.1f}%)")
    logger.info(f"  sp./BOLD/specimens (invalid): {results['sp_variants']} ({results['sp_variants']/results['total']*100:.1f}%)")
    logger.info(f"  Valid binomials with suffix: {results['with_suffix']} ({results['with_suffix']/results['total']*100:.1f}%)")
    logger.info(f"  Valid trinomials (subspecies): {results['trinomials']} ({results['trinomials']/results['total']*100:.1f}%)")
    logger.info(f"  Clean binomials: {results['clean']} ({results['clean']/results['total']*100:.1f}%)")
    
    logger.info("\nExamples of sp. variants (will be set to NaN):")
    for ex in results['examples']['sp_variants']:
        logger.info(f"  ~ {ex}")
    
    logger.info("\nExamples with suffixes (will be cleaned):")
    for ex in results['examples']['with_suffix']:
        logger.info(f"  ~ {ex}")
    
    if results['trinomials'] > 0:
        logger.info("\nExamples of trinomials (will extract subspecies):")
        for ex in results['examples']['trinomials']:
            logger.info(f"  ~ {ex}")
    
    logger.info("\nExamples of clean binomials (no change):")
    for ex in results['examples']['clean']:
        logger.info(f"  ~ {ex}")
    
    return results


def clean_metadata(input_path='metadata.csv', output_path='metadata_cleaned.csv'):
    """
    Clean species names in metadata and save to new file.
    
    Ensures:
    - species column contains full binomial: "Genus species"
    - subspecies column contains trinomial: "Genus species subspecies"
    - species_suffix contains extracted specimen IDs/codes
    """
    logger.info("\n" + "=" * 70)
    logger.info("CLEANING METADATA")
    logger.info("=" * 70)
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}\n")
    
    if 'species' not in df.columns:
        logger.error("No 'species' column found!")
        return
    
    # Add species_suffix column if it doesn't exist
    if 'species_suffix' not in df.columns:
        df['species_suffix'] = None
    
    # Ensure subspecies column exists
    if 'subspecies' not in df.columns:
        df['subspecies'] = None
    
    # Track original values
    original_species_values = df['species'].copy()
    original_subspecies_values = df['subspecies'].copy() if 'subspecies' in df.columns else pd.Series([None] * len(df))
    
    # Clean each species name
    cleaned_count = 0
    suffix_count = 0
    trinomial_count = 0
    invalidated_count = 0
    
    for idx, row in df.iterrows():
        species_val = row.get('species')
        genus_val = row.get('genus')
        
        if pd.isna(species_val) or species_val == '':
            continue
        
        original_species = str(species_val)
        
        # Clean the species name
        cleaned_binomial, cleaned_trinomial, suffix = clean_species_name(species_val, genus_val)
        
        # Track changes
        if str(cleaned_binomial) != original_species:
            cleaned_count += 1
        
        if suffix:
            df.at[idx, 'species_suffix'] = suffix
            suffix_count += 1
        
        if cleaned_trinomial:
            df.at[idx, 'subspecies'] = cleaned_trinomial
            trinomial_count += 1
        
        if cleaned_binomial is None and suffix:
            invalidated_count += 1
        
        # Update species column with cleaned binomial
        df.at[idx, 'species'] = cleaned_binomial
    
    # Save cleaned metadata
    df.to_csv(output_path, index=False)
    
    logger.info(f"✓ Cleaned metadata saved to: {output_path}")
    logger.info(f"\nChanges made:")
    logger.info(f"  Species values modified: {cleaned_count}")
    logger.info(f"  Suffixes extracted: {suffix_count}")
    logger.info(f"  Trinomials identified: {trinomial_count}")
    logger.info(f"  Species invalidated (sp./BOLD/etc): {invalidated_count}")
    
    # Show examples of suffix extraction
    logger.info("\nExamples of suffix extraction:")
    suffix_examples = []
    for idx, row in df.iterrows():
        if pd.notna(row['species_suffix']) and len(suffix_examples) < 10:
            original = original_species_values[idx]
            current_species = row['species']
            suffix = row['species_suffix']
            
            if pd.notna(current_species):
                suffix_examples.append(
                    f"  '{original}' → species='{current_species}' + suffix='{suffix}'"
                )
            else:
                suffix_examples.append(
                    f"  '{original}' → INVALID (suffix='{suffix}')"
                )
    
    for ex in suffix_examples:
        logger.info(ex)
    
    # Show examples of trinomials
    if trinomial_count > 0:
        logger.info("\nExamples of trinomials (subspecies):")
        trinomial_examples = []
        for idx, row in df.iterrows():
            if pd.notna(row['subspecies']) and len(trinomial_examples) < 5:
                original = original_species_values[idx]
                binomial = row['species']
                trinomial = row['subspecies']
                trinomial_examples.append(
                    f"  '{original}' → binomial='{binomial}', trinomial='{trinomial}'"
                )
        
        for ex in trinomial_examples:
            logger.info(ex)
    
    return df


def main():
    """Main execution."""
    
    input_file = Path('metadata.csv')
    output_file = Path('metadata_cleaned.csv')
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return
    
    # First, analyze what would change
    logger.info("Analyzing species names...\n")
    analyze_species_column(input_file)
    
    # Ask for confirmation
    print("\n" + "=" * 70)
    response = input("Proceed with cleaning? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        clean_metadata(input_file, output_file)
        logger.info("\n✓ Done! Use metadata_cleaned.csv for further processing.")
    else:
        logger.info("Cleaning cancelled.")


if __name__ == '__main__':
    main()
