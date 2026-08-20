#!/usr/bin/env python3
"""
migrate_sections.py

Migrates content from manuscript.tex into manuscript_restructured.tex by
replacing placeholder comment blocks (lines beginning with '% [') with the
corresponding LaTeX text extracted from the original manuscript.

Usage:
    python migrate_sections.py

Output:
    manuscript_restructured.tex  (overwritten in place)
"""

import re
import sys
from pathlib import Path

BASE     = Path(__file__).resolve().parent
OLD_FILE = BASE / "manuscript.tex"
NEW_FILE = BASE / "manuscript_restructured.tex"


# ─── I/O helpers ──────────────────────────────────────────────────────────────

def read(p):  return p.read_text("utf-8")
def write(p, t): p.write_text(t, "utf-8")


def _warn(msg):
    print(f"  WARNING: {msg}", file=sys.stderr)


# ─── Regex helpers ─────────────────────────────────────────────────────────────

def _s(pattern, text, flags=re.DOTALL):
    """Search; return match or None (with a warning on miss)."""
    m = re.search(pattern, text, flags)
    if m is None:
        _warn(f"pattern not found: {pattern[:70]!r}")
    return m


def _between(old, p_start, p_end):
    """Return old[start : end] stripped; empty string on miss."""
    ms, me = _s(p_start, old), _s(p_end, old)
    if ms is None or me is None:
        return ""
    return old[ms.start():me.start()].rstrip()


# ─── Heading stripper ──────────────────────────────────────────────────────────

def strip_heading(text):
    """
    Remove the leading \\section / \\subsection line (possibly multi-line for
    long titles) and any immediately following \\label / \\setcounter lines.
    The new skeleton already provides the correct new headings.
    """
    text = text.lstrip("\n")
    lines = text.split("\n")
    i = 0

    # Drop the \\section* / \\subsection block (ends at the line that closes '}')
    if i < len(lines) and re.match(r"\\(?:section\*?|subsection)\b", lines[i]):
        while i < len(lines):
            closed = re.search(r"\}\s*$", lines[i])
            i += 1
            if closed:
                break

    # Drop \\label{} and \\setcounter{} lines and leading blank lines
    while i < len(lines):
        l = lines[i].strip()
        if re.match(r"\\(?:label|setcounter)\{", l) or l == "":
            i += 1
        else:
            break

    return "\n".join(lines[i:]).lstrip("\n")


# ─── Content extraction from manuscript.tex ────────────────────────────────────

