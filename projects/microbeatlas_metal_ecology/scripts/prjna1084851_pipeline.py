#!/usr/bin/env python3
"""
PRJNA1084851 16S amplicon pipeline
===================================
Downloads 133 MiSeq paired-end 16S samples (SRR28246018–SRR28246150) from ENA,
trims 515F/806R primers, merges pairs, clusters OTUs at 97%, assigns SILVA 138
taxonomy, and builds a sample × OTU abundance table.

Raw FASTQs are deleted after each sample is processed (--no-keep-raw flag behaviour
is default). SILVA reference is kept permanently.

Usage:
    python3 scripts/prjna1084851_pipeline.py [--workers N] [--max-samples N]
"""

import os
import sys
import gzip
import re
import csv
import time
import shutil
import argparse
import logging
import subprocess
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT   = Path(__file__).parent.parent
DATA      = PROJECT / "data"
WORKDIR   = DATA / "prjna1084851"
FASTQDIR  = WORKDIR / "fastq"
TRIMDIR   = WORKDIR / "trimmed"
MERGEDIR  = WORKDIR / "merged"
SILVADIR  = WORKDIR / "silva"

for d in [FASTQDIR, TRIMDIR, MERGEDIR, SILVADIR]:
    d.mkdir(parents=True, exist_ok=True)

MANIFEST  = DATA / "prjna1084851_manifest.csv"
SILVA_FA  = SILVADIR / "silva138_v4_99.fasta"
SILVA_TAX = SILVADIR / "silva138_taxonomy.tsv"

# ── Amplicon primers (EMP 515F / 806R, Parada & Apprill) ───────────────────────
FWD_PRIMER = "GTGYCAGCMGCCGCGGTAA"   # 515F (19 bp)
REV_PRIMER = "GGACTACNVGGGTWTCTAAT"  # 806R (20 bp)

# ── ENA FTP URL template ───────────────────────────────────────────────────────
def ena_url(srr: str, read: int) -> str:
    # SRR28246018 → vol1/fastq/SRR282/018/SRR28246018/SRR28246018_1.fastq.gz
    prefix  = srr[:6]          # SRR282
    suffix  = srr[-3:]         # 018
    return (f"https://ftp.sra.ebi.ac.uk/vol1/fastq/{prefix}/{suffix}"
            f"/{srr}/{srr}_{read}.fastq.gz")

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(WORKDIR / "pipeline.log"),
    ],
)
log = logging.getLogger(__name__)

# ── Thread-safe counter ────────────────────────────────────────────────────────
_lock = threading.Lock()
_done = 0

# ── Helpers ────────────────────────────────────────────────────────────────────
def run(cmd, **kwargs):
    """Run a shell command, raise on failure."""
    result = subprocess.run(
        cmd, shell=isinstance(cmd, str),
        capture_output=True, text=True, **kwargs
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed (rc={result.returncode}):\n"
            f"  {cmd}\nSTDERR:\n{result.stderr[-2000:]}"
        )
    return result


def curl_download(url: str, dest: Path, retries: int = 3) -> bool:
    for attempt in range(retries):
        try:
            run(["curl", "-fsSL", "--retry", "3", "--retry-delay", "5",
                 "--connect-timeout", "30", "--max-time", "600",
                 "-o", str(dest), url])
            if dest.stat().st_size > 1000:
                return True
        except Exception as e:
            log.warning(f"Download attempt {attempt+1} failed for {url}: {e}")
            time.sleep(5 * (attempt + 1))
    return False


