#!/usr/bin/env python3
"""
Recovery script for the 52 PRJNA1084851 samples that returned 404 on ENA FTP.
Uses fasterq-dump (NCBI SRA toolkit) to download directly from NCBI.
Produces merged FASTQ files in the same location as the main pipeline.
"""

import sys, os, subprocess, shutil, threading, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

FASTERQ = "/tmp/sratoolkit.3.4.1-ubuntu64/bin/fasterq-dump"

PROJECT  = Path(__file__).parent.parent
DATA     = PROJECT / "data"
WORKDIR  = DATA / "prjna1084851"
FASTQDIR = WORKDIR / "fastq"
TRIMDIR  = WORKDIR / "trimmed"
MERGEDIR = WORKDIR / "merged"
for d in [FASTQDIR, TRIMDIR, MERGEDIR]: d.mkdir(exist_ok=True)

FWD_PRIMER = "GTGYCAGCMGCCGCGGTAA"
REV_PRIMER = "GGACTACNVGGGTWTCTAAT"

_lock = threading.Lock()
_done = 0

def process_failed(srr: str, total: int) -> dict:
    global _done
    stats = {"srr": srr, "status": "ok", "raw_pairs": 0,
             "trimmed_pairs": 0, "merged": 0, "error": ""}

    tmpdir  = WORKDIR / f"tmp_{srr}"
    r1_raw  = tmpdir / f"{srr}_1.fastq"
    r2_raw  = tmpdir / f"{srr}_2.fastq"
    trim1   = TRIMDIR / f"{srr}_1_trimmed.fastq.gz"
    trim2   = TRIMDIR / f"{srr}_2_trimmed.fastq.gz"
    merged  = MERGEDIR / f"{srr}_merged.fastq"

    # Skip if already merged
    if merged.exists() and merged.stat().st_size > 10000:
        lines = int(subprocess.check_output(f"wc -l < {merged}", shell=True).decode().strip())
        stats["merged"] = lines // 4
        with _lock:
            _done += 1
            print(f"  [{_done}/{total}] {srr}: already merged ({stats['merged']:,} reads) [skip]",
                  flush=True)
        return stats

    try:
        tmpdir.mkdir(exist_ok=True)

        # ── fasterq-dump ────────────────────────────────────────────────────
        result = subprocess.run(
            [FASTERQ, srr, "--outdir", str(tmpdir),
             "--threads", "4", "--split-files", "--temp", str(tmpdir)],
            capture_output=True, text=True, timeout=600,
        )
        if result.returncode != 0:
            raise RuntimeError(f"fasterq-dump failed: {result.stderr[-500:]}")
        if not r1_raw.exists() or not r2_raw.exists():
            raise RuntimeError("Expected _1.fastq/_2.fastq not produced")

        stats["raw_pairs"] = int(
            subprocess.check_output(f"wc -l < {r1_raw}", shell=True).decode().strip()
        ) // 4

        # ── cutadapt ────────────────────────────────────────────────────────
        subprocess.run([
            "cutadapt",
            "-g", FWD_PRIMER, "-G", REV_PRIMER,
            "--discard-untrimmed", "--minimum-length", "100", "--cores", "2",
            "-o", str(trim1), "-p", str(trim2),
            str(r1_raw), str(r2_raw),
        ], capture_output=True, check=True)

        stats["trimmed_pairs"] = int(
            subprocess.check_output(f"zcat {trim1} | wc -l", shell=True).decode().strip()
        ) // 4

        if stats["trimmed_pairs"] < 500:
            raise RuntimeError(f"Too few trimmed reads: {stats['trimmed_pairs']}")

        # ── vsearch merge ───────────────────────────────────────────────────
        subprocess.run([
            "vsearch",
            "--fastq_mergepairs", str(trim1), "--reverse", str(trim2),
            "--fastqout", str(merged),
            "--fastq_minovlen", "50", "--fastq_maxdiffs", "5",
            "--fastq_minlen", "200", "--fastq_maxlen", "300",
            "--threads", "2",
        ], capture_output=True, check=True)

        stats["merged"] = int(
            subprocess.check_output(f"wc -l < {merged}", shell=True).decode().strip()
        ) // 4

        if stats["merged"] < 100:
            raise RuntimeError(f"Too few merged reads: {stats['merged']}")

    except Exception as e:
        stats["status"] = "failed"
        stats["error"] = str(e)[:200]
        for f in [merged]: f.unlink(missing_ok=True)
    finally:
        # Always clean up temp and trimmed files
        shutil.rmtree(tmpdir, ignore_errors=True)
        trim1.unlink(missing_ok=True)
        trim2.unlink(missing_ok=True)

    with _lock:
        _done += 1
        print(f"  [{_done}/{total}] {srr}: raw={stats['raw_pairs']:,} "
              f"trimmed={stats['trimmed_pairs']:,} merged={stats['merged']:,} "
              f"[{stats['status']}]", flush=True)
    return stats


def main():
    qc = pd.read_csv(WORKDIR / "sample_qc_stats.csv")
    failed = sorted(qc[qc["status"] == "failed"]["srr"].tolist())
    total = len(failed)
    print(f"Recovering {total} failed samples via fasterq-dump...")
    print(f"fasterq-dump: {FASTERQ}")

    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    print(f"Workers: {workers}\n")

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(process_failed, srr, total): srr for srr in failed}
        results = [f.result() for f in as_completed(futures)]

    results_df = pd.DataFrame(results)
    ok = (results_df["status"] == "ok").sum()
    print(f"\nRecovered: {ok}/{total}")
    results_df.to_csv(WORKDIR / "recovery_qc_stats.csv", index=False)
    print(f"Stats saved: {WORKDIR}/recovery_qc_stats.csv")


if __name__ == "__main__":
    main()
