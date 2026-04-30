"""
Split EX070 into 5 sub-batches of 5 dossiers each, so we can isolate the
content-policy-flagged dossier(s) and recover verdicts for the other 24+.

Reads:  data/expansion/batches_claude/batch_EX070/input.md
        data/expansion/batches_claude/batch_EX070/manifest.csv
Writes: data/expansion/batches_claude/batch_EX070A/{input.md,manifest.csv,prompt.txt placeholder}
        ... batch_EX070B, EX070C, EX070D, EX070E
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PD = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
SRC = PD / "expansion" / "batches_claude" / "batch_EX070"
SRC_CX = PD / "expansion" / "batches_codex" / "batch_EX070"
PER_SUB = 5  # 25 / 5 = 5 sub-batches


def parse_dossiers(input_md: str) -> list[tuple[str, str]]:
    """Return list of (header, body) per dossier."""
    parts = re.split(r'(^## Dossier \d+/\d+ — [^\n]+\n)', input_md, flags=re.M)
    out: list[tuple[str, str]] = []
    i = 1
    while i < len(parts) - 1:
        head = parts[i]
        body = parts[i+1]
        out.append((head.strip(), body))
        i += 2
    return out


def main() -> None:
    text = (SRC / "input.md").read_text()
    dossiers = parse_dossiers(text)
    if len(dossiers) != 25:
        print(f"WARNING: expected 25 dossiers, got {len(dossiers)}", file=sys.stderr)

    # Read manifest for parallel chunking
    manifest = list(csv.DictReader(open(SRC / "manifest.csv")))
    if len(manifest) != len(dossiers):
        print(f"WARNING: manifest rows={len(manifest)} dossiers={len(dossiers)}", file=sys.stderr)

    suffixes = ["A", "B", "C", "D", "E"]
    for chunk_i in range(5):
        sub_id = f"EX070{suffixes[chunk_i]}"
        sub_doss = dossiers[chunk_i*PER_SUB : (chunk_i+1)*PER_SUB]
        sub_man = manifest[chunk_i*PER_SUB : (chunk_i+1)*PER_SUB]

        body_lines = [f"# Sub-batch {sub_id} — {len(sub_doss)} of 25 dossiers from EX070\n"]
        for j, (head, body) in enumerate(sub_doss, 1):
            # Renumber heading
            body_lines.append(f"## Dossier {j}/{len(sub_doss)} — " +
                              head.split(" — ", 1)[1].strip() + "\n")
            body_lines.append(body)
        body = "\n".join(body_lines)

        for parent in (PD/"expansion"/"batches_claude", PD/"expansion"/"batches_codex"):
            d = parent / f"batch_{sub_id}"
            d.mkdir(parents=True, exist_ok=True)
            (d/"input.md").write_text(body)
            with open(d/"manifest.csv", "w", newline="") as fh:
                fields = list(sub_man[0].keys())
                w = csv.DictWriter(fh, fieldnames=fields, delimiter=",")
                w.writeheader(); w.writerows(sub_man)

        gene_ids = [head.split(" — ", 1)[1].strip() for head, _ in sub_doss]
        print(f"  {sub_id}: {gene_ids}", file=sys.stderr)


if __name__ == "__main__":
    main()
