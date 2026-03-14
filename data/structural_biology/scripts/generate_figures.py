#!/usr/bin/env python3
"""
Publication-quality figure generation for structural biology projects.

All rendering is headless (no display required). Gracefully handles
missing matplotlib by printing a warning and returning None.

Usage:
  python generate_figures.py quality-summary --project-dir /path/to/project
  python generate_figures.py plddt-map --model model.pdb --output figures/plddt.png
  python generate_figures.py convergence --project-dir /path/to/project
  python generate_figures.py batch-summary --results-dir results/
  python generate_figures.py strategy-comparison --staging /path/to/staging
"""

import argparse
import json
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def _check_matplotlib():
    if not HAS_MATPLOTLIB:
        print("WARNING: matplotlib not available, skipping figure generation")
        return False
    return True


def generate_plddt_heatmap(pdb_path, output_path="plddt_heatmap.png"):
    """Generate a per-residue pLDDT colored bar from a PDB file.

    Reads B-factor column (pLDDT for AlphaFold models) and creates
    a horizontal bar colored by confidence.
    """
    if not _check_matplotlib():
        return None

    residues = []
    plddt_values = []

    with open(pdb_path) as f:
        for line in f:
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                try:
                    resnum = int(line[22:26].strip())
                    plddt = float(line[60:66].strip())
                    residues.append(resnum)
                    plddt_values.append(plddt)
                except (ValueError, IndexError):
                    pass

    if not residues:
        print(f"WARNING: No CA atoms found in {pdb_path}")
        return None

    fig, ax = plt.subplots(figsize=(max(len(residues) * 0.04, 8), 2))

    # Color map: blue (high) to red (low)
    colors = []
    for p in plddt_values:
        if p >= 90:
            colors.append("#0053D6")  # very high - blue
        elif p >= 70:
            colors.append("#65CBF3")  # high - cyan
        elif p >= 50:
            colors.append("#FFDB13")  # low - yellow
        else:
            colors.append("#FF7D45")  # very low - orange

    ax.bar(residues, plddt_values, color=colors, width=1.0, edgecolor="none")
    ax.set_xlim(min(residues) - 1, max(residues) + 1)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Residue Number")
    ax.set_ylabel("pLDDT")
    ax.set_title(f"AlphaFold Confidence — {os.path.basename(pdb_path)}")
    ax.axhline(90, color="gray", linewidth=0.5, linestyle="--", alpha=0.5)
    ax.axhline(70, color="gray", linewidth=0.5, linestyle="--", alpha=0.5)
    ax.axhline(50, color="gray", linewidth=0.5, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"  Generated {output_path}")
    return output_path


