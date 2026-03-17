#!/usr/bin/env python3
"""
Flatten BacDive raw JSON batch files into relational TSV tables.

Reads: data/bacdive_ingest/raw/batch_*.json
Writes: data/bacdive_ingest/*.tsv (one per table)

Tables:
  strain, taxonomy, culture_condition, isolation,
  physiology, metabolite_utilization, sequence_info, enzyme
"""

import csv
import glob
import json
import os
import sys

RAW_DIR = os.path.join(os.path.dirname(__file__), "raw")
OUT_DIR = os.path.dirname(__file__)


def safe_get(d, *keys, default=""):
    """Navigate nested dict safely."""
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, default)
        else:
            return default
    return d if d is not None else default


def flatten_strain(bid, record):
    """Extract core strain info."""
    gen = record.get("General", {})
    tax = record.get("Name and taxonomic classification", {})
    return {
        "bacdive_id": bid,
        "dsm_number": gen.get("DSM-Number", ""),
        "description": gen.get("description", ""),
        "ncbi_taxid": safe_get(gen, "NCBI tax id", "NCBI tax id"),
        "ncbi_taxid_match_level": safe_get(gen, "NCBI tax id", "Matching level"),
        "species_name": tax.get("species", ""),
        "strain_designation": tax.get("strain designation", ""),
        "type_strain": tax.get("type strain", ""),
        "keywords": ";".join(gen.get("keywords", [])) if isinstance(gen.get("keywords"), list) else str(gen.get("keywords", "")),
        "doi": gen.get("doi", ""),
    }


def flatten_taxonomy(bid, record):
    """Extract full taxonomy (LPSN preferred, fallback to main)."""
    tax = record.get("Name and taxonomic classification", {})
    lpsn = tax.get("LPSN", {})
    # Prefer LPSN taxonomy, fallback to top-level
    return {
        "bacdive_id": bid,
        "domain": lpsn.get("domain", tax.get("domain", "")),
        "phylum": lpsn.get("phylum", tax.get("phylum", "")),
        "class": lpsn.get("class", tax.get("class", "")),
        "order": lpsn.get("order", tax.get("order", "")),
        "family": lpsn.get("family", tax.get("family", "")),
        "genus": lpsn.get("genus", tax.get("genus", "")),
        "species": lpsn.get("species", tax.get("species", "")),
        "full_name": lpsn.get("full scientific name", tax.get("full scientific name", "")),
    }


def flatten_culture_conditions(bid, record):
    """Extract growth media and temperatures. Multiple rows per strain."""
    rows = []
    culture = record.get("Culture and growth conditions", {})
    if not culture:
        return rows

    # Culture media — can be a single dict or a list of dicts
    media = culture.get("culture medium", {})
    if isinstance(media, dict):
        media = [media]
    elif not isinstance(media, list):
        media = []

    for m in media:
        if isinstance(m, dict) and m.get("name"):
            rows.append({
                "bacdive_id": bid,
                "medium_name": m.get("name", ""),
                "growth": m.get("growth", ""),
                "medium_link": m.get("link", ""),
                "temperature": "",
                "record_type": "medium",
            })

    # Culture temperature — can be single dict or list
    temps = culture.get("culture temp", {})
    if isinstance(temps, dict):
        temps = [temps]
    elif not isinstance(temps, list):
        temps = []

    for t in temps:
        if isinstance(t, dict):
            rows.append({
                "bacdive_id": bid,
                "medium_name": "",
                "growth": t.get("growth", ""),
                "medium_link": "",
                "temperature": t.get("temperature", ""),
                "record_type": "temperature",
            })

    return rows


def flatten_isolation(bid, record):
    """Extract isolation source info."""
    iso_section = record.get("Isolation, sampling and environmental information", {})
    if not iso_section:
        return None

    iso = iso_section.get("isolation", {})
    cats = iso_section.get("isolation source categories", {})
    if not iso and not cats:
        return None

    if isinstance(iso, list):
        iso = iso[0] if iso else {}
    if isinstance(cats, list):
        cats = cats[0] if cats else {}
    if not isinstance(cats, dict):
        cats = {}

    return {
        "bacdive_id": bid,
        "sample_type": iso.get("sample type", "") if isinstance(iso, dict) else "",
        "country": iso.get("country", "") if isinstance(iso, dict) else "",
        "continent": iso.get("continent", "") if isinstance(iso, dict) else "",
        "geographic_location": iso.get("geographic location", "") if isinstance(iso, dict) else "",
        "cat1": cats.get("Cat1", ""),
        "cat2": cats.get("Cat2", ""),
        "cat3": cats.get("Cat3", ""),
    }


