"""SPIRE data client — per-sample eggnog download and per-MAG contig mapping.

Confirmed endpoints (both return 200 OK):
    GET https://spire.embl.de/download_eggnog/{SAMPLE_ID}
        gzip binary: eggNOG mapper annotations TSV for all MAGs in sample.
        Format: ## comment lines, then '#query\t...\tKEGG_ko\t...' header, then TSV rows.
        query field = "{contig_name}_{gene_index}" — strip last '_N' to get contig name.

    GET https://spire.embl.de/download_file/{MAG_ID}
        gzip binary: FASTA of all contigs assigned to this MAG.
        Contig names = FASTA header text after '>'.

Parallel workflow in batch_compute_ko_counts:
  Each sample runs a pipeline: fetch its MAG contig sets concurrently, then
  immediately download eggnog and count KOs — no global barrier between phases.
  All samples run this pipeline concurrently via an outer ThreadPoolExecutor.
  Cached files (contigs ~1 KB, eggnog ~36 MB) are skipped on re-runs.
"""

from __future__ import annotations

import gzip
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO, StringIO
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

log = logging.getLogger(__name__)

EGGNOG_DOWNLOAD_URL = "https://spire.embl.de/download_eggnog/{sample_id}"
MAG_FILE_URL = "https://spire.embl.de/download_file/{mag_id}"

# Legacy endpoint (kept for probe compatibility)
BASE_URL = "https://spire.embl.de/spire/api"
ANNOTATIONS_ENDPOINT = BASE_URL + "/sample/{sample_id}?format=tsv"

MAX_RETRIES = 2
BACKOFF_BASE = 2.0
DEFAULT_WORKERS = 20    # concurrent HTTP connections


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def _parse_eggnog_gzip(data: bytes) -> pd.DataFrame:
    """Decompress and parse a SPIRE eggnog gzip download into a DataFrame."""
    with gzip.open(BytesIO(data)) as fh:
        raw = fh.read().decode("utf-8", errors="replace")

    lines = raw.splitlines()
    header_idx: Optional[int] = None
    for i, line in enumerate(lines):
        if line.startswith("#query"):
            header_idx = i
            break

    if header_idx is None:
        log.warning("No '#query' header found in eggnog gzip")
        return pd.DataFrame()

    col_line = lines[header_idx].lstrip("#")
    data_lines = [
        l for l in lines[header_idx + 1:]
        if l.strip() and not l.startswith("#")
    ]

    tsv_text = col_line + "\n" + "\n".join(data_lines)
    return pd.read_csv(StringIO(tsv_text), sep="\t", low_memory=False)


def _parse_mag_fasta_gzip(data: bytes) -> frozenset:
    """Extract contig names from a SPIRE MAG FASTA gzip download."""
    with gzip.open(BytesIO(data)) as fh:
        raw = fh.read().decode("utf-8", errors="replace")
    return frozenset(
        line[1:].split()[0] for line in raw.splitlines() if line.startswith(">")
    )