# ── Step 1: Download SILVA 138 V4 reference ────────────────────────────────────
def download_silva():
    global SILVA_FA
    if SILVA_FA.exists() and SILVA_FA.stat().st_size > 1_000_000:
        log.info(f"SILVA reference already present: {SILVA_FA}")
        return

    log.info("Downloading SILVA 138 V4 reference from QIIME2 resources...")
    # QIIME2-preprocessed SILVA 138 99% NR V4 (515F/806R trimmed) — ~150 MB .qza
    qza_url = ("https://data.qiime2.org/2023.5/common/"
               "silva-138-99-seqs-515-806.qza")
    tax_url = ("https://data.qiime2.org/2023.5/common/"
               "silva-138-99-tax.qza")

    qza_path = SILVADIR / "silva138_v4_99.qza"
    tax_path = SILVADIR / "silva138_tax.qza"

    if not qza_path.exists():
        log.info("  Downloading SILVA sequences .qza ...")
        ok = curl_download(qza_url, qza_path)
        if not ok:
            raise RuntimeError("Failed to download SILVA sequences")

    if not tax_path.exists():
        log.info("  Downloading SILVA taxonomy .qza ...")
        ok = curl_download(tax_url, tax_path)
        if not ok:
            raise RuntimeError("Failed to download SILVA taxonomy")

    # .qza is a zip file; extract FASTA and taxonomy TSV
    import zipfile
    log.info("  Extracting SILVA sequences from .qza ...")
    with zipfile.ZipFile(qza_path) as z:
        # Find the dna-sequences.fasta inside
        fasta_member = next(
            m for m in z.namelist() if m.endswith("dna-sequences.fasta")
        )
        with z.open(fasta_member) as src, open(SILVA_FA, "wb") as dst:
            shutil.copyfileobj(src, dst)

    log.info("  Extracting SILVA taxonomy from .qza ...")
    with zipfile.ZipFile(tax_path) as z:
        tsv_member = next(
            m for m in z.namelist() if m.endswith("taxonomy.tsv")
        )
        with z.open(tsv_member) as src, open(SILVA_TAX, "wb") as dst:
            shutil.copyfileobj(src, dst)

    # Convert taxonomy TSV to sintax format embedded in SILVA_FA headers
    log.info("  Merging taxonomy into FASTA headers (sintax format) ...")
    tax_df = pd.read_csv(SILVA_TAX, sep="\t", index_col=0)
    tax_dict = {}
    for feat_id, row in tax_df.iterrows():
        lineage = str(row.get("Taxon", ""))
        # Convert "d__Bacteria; p__Proteobacteria; ..." → sintax
        parts = [p.strip() for p in lineage.split(";")]
        sintax_parts = []
        for p in parts:
            if p.startswith("d__"):
                sintax_parts.append(f"d:{p[3:]}")
            elif p.startswith("p__"):
                sintax_parts.append(f"p:{p[3:]}")
            elif p.startswith("c__"):
                sintax_parts.append(f"c:{p[3:]}")
            elif p.startswith("o__"):
                sintax_parts.append(f"o:{p[3:]}")
            elif p.startswith("f__"):
                sintax_parts.append(f"f:{p[3:]}")
            elif p.startswith("g__"):
                sintax_parts.append(f"g:{p[3:]}")
            elif p.startswith("s__"):
                sintax_parts.append(f"s:{p[3:]}")
        tax_dict[feat_id] = ",".join(sintax_parts)

    sintax_fa = SILVADIR / "silva138_v4_sintax.fasta"
    with open(SILVA_FA) as src, open(sintax_fa, "w") as dst:
        for line in src:
            if line.startswith(">"):
                feat_id = line[1:].split()[0]
                sintax = tax_dict.get(feat_id, "")
                dst.write(f">{feat_id};tax={sintax}\n")
            else:
                dst.write(line)

    log.info(f"  SILVA sintax reference written to {sintax_fa}")
    SILVA_FA = sintax_fa
    log.info("SILVA download and preparation complete.")


