"""
Characterise the LLM verdict set: contingency tables, organism breakdown,
confidence distribution, paper-consultation patterns, notable corrections.

Reads:  data/llm_verdicts.jsonl  +  data/ranked_genes.parquet
Writes: data/verdicts_characterisation.md (summary report)
        data/verdicts_with_context.parquet (verdicts joined to ranked features)
        figures/fig01_verdict_distribution.png
        figures/fig02_verdict_by_category.png
        figures/fig03_verdict_by_rank.png
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dossier as dossier_mod  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DIR = REPO_ROOT / "projects" / "fitness_browser_stubborn_set"
PROJECT_DATA = PROJECT_DIR / "data"
FIG_DIR = PROJECT_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

VERDICTS_PATH = PROJECT_DATA / "llm_verdicts.jsonl"
RANKED_PATH = PROJECT_DATA / "ranked_genes.parquet"
OUT_MD = PROJECT_DATA / "verdicts_characterisation.md"
OUT_PARQUET = PROJECT_DATA / "verdicts_with_context.parquet"

VERDICT_COLORS = {
    "already_correctly_named": "#9cb6c2",
    "improvable_new":          "#5b9bd5",
    "improvable_correction":   "#e8a13b",
    "recalcitrant":            "#c44c45",
}
VERDICT_ORDER = ["already_correctly_named", "improvable_new",
                 "improvable_correction", "recalcitrant"]
CATEGORY_ORDER = ["hypothetical", "DUF", "vague", "named_enzyme", "named_other"]


def load_verdicts() -> pd.DataFrame:
    rows = []
    with open(VERDICTS_PATH) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            rows.append(r)
    df = pd.DataFrame(rows)
    return df


def main() -> None:
    verdicts = load_verdicts()
    ranked = pd.read_parquet(RANKED_PATH)
    print(f"Verdicts loaded: {len(verdicts)}")
    print(f"Ranked genes:    {len(ranked)}")

    # Categorise existing gene_desc using the same rules as NB01
    def categorise(desc: str) -> str:
        d = (desc or "").strip().lower()
        if not d or d.startswith("locus ") or d in {"-", ""}:
            return "hypothetical"
        if "hypothetical" in d or "uncharacterized" in d or "unknown function" in d:
            return "DUF" if "duf" in d or "upf" in d else "hypothetical"
        if "duf" in d or "upf" in d:
            return "DUF"
        if any(t in d for t in ("putative", "predicted", "probable", "possible")):
            return "vague"
        enz = ("ase ", "ase,", "ase/", "ase-", "ligase", "reductase", "transporter",
               "kinase", "synthase", "dehydrogenase", "permease", "oxidase",
               "transferase", "hydrolase", "isomerase", "mutase", "polymerase")
        if any(t in d for t in enz) or d.endswith("ase"):
            return "named_enzyme"
        return "named_other"

    ranked["annotation_category"] = ranked["gene_desc"].astype(str).map(categorise)

    # Join verdicts with rank metadata
    df = verdicts.merge(
        ranked[["orgId", "locusId", "rank", "in_specificphenotype",
                "max_abs_fit", "max_abs_t", "fit_x_t", "gene_desc",
                "annotation_category"]],
        on=["orgId", "locusId"],
        how="left",
    )
    df.to_parquet(OUT_PARQUET, index=False)
    print(f"Wrote {OUT_PARQUET}")

    # ---- Top-level distribution
    verdict_counts = df["verdict"].value_counts().reindex(VERDICT_ORDER, fill_value=0)
    confidence_counts = df["confidence"].value_counts()
    n = len(df)
    print(f"\nVerdict distribution (n={n}):")
    for v in VERDICT_ORDER:
        print(f"  {v:30}: {verdict_counts[v]:3d} ({verdict_counts[v]/n*100:.0f}%)")
    print(f"\nConfidence: {dict(confidence_counts)}")

    # ---- Contingency: existing-annotation × verdict
    cont = pd.crosstab(df["annotation_category"], df["verdict"])
    cont = cont.reindex(index=CATEGORY_ORDER, columns=VERDICT_ORDER, fill_value=0)
    print("\nContingency table — existing annotation × verdict:")
    print(cont)

    # ---- Per-organism
    by_org = pd.crosstab(df["orgId"], df["verdict"])
    by_org = by_org.reindex(columns=VERDICT_ORDER, fill_value=0)
    by_org["total"] = by_org.sum(axis=1)
    by_org = by_org.sort_values("total", ascending=False)
    print("\nTop 10 organisms by genes visited:")
    print(by_org.head(10))

    # ---- Paper consultation
    n_with_papers = sum(1 for _, r in df.iterrows() if r.get("papers_consulted") and len(r["papers_consulted"]) > 0)
    total_consults = sum(len(r["papers_consulted"]) if r.get("papers_consulted") else 0 for _, r in df.iterrows())
    unique_pmids = set()
    for _, r in df.iterrows():
        for p in (r.get("papers_consulted") or []):
            unique_pmids.add(str(p))
    print(f"\nPaper consultation: {n_with_papers}/{n} genes ({n_with_papers/n*100:.0f}%); {total_consults} total fetches; {len(unique_pmids)} unique PMIDs")

    # ---- Figure 1: verdict distribution (pie + bar)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    ax = axes[0]
    counts = [verdict_counts[v] for v in VERDICT_ORDER]
    colors = [VERDICT_COLORS[v] for v in VERDICT_ORDER]
    ax.pie(counts, labels=[v.replace("_", "\n") for v in VERDICT_ORDER],
           colors=colors, autopct="%.0f%%", startangle=90, wedgeprops={"edgecolor": "white", "linewidth": 1})
    ax.set_title(f"Verdict distribution (n={n})")

    ax = axes[1]
    confs = ["high", "medium", "low"]
    conf_by_verdict = pd.crosstab(df["verdict"], df["confidence"]).reindex(index=VERDICT_ORDER, columns=confs, fill_value=0)
    bottoms = np.zeros(len(VERDICT_ORDER))
    conf_colors = {"high": "#3b7e3b", "medium": "#d3a73b", "low": "#b34c3b"}
    for c in confs:
        vals = [conf_by_verdict.loc[v, c] for v in VERDICT_ORDER]
        ax.bar(range(len(VERDICT_ORDER)), vals, bottom=bottoms, label=c, color=conf_colors[c], edgecolor="white")
        bottoms = bottoms + np.array(vals)
    ax.set_xticks(range(len(VERDICT_ORDER)))
    ax.set_xticklabels([v.replace("_", "\n") for v in VERDICT_ORDER], fontsize=9)
    ax.set_ylabel("# genes")
    ax.set_title("Verdict × confidence")
    ax.legend(loc="upper right", fontsize=9)
    plt.tight_layout()
    fig_path = FIG_DIR / "fig01_verdict_distribution.png"
    plt.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {fig_path}")

    # ---- Figure 2: verdict by existing-annotation category
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    bottoms = np.zeros(len(CATEGORY_ORDER))
    for v in VERDICT_ORDER:
        vals = [cont.loc[c, v] for c in CATEGORY_ORDER]
        ax.bar(range(len(CATEGORY_ORDER)), vals, bottom=bottoms, label=v, color=VERDICT_COLORS[v], edgecolor="white")
        bottoms = bottoms + np.array(vals)
    ax.set_xticks(range(len(CATEGORY_ORDER)))
    ax.set_xticklabels(CATEGORY_ORDER)
    ax.set_ylabel("# genes")
    ax.set_title("Verdict × existing annotation category")
    ax.legend(loc="upper right", fontsize=9)
    plt.tight_layout()
    fig_path = FIG_DIR / "fig02_verdict_by_category.png"
    plt.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {fig_path}")

    # ---- Figure 3: verdict by rank window
    fig, ax = plt.subplots(1, 1, figsize=(10, 4.5))
    df_sorted = df.sort_values("rank")
    window = 25
    n_windows = (df_sorted["rank"].max() // window) + 1
    by_window = (
        df_sorted.assign(window=(df_sorted["rank"] - 1) // window)
                 .groupby(["window", "verdict"]).size().unstack(fill_value=0)
                 .reindex(columns=VERDICT_ORDER, fill_value=0)
    )
    bottoms = np.zeros(len(by_window))
    x = (by_window.index + 1) * window  # window upper bound for x-axis
    for v in VERDICT_ORDER:
        ax.bar(x, by_window[v].values, bottom=bottoms, width=window * 0.9, label=v, color=VERDICT_COLORS[v], edgecolor="white")
        bottoms = bottoms + by_window[v].values
    ax.set_xlabel("Rank in priority queue (window upper bound, width=25)")
    ax.set_ylabel("# genes in window")
    ax.set_title("Verdict by rank window")
    ax.legend(loc="upper right", fontsize=9)
    plt.tight_layout()
    fig_path = FIG_DIR / "fig03_verdict_by_rank.png"
    plt.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {fig_path}")

    # ---- Markdown summary report
    md = []
    md.append(f"# Verdict characterisation — {n} genes (ranks 1-{int(df['rank'].max())})\n")
    md.append(f"## Verdict distribution\n")
    md.append("| Verdict | n | % |")
    md.append("|---|---:|---:|")
    for v in VERDICT_ORDER:
        md.append(f"| {v} | {verdict_counts[v]} | {verdict_counts[v]/n*100:.0f}% |")
    md.append("")
    md.append(f"**Improvable total** (improvable_new + improvable_correction): "
              f"{verdict_counts['improvable_new'] + verdict_counts['improvable_correction']} "
              f"({(verdict_counts['improvable_new'] + verdict_counts['improvable_correction'])/n*100:.0f}%)")
    md.append("")

    md.append(f"## Confidence × verdict\n")
    md.append("|  | high | medium | low |")
    md.append("|---|---:|---:|---:|")
    for v in VERDICT_ORDER:
        h = conf_by_verdict.loc[v, "high"]
        m = conf_by_verdict.loc[v, "medium"]
        l = conf_by_verdict.loc[v, "low"]
        md.append(f"| {v} | {h} | {m} | {l} |")
    md.append("")

    md.append(f"## Existing annotation × verdict\n")
    md.append("|  | " + " | ".join(VERDICT_ORDER) + " | total |")
    md.append("|---" + "|---:" * (len(VERDICT_ORDER) + 1) + "|")
    for c in CATEGORY_ORDER:
        row = [str(int(cont.loc[c, v])) for v in VERDICT_ORDER]
        md.append(f"| {c} | " + " | ".join(row) + f" | {sum(int(cont.loc[c, v]) for v in VERDICT_ORDER)} |")
    md.append("")

    md.append(f"## Top organisms\n")
    md.append("| orgId | total | improvable | recalcitrant | named_well |")
    md.append("|---|---:|---:|---:|---:|")
    for org, row in by_org.head(15).iterrows():
        impv = row.get("improvable_new", 0) + row.get("improvable_correction", 0)
        md.append(f"| {org} | {row['total']} | {impv} | {row.get('recalcitrant', 0)} | {row.get('already_correctly_named', 0)} |")
    md.append("")

    md.append(f"## Paper consultation\n")
    md.append(f"- {n_with_papers}/{n} genes ({n_with_papers/n*100:.0f}%) had paper consults")
    md.append(f"- {total_consults} total paper fetches")
    md.append(f"- {len(unique_pmids)} unique PMIDs cited")
    md.append("")

    # Notable corrections — improvable_correction with high confidence
    high_corr = df[(df["verdict"] == "improvable_correction") & (df["confidence"] == "high")].copy()
    md.append(f"## Notable corrections — high-confidence improvable_correction (n={len(high_corr)})\n")
    md.append("| rank | orgId::locusId | existing | proposed |")
    md.append("|---:|---|---|---|")
    for _, r in high_corr.sort_values("rank").iterrows():
        existing = (r.get("gene_desc") or "")[:60]
        proposed = (r.get("proposed_annotation") or "")[:60]
        md.append(f"| {int(r['rank'])} | {r['orgId']}::{r['locusId']} | {existing} | {proposed} |")
    md.append("")

    # Recalcitrant
    rec = df[df["verdict"] == "recalcitrant"].copy()
    md.append(f"## Recalcitrant genes (n={len(rec)}) — strong evidence but no proposable annotation\n")
    md.append("| rank | orgId::locusId | existing | rationale |")
    md.append("|---:|---|---|---|")
    for _, r in rec.sort_values("rank").iterrows():
        existing = (r.get("gene_desc") or "")[:50]
        rationale = (r.get("rationale") or "")[:120]
        md.append(f"| {int(r['rank'])} | {r['orgId']}::{r['locusId']} | {existing} | {rationale} |")
    md.append("")

    md.append(f"## Improvable_new (n={int(verdict_counts['improvable_new'])}) — sample of high-confidence proposals\n")
    high_new = df[(df["verdict"] == "improvable_new") & (df["confidence"] == "high")].sort_values("rank").head(20)
    md.append("| rank | orgId::locusId | existing | proposed |")
    md.append("|---:|---|---|---|")
    for _, r in high_new.iterrows():
        existing = (r.get("gene_desc") or "")[:50]
        proposed = (r.get("proposed_annotation") or "")[:60]
        md.append(f"| {int(r['rank'])} | {r['orgId']}::{r['locusId']} | {existing} | {proposed} |")

    with open(OUT_MD, "w") as fh:
        fh.write("\n".join(md))
    print(f"Saved {OUT_MD}")


if __name__ == "__main__":
    main()