def extract(old):
    """
    Return a dict of named content regions extracted from the original manuscript.
    Keys are used by the MAPPING table below.
    """
    R = {}
    print("Extracting blocks from manuscript.tex …")

    # ── Top-level section anchors ──────────────────────────────────────────────
    m_results  = _s(r"\\section\*\{Results\}", old)
    m_disc     = _s(r"\\section\*\{Discussion\}", old)
    m_methods  = _s(r"\\section\*\{Methods\}", old)
    m_data     = _s(r"\\section\*\{Data and Code Availability\}", old)
    m_ack      = _s(r"\\section\*\{Acknowledgements\}", old)
    m_coi      = _s(r"\\section\*\{Conflict of Interest\}", old)
    m_bib      = _s(r"\\begin\{thebibliography\}", old)
    m_enddoc   = _s(r"\\end\{document\}", old)

    # ── Results subsection anchors ─────────────────────────────────────────────
    m_s2  = _s(r"\\subsection\{Signal is directionally consistent in archaea", old)
    m_s3  = _s(r"\\subsection\{Genome streamlining is pervasive", old)
    m_s4  = _s(r"\\subsection\{Cofactor biosynthesis carries the strongest signal", old)
    m_s5  = _s(r"\\subsection\{Negative controls confirm", old)
    m_s6  = _s(r"\\subsection\{AMI genomic analysis", old)
    m_s7  = _s(r"\\subsection\{No pre-specified confounder", old)
    m_s8  = _s(r"\\subsection\{Signal is consistent within Proteobacteria", old)
    m_s9  = _s(r"\\subsection\{Independent niche-breadth validation", old)
    m_s10 = _s(r"\\subsection\{Community-level metal-gene signal", old)
    m_s11 = _s(r"\\subsection\{Soil-specialist genera", old)
    m_s12 = _s(r"\\subsection\{Gene list structural validation", old)
    m_s13 = _s(r"\\subsection\{Phylogenetic signal at two evolutionary scales", old)
    m_s14 = _s(r"\\subsection\{Exploratory CatBoost LOPO", old)

    # ── Discussion subsection anchors ──────────────────────────────────────────
    m_d1  = _s(r"\\subsection\{Resistance as ecological versatility", old)
    m_d2  = _s(r"\\subsection\{Quantitative evidence for the polarity", old)
    m_d3  = _s(r"\\subsection\{Comparison with prior work", old)
    m_d4  = _s(r"\\subsection\{Partial independent replication", old)
    m_d5  = _s(r"\\subsection\{The split may help reconcile", old)
    m_d6  = _s(r"\\subsection\{Untested predictions", old)
    m_d7  = _s(r"\\subsection\{Limitations\}", old)
    m_d8  = _s(r"\\subsection\{Future directions\}", old)
    m_d9  = _s(r"\\subsection\{Broader implications\}", old)

    # ── Within-section text anchors ────────────────────────────────────────────
    m_central   = _s(r"The central finding of this study is not the magnitude", old)
    m_multiaxis = _s(
        r"\\begin\{figure\*\}\s*\[htbp\]\s*\n"
        r"\\centering\s*\n"
        r"\\includegraphics[^\n]*fig01_multiaxis",
        old,
    )
    m_aggregate = _s(r"The aggregate association between per-Mb", old)

    # §4 internal split anchors
    m_expanded  = _s(r"\\textbf\{Expanded cofactor KO set confirms cobalamin", old)
    m_nonexcl   = _s(r"\\textbf\{Non-exclusive functional classification is robust", old)
    m_nonmetal  = _s(r"\\textbf\{Non-metal cofactor comparison\.", old)
    m_metals    = _s(r"\\textbf\{The effect is uniform across nine metals\.", old)
    m_h4c       = _s(r"\\textbf\{T\. H4c residualised sensitivity analysis\.", old)

    # Discussion internal anchors
    m_d1_p2     = _s(r"The mechanism that generates this polarity", old)
    m_d1_p3     = _s(r"The cofactor constraint operates at the cross-biome scale", old)
    m_d2_p2     = _s(
        r"Resistance and\s+detoxification genes \(106 of 140 primary KOs\)",
        old,
    )
    m_bqh       = _s(
        r"The retention of complete cofactor biosynthesis pathways in ecological\s+"
        r"specialists presents an apparent tension with the Black Queen",
        old,
    )
    m_snb       = _s(r"The phi-coefficient-weighted co-occurrence degree", old)
    m_temporal  = _s(
        r"Viewed through an evolutionary lens, the Australia null is not solely", old
    )
    m_ami_end   = _s(r"The AMI genomic density analysis \(\$\\beta", old)

    # ── Multiaxis figure (extracted verbatim) ──────────────────────────────────
    fig_m = re.search(
        r"(\\begin\{figure\*\}.*?\\label\{fig:multiaxis\}.*?\\end\{figure\*\})",
        old, re.DOTALL,
    )
    R["fig_multiaxis"] = fig_m.group(1) if fig_m else ""

    # ── Introduction paras 3-5 ────────────────────────────────────────────────
    m_p3 = _s(r"Despite the theoretical expectation", old)
    if m_p3 and m_results:
        R["intro_paras_3_5"] = old[m_p3.start():m_results.start()].rstrip()

    # ── Results §1: opening paragraph (central finding / split) ──────────────
    if m_central and m_multiaxis:
        R["results_s1_opening"] = old[m_central.start():m_multiaxis.start()].rstrip()

    # ── Results §1: aggregate β=-0.021 stats + Table 1 ────────────────────────
    if m_aggregate and m_s2:
        R["results_s1_aggregate"] = old[m_aggregate.start():m_s2.start()].rstrip()

    # ── Results §2: archaea + sensitivity ─────────────────────────────────────
    if m_s2 and m_s3:
        R["results_s2"] = strip_heading(old[m_s2.start():m_s3.start()])

    # ── Results §3: landscape (14/19 KEGG, Table 3, Fig 2) ────────────────────
    if m_s3 and m_s4:
        R["results_s3"] = strip_heading(old[m_s3.start():m_s4.start()])

    # ── Results §4: split content (non-contiguous, excludes expanded/nonmetal/h4c) ──
    if all([m_s4, m_expanded, m_nonexcl, m_nonmetal, m_metals, m_h4c, m_s5]):
        # Part 1: heading → expanded cofactor  (opening para + Table 4 + Fig 3 + IQR)
        p1 = strip_heading(old[m_s4.start():m_expanded.start()])
        # Part 2: non-exclusive → non-metal    (non-exclusive, distinctive, permutation,
        #                                        resistance prevalence, cofactor jackknife)
        p2 = old[m_nonexcl.start():m_nonmetal.start()].rstrip()
        # Part 3: metals → h4c                 (metal-specific paragraph + Table 5)
        p3 = old[m_metals.start():m_h4c.start()].rstrip()
        R["results_s4_split"] = p1 + "\n\n" + p2 + "\n\n" + p3

    # ── Results §4: expanded cofactor block (→ §4 Cobalamin Ultimatum) ────────
    if m_expanded and m_nonexcl:
        R["results_s4_expanded"] = old[m_expanded.start():m_nonexcl.start()].rstrip()

    # ── Results §4: non-metal cofactor comparison (→ §4) ──────────────────────
    if m_nonmetal and m_metals:
        R["results_s4_nonmetal"] = old[m_nonmetal.start():m_metals.start()].rstrip()

    # ── Results §4: H4c residualised sensitivity (→ §4) ───────────────────────
    if m_h4c and m_s5:
        R["results_s4_h4c"] = old[m_h4c.start():m_s5.start()].rstrip()

    # ── Results §5: negative controls ─────────────────────────────────────────
    if m_s5 and m_s6:
        R["results_s5"] = strip_heading(old[m_s5.start():m_s6.start()])

    # ── Results §6: AMI/NGSA replication ──────────────────────────────────────
    if m_s6 and m_s7:
        R["results_s6"] = strip_heading(old[m_s6.start():m_s7.start()])

    # ── Results §7: confounders ────────────────────────────────────────────────
    if m_s7 and m_s8:
        R["results_s7"] = strip_heading(old[m_s7.start():m_s8.start()])

    # ── Results §8: clade-stratified ──────────────────────────────────────────
    if m_s8 and m_s9:
        R["results_s8"] = strip_heading(old[m_s8.start():m_s9.start()])

    # ── Results §9: EMP validation ────────────────────────────────────────────
    if m_s9 and m_s10:
        R["results_s9"] = strip_heading(old[m_s9.start():m_s10.start()])

    # ── Results §10: CWM community-level ──────────────────────────────────────
    if m_s10 and m_s11:
        R["results_s10"] = strip_heading(old[m_s10.start():m_s11.start()])

    # ── Results §11: soil-specialist ──────────────────────────────────────────
    if m_s11 and m_s12:
        R["results_s11"] = strip_heading(old[m_s11.start():m_s12.start()])

    # ── Results §12: gene list structural validation ───────────────────────────
    if m_s12 and m_s13:
        R["results_s12"] = strip_heading(old[m_s12.start():m_s13.start()])

    # ── Results §13: phylo-D two scales ───────────────────────────────────────
    if m_s13 and m_s14:
        R["results_s13"] = strip_heading(old[m_s13.start():m_s14.start()])

    # ── Results §14: CatBoost LOPO ─────────────────────────────────────────────
    if m_s14 and m_disc:
        R["results_s14"] = strip_heading(old[m_s14.start():m_disc.start()])

    # ── Discussion §1, paragraph 1 only (up to "The mechanism that generates") ─
    if m_d1 and m_d1_p2:
        R["disc_s1_p1"] = strip_heading(old[m_d1.start():m_d1_p2.start()])

    # ── Discussion §1, paragraph 2 only (two-scale mechanism) ─────────────────
    if m_d1_p2 and m_d1_p3:
        R["disc_s1_p2"] = old[m_d1_p2.start():m_d1_p3.start()].rstrip()

    # ── Discussion §1, paragraphs 3+4 (cofactor cross-biome + streamlining) ───
    if m_d1_p3 and m_d2:
        R["disc_s1_p3_4"] = old[m_d1_p3.start():m_d2.start()].rstrip()

    # ── Discussion §2, paragraph 1 only ("The separation of chromosomal...") ──
    if m_d2 and m_d2_p2:
        R["disc_s2_p1"] = strip_heading(old[m_d2.start():m_d2_p2.start()])

    # ── Discussion §2, paragraphs 2–5 (before BQH paragraph) ─────────────────
    if m_d2_p2 and m_bqh:
        R["disc_s2_p2_5"] = old[m_d2_p2.start():m_bqh.start()].rstrip()

    # ── Discussion §2, BQH paragraph (→ §4 Cobalamin Ultimatum) ──────────────
    if m_bqh and m_d3:
        R["disc_s2_bqh"] = old[m_bqh.start():m_d3.start()].rstrip()

    # ── Discussion §3: von Meijenfeldt SNB paragraph (last para of §3) ────────
    if m_snb and m_d4:
        R["disc_s3_snb"] = old[m_snb.start():m_d4.start()].rstrip()

    # ── Discussion §3: main body (all prior-work paragraphs before SNB) ───────
    if m_d3 and m_snb:
        R["disc_s3_main"] = strip_heading(old[m_d3.start():m_snb.start()])

    # ── Discussion §3: full section (catch-all) ────────────────────────────────
    if m_d3 and m_d4:
        R["disc_s3"] = strip_heading(old[m_d3.start():m_d4.start()])

    # ── Discussion §4: full Australia null section ─────────────────────────────
    if m_d4 and m_d5:
        R["disc_s4"] = strip_heading(old[m_d4.start():m_d5.start()])

    # ── Discussion §4: temporal disconnect paragraph only ─────────────────────
    if m_temporal and m_ami_end:
        R["disc_s4_temporal"] = old[m_temporal.start():m_ami_end.start()].rstrip()

    # ── Discussion §5: split reconciles patterns ───────────────────────────────
    if m_d5 and m_d6:
        R["disc_s5"] = strip_heading(old[m_d5.start():m_d6.start()])

    # ── Discussion §6: untested predictions ───────────────────────────────────
    if m_d6 and m_d7:
        R["disc_s6"] = strip_heading(old[m_d6.start():m_d7.start()])

    # ── Discussion §7: limitations ────────────────────────────────────────────
    if m_d7 and m_d8:
        R["disc_s7"] = strip_heading(old[m_d7.start():m_d8.start()])

    # ── Discussion §8: future directions ──────────────────────────────────────
    if m_d8 and m_d9:
        R["disc_s8"] = strip_heading(old[m_d8.start():m_d9.start()])

    # ── Discussion §9: broader implications ───────────────────────────────────
    if m_d9 and m_methods:
        R["disc_s9"] = strip_heading(old[m_d9.start():m_methods.start()])

    # ── Methods (all 21 subsections) ──────────────────────────────────────────
    if m_methods and m_data:
        R["methods_full"] = strip_heading(old[m_methods.start():m_data.start()])

    # ── Data and Code Availability ────────────────────────────────────────────
    if m_data and m_ack:
        R["data_avail"] = strip_heading(old[m_data.start():m_ack.start()])

    # ── Acknowledgements ──────────────────────────────────────────────────────
    if m_ack and m_coi:
        R["acknowledgements"] = strip_heading(old[m_ack.start():m_coi.start()])

    # ── Conflict of Interest ──────────────────────────────────────────────────
    if m_coi and m_bib:
        R["conflict"] = strip_heading(old[m_coi.start():m_bib.start()])

    # ── Bibliography ──────────────────────────────────────────────────────────
    if m_bib and m_enddoc:
        R["bibliography"] = old[m_bib.start():m_enddoc.start()].rstrip()

    # ── Report ────────────────────────────────────────────────────────────────
    total = sum(len(v) for v in R.values())
    print(f"  {len(R)} regions · {total:,} total chars")
    for k in sorted(R):
        status = f"{len(R[k]):8,}c" if R[k] else "     EMPTY"
        print(f"    {status}  {k}")

    return R