# ── Step 2: Process one sample ─────────────────────────────────────────────────
def process_sample(srr: str, keep_raw: bool = False) -> dict:
    """Download, trim, merge one sample. Returns dict with stats."""
    global _done
    r1_gz  = FASTQDIR / f"{srr}_1.fastq.gz"
    r2_gz  = FASTQDIR / f"{srr}_2.fastq.gz"
    trim1  = TRIMDIR  / f"{srr}_1_trimmed.fastq.gz"
    trim2  = TRIMDIR  / f"{srr}_2_trimmed.fastq.gz"
    merged = MERGEDIR / f"{srr}_merged.fastq"
    stats  = {"srr": srr, "status": "ok", "raw_pairs": 0,
              "trimmed_pairs": 0, "merged": 0, "error": ""}

    # Skip if merged file already exists (e.g. placed by recovery script)
    if merged.exists() and merged.stat().st_size > 10_000:
        lines = int(subprocess.check_output(f"wc -l < {merged}", shell=True).decode().strip())
        stats["merged"] = lines // 4
        if stats["merged"] >= 100:
            with _lock:
                _done += 1
                log.info(f"  [{_done}/N] {srr}: pre-merged ({stats['merged']:,} reads) [skip]")
            return stats

    try:
        # ── Download ──────────────────────────────────────────────────────────
        if not r1_gz.exists():
            if not curl_download(ena_url(srr, 1), r1_gz):
                raise RuntimeError(f"R1 download failed for {srr}")
        if not r2_gz.exists():
            if not curl_download(ena_url(srr, 2), r2_gz):
                raise RuntimeError(f"R2 download failed for {srr}")

        # Count raw pairs (fast: check header count in gzip)
        try:
            raw_lines = int(subprocess.check_output(
                f"zcat {r1_gz} | wc -l", shell=True
            ).decode().strip())
            stats["raw_pairs"] = raw_lines // 4
        except Exception:
            pass

        # ── Trim primers (cutadapt) ────────────────────────────────────────────
        # Adapter on R1 = FWD; adapter on R2 = REV (linked adapters)
        cutadapt_cmd = [
            "cutadapt",
            "-g", FWD_PRIMER,          # 5' adapter on R1
            "-G", REV_PRIMER,          # 5' adapter on R2
            "--discard-untrimmed",     # discard pairs without both primers
            "--minimum-length", "100",
            "--cores", "2",
            "-o", str(trim1),
            "-p", str(trim2),
            str(r1_gz), str(r2_gz),
        ]
        run(cutadapt_cmd)

        # Count trimmed pairs
        try:
            trim_lines = int(subprocess.check_output(
                f"zcat {trim1} | wc -l", shell=True
            ).decode().strip())
            stats["trimmed_pairs"] = trim_lines // 4
        except Exception:
            pass

        if stats["trimmed_pairs"] < 500:
            raise RuntimeError(
                f"Too few reads after trimming: {stats['trimmed_pairs']}"
            )

        # ── Merge paired-end reads (vsearch) ────────────────────────────────
        run([
            "vsearch",
            "--fastq_mergepairs", str(trim1),
            "--reverse",          str(trim2),
            "--fastqout",         str(merged),
            "--fastq_minovlen",   "50",
            "--fastq_maxdiffs",   "5",
            "--fastq_minlen",     "200",
            "--fastq_maxlen",     "300",
            "--threads",          "2",
        ])

        try:
            merged_lines = int(subprocess.check_output(
                f"wc -l < {merged}", shell=True
            ).decode().strip())
            stats["merged"] = merged_lines // 4
        except Exception:
            pass

        if stats["merged"] < 100:
            raise RuntimeError(f"Too few merged reads: {stats['merged']}")

        # ── Clean up raw FASTQs ────────────────────────────────────────────
        if not keep_raw:
            r1_gz.unlink(missing_ok=True)
            r2_gz.unlink(missing_ok=True)

        # Also remove trimmed (keep merged only until clustering)
        trim1.unlink(missing_ok=True)
        trim2.unlink(missing_ok=True)

    except Exception as e:
        stats["status"] = "failed"
        stats["error"] = str(e)[:200]
        log.warning(f"  FAILED {srr}: {e}")
        # Clean up partial files
        for f in [r1_gz, r2_gz, trim1, trim2, merged]:
            f.unlink(missing_ok=True)

    with _lock:
        _done += 1
        log.info(f"  [{_done}/N] {srr}: raw={stats['raw_pairs']:,} "
                 f"trimmed={stats['trimmed_pairs']:,} merged={stats['merged']:,} "
                 f"[{stats['status']}]")
    return stats


