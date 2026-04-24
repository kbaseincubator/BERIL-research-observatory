"""
Convert PaperBLAST kescience_paperblast.uniq parquet (downloaded from MinIO
at s3a://cdm-lake/tenant-sql-warehouse/kescience/kescience_paperblast.db/uniq/
into data/paperblast/uniq_parquet/) to a single FASTA for DIAMOND DB build.

Run:
    python projects/fitness_browser_stubborn_set/notebooks/04_dump_paperblast_sequences.py
"""
import time
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PARQUET_DIR = REPO_ROOT / "data" / "paperblast" / "uniq_parquet"
OUT_PATH = REPO_ROOT / "data" / "paperblast" / "paperblast_uniq.fasta"


def main() -> None:
    t0 = time.time()
    parts = sorted(p for p in PARQUET_DIR.glob("*.parquet"))
    print(f"Found {len(parts)} parquet parts under {PARQUET_DIR}")

    fh = open(OUT_PATH, "w")
    n_total = 0
    for p in parts:
        df = pd.read_parquet(p, columns=["sequence_id", "sequence"])
        for sid, seq in zip(df["sequence_id"].values, df["sequence"].values):
            if not seq:
                continue
            fh.write(f">{sid}\n")
            for i in range(0, len(seq), 60):
                fh.write(seq[i:i+60] + "\n")
        n_total += len(df)
        print(f"[{time.time()-t0:5.1f}s] {p.name}: +{len(df):,}  cumulative {n_total:,}")
    fh.close()
    size_mb = OUT_PATH.stat().st_size / 1e6
    print(f"[{time.time()-t0:5.1f}s] Wrote {OUT_PATH}  ({size_mb:.1f} MB, {n_total:,} sequences)")


if __name__ == "__main__":
    main()