# ─── Placeholder → region mapping ─────────────────────────────────────────────
#
# Each tuple: (substring_to_match_in_placeholder,  region_key_or_tuple_or_None)
#   None  → keep the placeholder as-is (new text must be written by hand)
#   str   → substitute with R[key]
#   tuple → concatenate R[key1] + '\n\n' + R[key2] …
#
# The FIRST matching entry wins; put more-specific patterns before generic ones.

MAPPING = [
    # ── New-text markers (keep as-is) ──────────────────────────────────────────
    ("NEW ABSTRACT",                    None),
    ("NEW PARA 1",                      None),
    ("NEW PARA 2",                      None),
    ("NEW BQH BOUNDARY",                None),
    ("NEW MAG/PLASMID",                 None),
    ("NEW SYNTHESIS PARAGRAPH",         None),
    ("NEW SECTION",                     None),
    ("PLSDB CROSS-REFERENCE",           None),

    # ── Introduction ─────────────────────────────────────────────────────────
    ("Introduction §§3-5",              "intro_paras_3_5"),
    ("Introduction Para 3",             "intro_paras_3_5"),

    # ── §3.1 Streamlining landscape ──────────────────────────────────────────
    ("Results §3",                      "results_s3"),
    ("Results §1 aggregate",            "results_s1_aggregate"),

    # ── §3.2 Cofactor vs resistance split ────────────────────────────────────
    ("Results §1 opening paragraph",    "results_s1_opening"),
    ("Results §1 Para 1",               "results_s1_opening"),

    # ── §3.3 Multi-axis framework ────────────────────────────────────────────
    ("Results §1 multi-axis",           "fig_multiaxis"),
    ("multi-axis summary",              "fig_multiaxis"),

    # ── §4 Cobalamin Ultimatum (specific patterns before generic §4) ──────────
    ('Results §4 "Expanded cofactor',   "results_s4_expanded"),
    ("Expanded cofactor KO set",        "results_s4_expanded"),
    ('Results §4 "H4c',                 "results_s4_h4c"),
    ("H4c residualised",                "results_s4_h4c"),
    ('Results §4 "Non-metal',           "results_s4_nonmetal"),
    ("Non-metal cofactor comparison",   "results_s4_nonmetal"),
    ("Discussion §2 final (BQH)",       "disc_s2_bqh"),   # BQH para → §4

    # ── §3.2 generic §4 catch-all (after specifics above) ─────────────────────
    ("Results §4",                      "results_s4_split"),

    # ── §5 Transient Geochemistry ─────────────────────────────────────────────
    ("Results §14",                     "results_s14"),
    ("CatBoost LOPO",                   "results_s14"),
    ("Results §10",                     "results_s10"),
    ("Community-level metal-gene",      "results_s10"),
    ("Results §6 AMI",                  "results_s6"),
    ("AMI/NGSA section",                "results_s6"),
    ('Discussion §4 "temporal',         "disc_s4_temporal"),
    ("temporal disconnect",             "disc_s4_temporal"),
    ("Results §13",                     "results_s13"),

    # ── Robustness sections ───────────────────────────────────────────────────
    ("Results §2",                      "results_s2"),
    ("Results §7",                      "results_s7"),
    ("Results §8",                      "results_s8"),
    ("Results §9",                      "results_s9"),
    ("Results §11",                     "results_s11"),
    ("Results §12",                     "results_s12"),
    ("Results §5",                      "results_s5"),

    # ── §6.1 Beyond the Black Queen ───────────────────────────────────────────
    ("Discussion §1 paras 1, 3, 4",    ("disc_s1_p1", "disc_s1_p3_4")),
    ("Discussion §1 Para 1",           "disc_s1_p1"),
    ("Discussion §2 paras 2-5",        "disc_s2_p2_5"),
    ("Discussion §2 Para 2",           "disc_s2_p2_5"),

    # ── §6.2 Two-scale evolutionary clock ─────────────────────────────────────
    ("Discussion §1 para 2",           "disc_s1_p2"),
    (r"Discussion §1 ¶2",              "disc_s1_p2"),

    # ── §6.3 Benchmarking / Prior work (specific before generic) ──────────────
    ("Discussion §3 von Meijenfeldt",  "disc_s3_snb"),
    ("von Meijenfeldt SNB",            "disc_s3_snb"),
    ("Discussion §2 para 1",           "disc_s2_p1"),
    ("Discussion §3 prior-work",       "disc_s3_main"),
    ("Comparison with prior work",     "disc_s3"),
    ("Discussion §3",                  "disc_s3"),

    # ── §6.4 Limitations and Future Directions ────────────────────────────────
    ("Discussion §5",                  "disc_s5"),
    ("CONDENSED FROM OLD Discussion §6","disc_s6"),
    ("Discussion §6",                  "disc_s6"),
    ("Discussion §7",                  "disc_s7"),
    ("Discussion §8",                  "disc_s8"),
    ("Discussion §9",                  "disc_s9"),

    # ── Methods and back matter ────────────────────────────────────────────────
    ("CONTENT FROM OLD Methods",       "methods_full"),
    ("OLD Methods",                    "methods_full"),
    ("Data and Code Availability",     "data_avail"),
    ("Acknowledgements",               "acknowledgements"),
    ("Conflict of Interest",           "conflict"),
    ("thebibliography",                "bibliography"),
    ("Bibliography",                   "bibliography"),
]