def flatten_physiology(bid, record):
    """Extract physiology: oxygen tolerance, gram stain, cell shape, motility."""
    phys = record.get("Physiology and metabolism", {})
    morph = record.get("Morphology", {})
    pred = record.get("Genome-based predictions", {})

    # Cell morphology can be dict or list
    cell_morph = morph.get("cell morphology", {})
    if isinstance(cell_morph, list):
        cell_morph = cell_morph[0] if cell_morph else {}

    oxygen = phys.get("oxygen tolerance", {})
    if isinstance(oxygen, list):
        oxygen = oxygen[0] if oxygen else {}
    elif isinstance(oxygen, dict) and "@ref" in oxygen:
        pass  # single entry is fine

    murein = phys.get("murein", {})
    if isinstance(murein, list):
        murein = murein[0] if murein else {}

    return {
        "bacdive_id": bid,
        "gram_stain": cell_morph.get("gram stain", ""),
        "cell_shape": cell_morph.get("cell shape", ""),
        "motility": cell_morph.get("motility", ""),
        "oxygen_tolerance": oxygen.get("oxygen tolerance", "") if isinstance(oxygen, dict) else str(oxygen),
        "murein_type": murein.get("murein type", "") if isinstance(murein, dict) else "",
        # Genome-based predictions
        "predicted_gram": safe_get(pred, "gram stain", "prediction"),
        "predicted_motility": safe_get(pred, "motility", "prediction"),
        "predicted_oxygen": safe_get(pred, "oxygen tolerance", "prediction"),
    }


def flatten_metabolite_utilization(bid, record):
    """Extract metabolite utilization data. Multiple rows per strain."""
    rows = []
    phys = record.get("Physiology and metabolism", {})

    met_util = phys.get("metabolite utilization", {})
    if isinstance(met_util, dict):
        met_util = [met_util]
    elif not isinstance(met_util, list):
        met_util = []

    for entry in met_util:
        if not isinstance(entry, dict):
            continue
        # Entry may have a list of tested metabolites
        tests = entry.get("metabolite", "")
        if isinstance(tests, str) and tests:
            rows.append({
                "bacdive_id": bid,
                "compound_name": tests,
                "chebi_id": entry.get("chebi id", ""),
                "utilization": entry.get("utilization activity", entry.get("utilization", "")),
            })

    # Also check metabolite production
    met_prod = phys.get("metabolite production", {})
    if isinstance(met_prod, dict):
        met_prod = [met_prod]
    elif not isinstance(met_prod, list):
        met_prod = []

    for entry in met_prod:
        if not isinstance(entry, dict):
            continue
        rows.append({
            "bacdive_id": bid,
            "compound_name": entry.get("metabolite", ""),
            "chebi_id": entry.get("chebi id", ""),
            "utilization": "produced",
        })

    return rows


def flatten_sequence_info(bid, record):
    """Extract genome and 16S sequence accessions."""
    rows = []
    seq = record.get("Sequence information", {})
    if not seq:
        return rows

    # 16S sequences
    s16 = seq.get("16S sequences", {})
    if isinstance(s16, dict):
        s16 = [s16]
    elif not isinstance(s16, list):
        s16 = []

    for entry in s16:
        if isinstance(entry, dict) and entry.get("accession"):
            rows.append({
                "bacdive_id": bid,
                "accession_type": "16S",
                "accession": entry.get("accession", ""),
                "database": entry.get("database", ""),
                "assembly_level": "",
                "description": entry.get("description", ""),
            })

    # Genome sequences
    genomes = seq.get("Genome sequences", {})
    if isinstance(genomes, dict):
        genomes = [genomes]
    elif not isinstance(genomes, list):
        genomes = []

    for entry in genomes:
        if isinstance(entry, dict):
            acc = entry.get("INSDC accession", entry.get("accession", ""))
            if acc:
                rows.append({
                    "bacdive_id": bid,
                    "accession_type": "genome",
                    "accession": acc,
                    "database": entry.get("database", "INSDC"),
                    "assembly_level": entry.get("assembly level", ""),
                    "description": entry.get("description", ""),
                })

    # GC content
    gc = seq.get("GC content", {})
    if isinstance(gc, dict) and gc.get("GC-content"):
        rows.append({
            "bacdive_id": bid,
            "accession_type": "gc_content",
            "accession": str(gc.get("GC-content", "")),
            "database": gc.get("method", ""),
            "assembly_level": "",
            "description": "",
        })

    return rows