# ── Step 3: Concatenate, dereplicate, cluster OTUs ─────────────────────────────
def cluster_otus(sample_stats: list, min_reads: int = 500) -> Path:
    log.info("=== Clustering OTUs ===")

    # Filter to samples that passed QC
    good = [s["srr"] for s in sample_stats
            if s["status"] == "ok" and s["merged"] >= min_reads]
    log.info(f"Samples with ≥{min_reads} merged reads: {len(good)}/{len(sample_stats)}")

    # Concatenate all merged reads into one FASTA with sample label in header
    all_fa = WORKDIR / "all_reads.fasta"
    log.info(f"Concatenating reads from {len(good)} samples → {all_fa}")
    with open(all_fa, "w") as out:
        for srr in good:
            merged_fq = MERGEDIR / f"{srr}_merged.fastq"
            if not merged_fq.exists():
                continue
            with open(merged_fq) as fq:
                i = 0
                for line in fq:
                    if i % 4 == 0:
                        out.write(f">{srr}.{line[1:].split()[0]}\n")
                    elif i % 4 == 1:
                        out.write(line)
                    i += 1

    log.info(f"All reads FASTA created")

    # Dereplicate
    derep_fa  = WORKDIR / "all_derep.fasta"
    log.info("Dereplicating...")
    run([
        "vsearch", "--derep_fulllength", str(all_fa),
        "--output", str(derep_fa),
        "--sizeout", "--minuniquesize", "2",
        "--uc", str(WORKDIR / "derep.uc"),
        "--threads", "8",
    ])

    # Chimera filter (de novo)
    nochim_fa = WORKDIR / "all_nochim.fasta"
    log.info("Chimera filtering (de novo)...")
    run([
        "vsearch", "--uchime3_denovo", str(derep_fa),
        "--nonchimeras", str(nochim_fa),
        "--threads", "8",
    ])

    # Cluster at 97%
    otus_fa = WORKDIR / "otus97.fasta"
    otus_uc = WORKDIR / "otus97.uc"
    log.info("Clustering at 97% identity...")
    run([
        "vsearch", "--cluster_size", str(nochim_fa),
        "--id", "0.97",
        "--centroids", str(otus_fa),
        "--uc", str(otus_uc),
        "--sizein", "--sizeout",
        "--relabel", "OTU_",
        "--threads", "32",
    ])

    n_otus = sum(1 for line in open(otus_fa) if line.startswith(">"))
    log.info(f"OTUs clustered: {n_otus:,}")

    # Map all reads back to OTUs to build abundance table
    map_uc = WORKDIR / "map_to_otus.uc"
    log.info("Mapping all reads to OTUs...")
    run([
        "vsearch", "--usearch_global", str(all_fa),
        "--db", str(otus_fa),
        "--id", "0.97",
        "--uc", str(map_uc),
        "--threads", "32",
    ])

    # Clean up large intermediate files
    all_fa.unlink(missing_ok=True)

    return otus_fa, map_uc, good