def _lookup(block_lines, R):
    """
    Given a placeholder comment block (list of lines starting with '% ['),
    return the replacement string or None (keep placeholder as-is).
    """
    block_text = "\n".join(block_lines)

    for pattern, key in MAPPING:
        if pattern in block_text:
            if key is None:
                return None  # new-text marker — keep
            if isinstance(key, tuple):
                parts = [R.get(k, "") for k in key]
                content = "\n\n".join(p for p in parts if p)
            else:
                content = R.get(key, "")

            if content:
                return content
            else:
                _warn(f"region '{key}' is empty — keeping placeholder")
                return None

    # Unrecognised placeholder — leave it alone
    _warn(f"no mapping for: {block_lines[0][:80]!r}")
    return None


# ─── Placeholder replacement ────────────────────────────────────────────────────

def replace(new_text, R):
    """
    Walk manuscript_restructured.tex line by line.  When a contiguous block of
    lines starting with '% [' is found (a placeholder block), replace it with
    the corresponding content.  All other lines pass through unchanged.
    """
    lines = new_text.split("\n")
    out = []
    i = 0
    n_replaced = 0
    n_kept = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detect start of a placeholder block
        if stripped.startswith("% ["):
            # Collect the entire comment block (lines beginning with %)
            ph = []
            while i < len(lines):
                cs = lines[i].strip()
                if cs == "" or (cs and not cs.startswith("%")):
                    break
                ph.append(lines[i])
                i += 1

            replacement = _lookup(ph, R)
            if replacement is not None:
                out.append(replacement)
                n_replaced += 1
            else:
                out.extend(ph)
                n_kept += 1
        else:
            out.append(line)
            i += 1

    print(f"\n  Placeholders replaced: {n_replaced}   kept as-is: {n_kept}")
    return "\n".join(out)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"Reading {OLD_FILE.name} …")
    old = read(OLD_FILE)

    print(f"Reading {NEW_FILE.name} …")
    new_skeleton = read(NEW_FILE)

    regions = extract(old)
    result  = replace(new_skeleton, regions)

    write(NEW_FILE, result)

    n_lines = result.count("\n")
    n_chars = len(result)
    print(f"\nWrote {NEW_FILE.name}  ({n_chars:,} chars, {n_lines:,} lines)")
    print("Done.")


if __name__ == "__main__":
    main()