def _parse_mag_fasta_with_stats(data: bytes) -> tuple[frozenset, dict]:
    """Parse SPIRE MAG FASTA gzip → (frozenset of names, dict of {name: (length, gc)}).

    Returns contig names and per-contig statistics (length in bp, GC fraction).
    """
    with gzip.open(BytesIO(data)) as fh:
        raw = fh.read().decode("utf-8", errors="replace")

    stats: dict[str, tuple[int, float]] = {}
    current_name: Optional[str] = None
    current_seq: list[str] = []

    def _record():
        if current_name is None:
            return
        seq = "".join(current_seq).upper()
        length = len(seq)
        gc = (seq.count("G") + seq.count("C")) / length if length > 0 else 0.0
        stats[current_name] = (length, gc)

    for line in raw.splitlines():
        if line.startswith(">"):
            _record()
            current_name = line[1:].split()[0]
            current_seq = []
        elif current_name is not None:
            current_seq.append(line.strip())
    _record()

    return frozenset(stats.keys()), stats


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class SPIREClient:
    """Download and cache SPIRE per-sample eggnog annotations and per-MAG contig sets.

    Thread-safe: multiple workers can call download/get methods concurrently.
    Rate limiting is removed in favour of max_workers concurrency cap.
    """

    def __init__(self, cache_dir: str | Path = "data/spire_cache"):
        self.cache_dir = Path(cache_dir)
        self._eggnog_dir = self.cache_dir / "eggnog"
        self._contig_dir = self.cache_dir / "mag_contigs"
        self._eggnog_dir.mkdir(parents=True, exist_ok=True)
        self._contig_dir.mkdir(parents=True, exist_ok=True)
        # Per-path write locks so concurrent threads don't race on the same cache file
        self._write_locks: dict[str, threading.Lock] = {}
        self._lock_registry = threading.Lock()

    def _write_lock(self, path: Path) -> threading.Lock:
        key = str(path)
        with self._lock_registry:
            if key not in self._write_locks:
                self._write_locks[key] = threading.Lock()
            return self._write_locks[key]

    # ------------------------------------------------------------------
    # HTTP fetch (no rate limit — rely on max_workers for throttling)
    # ------------------------------------------------------------------

    def _fetch(self, url: str, timeout: tuple = (10, 30),
               max_total_secs: int = 120) -> Optional[bytes]:
        """GET url with retries; return raw bytes or None.

        Uses streaming with a hard wall-clock deadline so servers that trickle
        bytes never hold a worker thread indefinitely.
        """
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = requests.get(url, timeout=timeout, stream=True)
                if resp.status_code == 200:
                    deadline = time.time() + max_total_secs
                    chunks = []
                    for chunk in resp.iter_content(chunk_size=512 * 1024):
                        if time.time() > deadline:
                            resp.close()
                            raise requests.exceptions.Timeout(
                                f"total timeout ({max_total_secs}s) for {url}"
                            )
                        if chunk:
                            chunks.append(chunk)
                    return b"".join(chunks)
                elif resp.status_code == 404:
                    log.debug("404 for %s", url)
                    return None
                elif resp.status_code == 429:
                    wait = BACKOFF_BASE ** attempt
                    log.warning("429 rate-limited for %s — waiting %.1fs", url, wait)
                    time.sleep(wait)
                    continue
                else:
                    log.warning("HTTP %s for %s (attempt %d/%d)", resp.status_code, url, attempt, MAX_RETRIES)
            except Exception as exc:
                log.warning("Request error %s (attempt %d/%d): %s", url, attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_BASE ** attempt)
        log.error("All retries exhausted for %s", url)
        return None

    # ------------------------------------------------------------------
    # Per-sample eggnog
    # ------------------------------------------------------------------

    def _eggnog_cache_path(self, sample_id: str) -> Path:
        return self._eggnog_dir / f"{sample_id}.gz"

    def fetch_eggnog_bytes(self, sample_id: str) -> Optional[bytes]:
        """Download eggnog gzip bytes for sample_id without saving to disk.

        Use this when the caller will process and store results in a different
        format (e.g., per-sample parquet KO counts).
        """
        url = EGGNOG_DOWNLOAD_URL.format(sample_id=sample_id)
        return self._fetch(url, timeout=(10, 30), max_total_secs=180)

    def download_eggnog_for_sample(self, sample_id: str) -> Optional[pd.DataFrame]:
        """Return parsed eggnog DataFrame for sample_id; uses disk cache."""
        cache_path = self._eggnog_cache_path(sample_id)
        if cache_path.exists():
            return _parse_eggnog_gzip(cache_path.read_bytes())

        url = EGGNOG_DOWNLOAD_URL.format(sample_id=sample_id)
        # (connect_timeout, read_timeout): read_timeout is per-chunk, not total.
        # Keeps the download alive as long as data keeps flowing, but bails fast
        data = self._fetch(url, timeout=(10, 30), max_total_secs=180)
        if data is None:
            return None

        with self._write_lock(cache_path):
            if not cache_path.exists():   # double-check after acquiring lock
                cache_path.write_bytes(data)
                log.info("Cached eggnog for %s (%d KB)", sample_id, len(data) // 1024)
        return _parse_eggnog_gzip(data)

    # ------------------------------------------------------------------
    # Per-MAG contig set
    # ------------------------------------------------------------------

    def _contig_cache_path(self, mag_id: str) -> Path:
        return self._contig_dir / f"{mag_id}.txt"

    def _contig_stats_path(self, mag_id: str) -> Path:
        return self._contig_dir / f"{mag_id}.stats"

    def get_mag_contig_set(self, mag_id: str) -> Optional[frozenset]:
        """Return frozenset of contig names for mag_id; uses disk cache.

        Cache stores contig names (one per line, ~1 KB) in a .txt file and
        per-contig stats (length, gc) in a .stats TSV sidecar on new downloads.
        Thread-safe: concurrent calls for different mag_ids run in parallel.
        """
        cache_path = self._contig_cache_path(mag_id)
        if cache_path.exists():
            return frozenset(l for l in cache_path.read_text().splitlines() if l)

        url = MAG_FILE_URL.format(mag_id=mag_id)
        data = self._fetch(url, timeout=(10, 20), max_total_secs=60)
        if data is None:
            return None

        contigs, stats = _parse_mag_fasta_with_stats(data)
        with self._write_lock(cache_path):
            if not cache_path.exists():
                cache_path.write_text("\n".join(sorted(contigs)))
                # Save per-contig stats sidecar: contig\tlength\tgc
                stats_path = self._contig_stats_path(mag_id)
                lines = ["contig\tlength\tgc"] + [
                    f"{name}\t{length}\t{gc:.6f}"
                    for name, (length, gc) in sorted(stats.items())
                ]
                stats_path.write_text("\n".join(lines))
        return contigs

    def get_mag_contig_stats(self, mag_id: str) -> Optional[pd.DataFrame]:
        """Return DataFrame of contig stats (name, length, gc) for mag_id.

        Returns None if the stats sidecar does not exist (MAG was cached before
        stats capture was added). Re-download to populate: delete the .txt cache
        and call get_mag_contig_set() again.
        """
        stats_path = self._contig_stats_path(mag_id)
        if not stats_path.exists():
            return None
        return pd.read_csv(stats_path, sep="\t")

    # ------------------------------------------------------------------
    # Batch: parallel KO count computation
    # ------------------------------------------------------------------

    def batch_compute_ko_counts(
        self,
        mag_meta_df: pd.DataFrame,
        primary_kos: frozenset,
        subcat_kos: dict,
        max_samples: Optional[int] = None,
        max_workers: int = DEFAULT_WORKERS,
    ) -> pd.DataFrame:
        """Compute per-MAG KO counts.

        Phase 1 — prefetch all MAG contig sets in parallel (cached ~1 KB files).
        Phase 2 — process samples in parallel: download eggnog + count KOs per MAG.
                   Contigs are read from disk cache; no re-download needed.
        """
        from mag_utils import normalise_ko_ids

        sample_groups = mag_meta_df.groupby("sample_id")["mag_id"].apply(list).to_dict()
        if max_samples is not None:
            sample_groups = dict(list(sample_groups.items())[:max_samples])

        all_mag_ids = [mid for mids in sample_groups.values() for mid in mids]
        n_samples = len(sample_groups)

        # ------------------------------------------------------------------
        # Phase 1: prefetch contig sets
        # ------------------------------------------------------------------
        try:
            from tqdm.auto import tqdm
        except ImportError:
            tqdm = None

        n_cached = sum(1 for mid in all_mag_ids if self._contig_cache_path(mid).exists())
        print(f"Phase 1: {len(all_mag_ids):,} contig sets ({n_cached:,} cached, "
              f"{len(all_mag_ids)-n_cached:,} to fetch)...")

        def _fetch_contig(mid):
            self.get_mag_contig_set(mid)

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            itr = ex.map(_fetch_contig, all_mag_ids)
            if tqdm is not None:
                itr = tqdm(itr, total=len(all_mag_ids), desc="Phase 1 contigs", unit="MAG")
            list(itr)
        print("Phase 1 complete.")

        # ------------------------------------------------------------------
        # Phase 2: parallel sample processing
        # ------------------------------------------------------------------
        print(f"Phase 2: processing {n_samples:,} samples...")

        def _process_sample(args):
            sample_id, mag_ids = args
            eggnog_df = self.download_eggnog_for_sample(sample_id)
            if eggnog_df is None or eggnog_df.empty or "query" not in eggnog_df.columns:
                return []
            eggnog_df = eggnog_df.copy()
            eggnog_df["contig"] = eggnog_df["query"].str.rsplit("_", n=1).str[0]

            records = []
            for mag_id in mag_ids:
                contigs = self.get_mag_contig_set(mag_id)   # disk cache: fast
                if contigs is None:
                    continue
                mask = eggnog_df["contig"].isin(contigs)
                ko_series = (eggnog_df.loc[mask, "KEGG_ko"] if mask.any()
                             else pd.Series(dtype=str))
                ko_set: set = set()
                for raw in ko_series.dropna():
                    ko_set.update(normalise_ko_ids(str(raw)))
                row: dict = {"mag_id": mag_id, "n_ko_primary": len(ko_set & primary_kos)}
                for cat, cat_kos in subcat_kos.items():
                    col = "n_ko_" + cat.lower().replace(" ", "_").replace("/", "_")
                    row[col] = len(ko_set & cat_kos)
                records.append(row)
            return records

        all_records = []
        all_records_lock = threading.Lock()

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_process_sample, item): item[0]
                       for item in sample_groups.items()}
            itr = as_completed(futures)
            if tqdm is not None:
                itr = tqdm(itr, total=n_samples, desc="Phase 2 samples", unit="sample")
            for future in itr:
                result = future.result()
                if result:
                    with all_records_lock:
                        all_records.extend(result)

        print(f"Phase 2 complete: {len(all_records):,} MAGs with KO data.")
        log.info("Finished: %d MAGs with KO data from %d samples", len(all_records), n_samples)
        return pd.DataFrame(all_records) if all_records else pd.DataFrame()

    # ------------------------------------------------------------------
    # Endpoint probe
    # ------------------------------------------------------------------

    def probe_endpoints(self) -> dict:
        """Return reachability status of SPIRE download endpoints."""
        results = {}
        for name, url in [
            # SAMEA104408696 confirmed 200; SAMEA2619158 has no eggnog download (404)
            ("eggnog_download", EGGNOG_DOWNLOAD_URL.format(sample_id="SAMEA104408696")),
            ("mag_file", MAG_FILE_URL.format(mag_id="spire_mag_00000001")),
            ("api_sample", ANNOTATIONS_ENDPOINT.format(sample_id="SAMEA2619158")),
        ]:
            try:
                resp = requests.head(url, timeout=15)
                results[name] = {"status": resp.status_code, "url": url}
            except Exception as exc:
                results[name] = {"status": "error", "error": str(exc), "url": url}
        return results

    def cache_stats(self) -> dict:
        n_eggnog = len(list(self._eggnog_dir.glob("*.gz")))
        n_contigs = len(list(self._contig_dir.glob("*.txt")))
        return {
            "n_eggnog_cached": n_eggnog,
            "n_contig_sets_cached": n_contigs,
            "cache_dir": str(self.cache_dir),
        }