# ── Step 4: Assign taxonomy with sintax ───────────────────────────────────────
def assign_taxonomy(otus_fa: Path) -> dict:
    log.info("=== Assigning Taxonomy (SILVA 138 sintax) ===")
    sintax_fa = SILVADIR / "silva138_v4_sintax.fasta"

    sintax_out = WORKDIR / "otus_taxonomy.txt"
    run([
        "vsearch", "--sintax", str(otus_fa),
        "--db", str(sintax_fa),
        "--tabbedout", str(sintax_out),
        "--sintax_cutoff", "0.8",
        "--threads", "32",
    ])

    # Parse sintax output: OTU_id → {domain, phylum, ..., genus}
    tax = {}
    with open(sintax_out) as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 4:
                continue
            otu_id = parts[0].split(";")[0]
            tax_str = parts[3] if len(parts) > 3 else ""
            # Parse "d:Bacteria(1.00),p:Proteobacteria(0.99),..."
            tax_parts = {}
            for item in tax_str.split(","):
                m = re.match(r"([a-z]):([^(]+)", item)
                if m:
                    level_map = {
                        "d": "domain", "p": "phylum", "c": "class",
                        "o": "order",  "f": "family", "g": "genus",
                        "s": "species",
                    }
                    key = level_map.get(m.group(1), m.group(1))
                    val = m.group(2).strip()
                    if val and val not in ("uncultured", "unidentified", ""):
                        tax_parts[key] = val
            tax[otu_id] = tax_parts

    log.info(f"Taxonomy assigned for {len(tax)} OTUs")
    return tax


# ── Step 5: Build OTU table ────────────────────────────────────────────────────
def build_otu_table(map_uc: Path, good_samples: list, taxonomy: dict) -> pd.DataFrame:
    log.info("=== Building OTU Table ===")

    # Parse UC mapping file: sample → OTU → count
    counts = {}  # {sample: {otu: count}}
    with open(map_uc) as f:
        for line in f:
            if not line.startswith("H"):  # H = hit
                continue
            parts = line.strip().split("\t")
            if len(parts) < 10:
                continue
            query = parts[8]   # e.g. "SRR28246018.M01234"
            target = parts[9]  # e.g. "OTU_1;size=1234"
            sample = query.split(".")[0]
            otu = target.split(";")[0]
            if sample not in counts:
                counts[sample] = {}
            counts[sample][otu] = counts[sample].get(otu, 0) + 1

    # Build DataFrame: rows=samples, cols=OTUs
    all_otus = sorted(set(otu for s in counts.values() for otu in s))
    rows = []
    for sample in good_samples:
        row = {"sample": sample}
        sc = counts.get(sample, {})
        for otu in all_otus:
            row[otu] = sc.get(otu, 0)
        rows.append(row)

    otu_table = pd.DataFrame(rows).set_index("sample")
    log.info(f"OTU table: {otu_table.shape[0]} samples × {otu_table.shape[1]} OTUs")

    # Remove OTUs with total count < 2
    otu_table = otu_table.loc[:, otu_table.sum() >= 2]
    log.info(f"After filtering singletons: {otu_table.shape[1]} OTUs")

    # Add taxonomy columns
    tax_rows = []
    for otu in otu_table.columns:
        t = taxonomy.get(otu, {})
        tax_rows.append({
            "otu_id": otu,
            "domain": t.get("domain", ""),
            "phylum": t.get("phylum", ""),
            "class":  t.get("class", ""),
            "order":  t.get("order", ""),
            "family": t.get("family", ""),
            "genus":  t.get("genus", ""),
        })
    tax_df = pd.DataFrame(tax_rows).set_index("otu_id")

    # Save OTU table
    otu_out = DATA / "enigma_otu_table.csv"
    otu_table.to_csv(otu_out)
    log.info(f"OTU table saved: {otu_out}")

    # Save taxonomy
    tax_out = DATA / "enigma_otu_taxonomy.csv"
    tax_df.to_csv(tax_out)
    log.info(f"Taxonomy saved: {tax_out}")

    return otu_table, tax_df