def generate_quality_summary(project_dir, output_path=None):
    """Generate a multi-panel quality summary figure for a project.

    Panels: R-factor convergence, MolProbity convergence, final metrics bar chart.
    """
    if not _check_matplotlib():
        return None

    from refinement_state import ProjectState

    state = ProjectState.load(project_dir)
    metrics = state.cycle_metrics
    if not metrics:
        print("WARNING: No cycle metrics found")
        return None

    if output_path is None:
        figures_dir = os.path.join(project_dir, "figures")
        os.makedirs(figures_dir, exist_ok=True)
        output_path = os.path.join(figures_dir, "quality_summary.png")

    fig = plt.figure(figsize=(14, 5))
    gs = gridspec.GridSpec(1, 3, figure=fig, wspace=0.35)

    cycles = [m["cycle"] for m in metrics]

    # Panel 1: R-factor convergence
    ax1 = fig.add_subplot(gs[0, 0])
    r_work = [m.get("r_work") for m in metrics]
    r_free = [m.get("r_free") for m in metrics]
    has_rfactors = any(v is not None for v in r_free)

    if has_rfactors:
        valid_rw = [(c, v) for c, v in zip(cycles, r_work) if v is not None]
        valid_rf = [(c, v) for c, v in zip(cycles, r_free) if v is not None]
        if valid_rw:
            ax1.plot(*zip(*valid_rw), "b-o", label="R-work", markersize=5)
        if valid_rf:
            ax1.plot(*zip(*valid_rf), "r-o", label="R-free", markersize=5)
        ax1.set_ylabel("R-factor")
        ax1.legend(fontsize=8)
    else:
        cc = [m.get("map_model_cc") for m in metrics]
        valid_cc = [(c, v) for c, v in zip(cycles, cc) if v is not None]
        if valid_cc:
            ax1.plot(*zip(*valid_cc), "g-o", label="Map-Model CC", markersize=5)
        ax1.set_ylabel("Correlation Coefficient")
        ax1.legend(fontsize=8)

    ax1.set_xlabel("Cycle")
    ax1.set_title("Convergence")

    # Panel 2: MolProbity + Clashscore
    ax2 = fig.add_subplot(gs[0, 1])
    mp = [m.get("molprobity_score") for m in metrics]
    clash = [m.get("clash_score") for m in metrics]

    valid_mp = [(c, v) for c, v in zip(cycles, mp) if v is not None]
    valid_clash = [(c, v) for c, v in zip(cycles, clash) if v is not None]

    if valid_mp:
        ax2.plot(*zip(*valid_mp), "m-o", label="MolProbity", markersize=5)
    if valid_clash:
        ax2_twin = ax2.twinx()
        ax2_twin.plot(*zip(*valid_clash), "c-s", label="Clashscore", markersize=5)
        ax2_twin.set_ylabel("Clashscore", color="c")

    ax2.set_xlabel("Cycle")
    ax2.set_ylabel("MolProbity Score", color="m")
    ax2.set_title("Validation Metrics")
    if valid_mp:
        ax2.legend(loc="upper left", fontsize=8)

    # Panel 3: Final metrics bar chart
    ax3 = fig.add_subplot(gs[0, 2])
    final = metrics[-1]

    bar_data = {}
    if final.get("ramachandran_favored") is not None:
        bar_data["Rama Fav (%)"] = final["ramachandran_favored"]
    if final.get("rotamer_outliers") is not None:
        bar_data["Rota Out (%)"] = final["rotamer_outliers"]
    if final.get("ramachandran_outliers") is not None:
        bar_data["Rama Out (%)"] = final["ramachandran_outliers"]

    if bar_data:
        bars = ax3.bar(bar_data.keys(), bar_data.values(),
                       color=["#2ecc71", "#e74c3c", "#e74c3c"])
        ax3.set_ylabel("Percentage")
        ax3.set_title("Final Cycle Metrics")
        for bar, val in zip(bars, bar_data.values()):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                     f"{val:.1f}", ha="center", fontsize=8)

    fig.suptitle(f"Project: {state.project_id}", fontsize=12, y=1.02)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Generated {output_path}")
    return output_path


def generate_batch_histogram(results_dir, output_path=None):
    """Generate distribution histograms from batch validation results.

    Reads batch_stats.json and summary.tsv to create quality distribution plots.
    """
    if not _check_matplotlib():
        return None

    summary_path = os.path.join(results_dir, "summary.tsv")
    if not os.path.exists(summary_path):
        print(f"WARNING: {summary_path} not found")
        return None

    if output_path is None:
        output_path = os.path.join(results_dir, "batch_histogram.png")

    import csv
    plddt_values = []
    n_residues = []

    with open(summary_path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            try:
                plddt_values.append(float(row["mean_plddt"]))
            except (ValueError, KeyError):
                pass
            try:
                n_residues.append(int(row["n_residues"]))
            except (ValueError, KeyError):
                pass

    if not plddt_values:
        print("WARNING: No pLDDT values to plot")
        return None

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # pLDDT distribution
    ax1 = axes[0]
    ax1.hist(plddt_values, bins=20, color="#3498db", edgecolor="white", alpha=0.8)
    ax1.axvline(90, color="green", linewidth=1.5, linestyle="--", label="Very High (90)")
    ax1.axvline(70, color="orange", linewidth=1.5, linestyle="--", label="High (70)")
    ax1.axvline(50, color="red", linewidth=1.5, linestyle="--", label="Low (50)")
    ax1.set_xlabel("Mean pLDDT")
    ax1.set_ylabel("Count")
    ax1.set_title("pLDDT Distribution")
    ax1.legend(fontsize=8)

    # Residue count distribution
    ax2 = axes[1]
    ax2.hist(n_residues, bins=20, color="#2ecc71", edgecolor="white", alpha=0.8)
    ax2.set_xlabel("Number of Residues")
    ax2.set_ylabel("Count")
    ax2.set_title("Protein Size Distribution")

    plt.suptitle(f"Batch Validation Summary (n={len(plddt_values)})")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"  Generated {output_path}")
    return output_path