def flatten_enzyme(bid, record):
    """Extract enzyme activity data."""
    rows = []
    phys = record.get("Physiology and metabolism", {})

    enzymes = phys.get("enzymes", {})
    if isinstance(enzymes, dict):
        enzymes = [enzymes]
    elif not isinstance(enzymes, list):
        enzymes = []

    for entry in enzymes:
        if not isinstance(entry, dict):
            continue
        rows.append({
            "bacdive_id": bid,
            "enzyme_name": entry.get("value", entry.get("enzyme", "")),
            "ec_number": entry.get("ec", entry.get("EC", "")),
            "activity": entry.get("activity", ""),
        })

    return rows


def write_tsv(filename, rows, fieldnames):
    """Write rows to TSV file."""
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t",
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {filename}: {len(rows):>8,} rows")
    return path


def main():
    # Load all batch files
    batch_files = sorted(glob.glob(os.path.join(RAW_DIR, "batch_*.json")))
    print(f"Loading {len(batch_files)} batch files...")

    all_records = {}
    for bf in batch_files:
        with open(bf) as f:
            batch = json.load(f)
        for bid_str, record in batch.items():
            all_records[int(bid_str)] = record

    print(f"Total strains loaded: {len(all_records):,}")

    # Flatten into tables
    strains = []
    taxonomies = []
    culture_conditions = []
    isolations = []
    physiologies = []
    metabolites = []
    sequences = []
    enzymes = []

    for bid, record in sorted(all_records.items()):
        strains.append(flatten_strain(bid, record))
        taxonomies.append(flatten_taxonomy(bid, record))
        culture_conditions.extend(flatten_culture_conditions(bid, record))

        iso = flatten_isolation(bid, record)
        if iso:
            isolations.append(iso)

        physiologies.append(flatten_physiology(bid, record))
        metabolites.extend(flatten_metabolite_utilization(bid, record))
        sequences.extend(flatten_sequence_info(bid, record))
        enzymes.extend(flatten_enzyme(bid, record))

    # Write TSV files
    print(f"\nWriting TSV files:")
    write_tsv("strain.tsv", strains,
              ["bacdive_id", "dsm_number", "description", "ncbi_taxid", "ncbi_taxid_match_level",
               "species_name", "strain_designation", "type_strain", "keywords", "doi"])

    write_tsv("taxonomy.tsv", taxonomies,
              ["bacdive_id", "domain", "phylum", "class", "order", "family", "genus", "species", "full_name"])

    write_tsv("culture_condition.tsv", culture_conditions,
              ["bacdive_id", "medium_name", "growth", "medium_link", "temperature", "record_type"])

    write_tsv("isolation.tsv", isolations,
              ["bacdive_id", "sample_type", "country", "continent", "geographic_location", "cat1", "cat2", "cat3"])

    write_tsv("physiology.tsv", physiologies,
              ["bacdive_id", "gram_stain", "cell_shape", "motility", "oxygen_tolerance", "murein_type",
               "predicted_gram", "predicted_motility", "predicted_oxygen"])

    write_tsv("metabolite_utilization.tsv", metabolites,
              ["bacdive_id", "compound_name", "chebi_id", "utilization"])

    write_tsv("sequence_info.tsv", sequences,
              ["bacdive_id", "accession_type", "accession", "database", "assembly_level", "description"])

    write_tsv("enzyme.tsv", enzymes,
              ["bacdive_id", "enzyme_name", "ec_number", "activity"])

    print(f"\nDone! {len(strains):,} strains flattened into 8 tables.")


if __name__ == "__main__":
    main()