# ── Step 6: Build metadata table ──────────────────────────────────────────────
def build_metadata(good_samples: list) -> pd.DataFrame:
    """Extract treatment/well metadata from ENIGMA_ID and BioSample data."""
    log.info("=== Building Sample Metadata ===")
    manifest = pd.read_csv(MANIFEST)

    # Parse ENIGMA_IDs from BioSample (fetched during manifest build)
    # ENIGMA_ID format: EVO09_GP01_20090226_F02_R1
    # → project=EVO09, well=GP01, date=20090226, filter=F02, rep=R1
    meta_records = []
    for srr in good_samples:
        row = manifest[manifest["srr"] == srr]
        if row.empty:
            continue
        row = row.iloc[0]
        spots = int(row.get("spots", 0) or 0)
        enigma_id = ""  # will be enriched from BioSample later if needed
        meta_records.append({
            "srr": srr,
            "spots": spots,
            "biosample": row.get("biosample", ""),
            "sample_acc": row.get("sample_acc", ""),
        })

    meta_df = pd.DataFrame(meta_records).set_index("srr")

    # Save
    meta_out = DATA / "enigma_sample_metadata.csv"
    meta_df.to_csv(meta_out)
    log.info(f"Sample metadata saved: {meta_out}")
    return meta_df


# ── Step 7: Clean up merged reads ─────────────────────────────────────────────
def cleanup_merged():
    log.info("Cleaning up merged FASTQ files...")
    count = 0
    for f in MERGEDIR.glob("*.fastq"):
        f.unlink()
        count += 1
    log.info(f"Deleted {count} merged FASTQ files")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="PRJNA1084851 16S pipeline")
    parser.add_argument("--workers",    type=int, default=16,
                        help="Parallel download+trim+merge workers (default 16)")
    parser.add_argument("--max-samples", type=int, default=None,
                        help="Process only first N samples (for testing)")
    parser.add_argument("--keep-raw",  action="store_true",
                        help="Keep raw FASTQ files after processing")
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip download/trim/merge (use existing merged files)")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("PRJNA1084851 16S Amplicon Pipeline")
    log.info("=" * 60)

    # Step 1: SILVA reference
    global SILVA_FA
    download_silva()
    # Use sintax-formatted SILVA if it was created
    sintax_fa = SILVADIR / "silva138_v4_sintax.fasta"
    if sintax_fa.exists():
        SILVA_FA = sintax_fa

    # Load manifest
    manifest = pd.read_csv(MANIFEST)
    srr_list = manifest["srr"].tolist()
    if args.max_samples:
        srr_list = srr_list[: args.max_samples]
    log.info(f"Samples to process: {len(srr_list)}")

    # Step 2: Download, trim, merge (parallel)
    sample_stats = []
    if not args.skip_download:
        log.info(f"=== Downloading & Processing ({args.workers} workers) ===")
        global _done
        with _lock:
            _done = 0
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {
                ex.submit(process_sample, srr, args.keep_raw): srr
                for srr in srr_list
            }
            for fut in as_completed(futures):
                sample_stats.append(fut.result())
    else:
        log.info("Skipping download (--skip-download). Using existing merged files.")
        for srr in srr_list:
            merged = MERGEDIR / f"{srr}_merged.fastq"
            if merged.exists():
                lines = int(subprocess.check_output(
                    f"wc -l < {merged}", shell=True
                ).decode().strip())
                sample_stats.append({
                    "srr": srr, "status": "ok",
                    "raw_pairs": 0, "trimmed_pairs": 0,
                    "merged": lines // 4, "error": "",
                })

    # Save per-sample stats
    stats_df = pd.DataFrame(sample_stats)
    stats_df.to_csv(WORKDIR / "sample_qc_stats.csv", index=False)
    log.info(f"QC stats: {(stats_df['status'] == 'ok').sum()} / {len(stats_df)} samples passed")

    # Step 3–5: OTU clustering, taxonomy, table
    otus_fa, map_uc, good_samples = cluster_otus(sample_stats)
    taxonomy   = assign_taxonomy(otus_fa)
    otu_table, tax_df = build_otu_table(map_uc, good_samples, taxonomy)
    meta_df    = build_metadata(good_samples)

    # Step 6: Clean up merged reads
    cleanup_merged()

    log.info("=" * 60)
    log.info("Pipeline complete.")
    log.info(f"  Samples processed: {len(good_samples)}")
    log.info(f"  OTUs (after filtering): {otu_table.shape[1]}")
    log.info(f"  Outputs in: {DATA}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