def generate_strategy_comparison(staging_dir, output_path=None):
    """Generate a bar chart comparing strategies by final R-free across projects."""
    if not _check_matplotlib():
        return None

    from refinement_state import ProjectState

    if output_path is None:
        output_path = os.path.join(staging_dir, "strategy_comparison.png")

    strategy_data = {}

    for entry in os.listdir(staging_dir):
        project_dir = os.path.join(staging_dir, entry)
        notes_path = os.path.join(project_dir, "project_notes.json")
        if not os.path.exists(notes_path):
            continue

        state = ProjectState.load(project_dir)
        if not state.cycle_metrics:
            continue

        # Get final R-free and strategy
        final = state.cycle_metrics[-1]
        r_free = final.get("r_free")
        strategy = final.get("refinement_strategy", "unknown")

        if r_free is not None:
            if strategy not in strategy_data:
                strategy_data[strategy] = []
            strategy_data[strategy].append(r_free)

    if not strategy_data:
        print("WARNING: No strategy data to compare")
        return None

    strategies = sorted(strategy_data.keys())
    means = [sum(strategy_data[s]) / len(strategy_data[s]) for s in strategies]
    counts = [len(strategy_data[s]) for s in strategies]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(range(len(strategies)), means, color="#3498db", edgecolor="white")
    ax.set_xticks(range(len(strategies)))
    ax.set_xticklabels(strategies, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Mean Final R-free")
    ax.set_title("Strategy Comparison by Final R-free")

    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
                f"n={count}", ha="center", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"  Generated {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate publication-quality structural biology figures"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_qs = subparsers.add_parser("quality-summary", help="Multi-panel project summary")
    p_qs.add_argument("--project-dir", required=True)
    p_qs.add_argument("--output", help="Output PNG path")

    p_plddt = subparsers.add_parser("plddt-map", help="Per-residue pLDDT heatmap")
    p_plddt.add_argument("--model", required=True, help="PDB model file")
    p_plddt.add_argument("--output", default="plddt_heatmap.png")

    p_conv = subparsers.add_parser("convergence", help="R-factor convergence plot")
    p_conv.add_argument("--project-dir", required=True)
    p_conv.add_argument("--output", help="Output PNG path")

    p_batch = subparsers.add_parser("batch-summary", help="Batch validation histograms")
    p_batch.add_argument("--results-dir", required=True)
    p_batch.add_argument("--output", help="Output PNG path")

    p_strat = subparsers.add_parser("strategy-comparison", help="Strategy comparison chart")
    p_strat.add_argument("--staging", required=True, help="Staging directory with projects")
    p_strat.add_argument("--output", help="Output PNG path")

    args = parser.parse_args()

    if args.command == "quality-summary":
        generate_quality_summary(args.project_dir, args.output)

    elif args.command == "plddt-map":
        generate_plddt_heatmap(args.model, args.output)

    elif args.command == "convergence":
        from generate_scripts import generate_rfactor_plot
        from refinement_state import ProjectState
        state = ProjectState.load(args.project_dir)
        rfactor_data = [
            {"cycle": m["cycle"], "r_work": m["r_work"], "r_free": m["r_free"]}
            for m in state.cycle_metrics
            if m.get("r_work") is not None and m.get("r_free") is not None
        ]
        if rfactor_data:
            out = args.output or os.path.join(args.project_dir, "figures", "convergence.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            generate_rfactor_plot(rfactor_data, output_path=out)

    elif args.command == "batch-summary":
        generate_batch_histogram(args.results_dir, args.output)

    elif args.command == "strategy-comparison":
        generate_strategy_comparison(args.staging, args.output)


if __name__ == "__main__":
    main()
