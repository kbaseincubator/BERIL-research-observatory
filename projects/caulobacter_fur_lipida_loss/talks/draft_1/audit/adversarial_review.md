---
reviewer: BERIL Adversarial Review (Presentation, opus)
type: presentation
date: 2026-06-07
draft_dir: /home/aparkin/BERIL-research-observatory/projects/caulobacter_fur_lipida_loss/talks/draft_1
project_id: caulobacter_fur_lipida_loss
draft_number: 1
prompt_version: adversarial_presentation.v3
tier: STRONG
total_findings: 11
severity_counts:
  P0: 1
  P1: 9
  P2: 0
class_counts:
  throughline: 1
  claim_evidence: 5
  register_drift: 0
  qa_softball: 1
  substory_arc: 2
  citation_reality: 0
  missing_slide: 1
  unbacked_quantitative: 0
  central_objection: 1
---

# Adversarial Review — caulobacter_fur_lipida_loss draft_1

**Reviewer:** beril-adversarial --type presentation v3 (opus)
**Reviewed at:** 2026-06-07T00:00:00Z
**Total findings:** 11 (1 P0, 9 P1, 0 P2, 1 info)

This is a quantitatively well-grounded deck — almost every number on a
slide traces verbatim to REPORT.md, and the substory ordering is
clean. The trouble is in two places: the deck's central rhetorical
move ("partially independent" layers) is not what the data establish,
and the deck's figure curation is broken — load-bearing figures the
throughline explicitly names are missing while one S3-belonging
heatmap is shown twice. The killshot a senior reviewer lands is the
"partially independent" one. The P0 is the missing master synthesis
figure.

## A. Throughline integrity

### P1

**F009 — `throughline` — slide 27 (S6 divider) and propagated.**
Quote: *"Five partially independent layers compose one Caulobacter-specific
program for surviving lipid A loss."* The phrase **PARTIALLY
INDEPENDENT** is doing rhetorical work the evidence does not back.
REPORT supports each layer as a layer against its own threshold, but
no analysis demonstrates any layer could fail while the others
continue to support viability. Layers 1–4 were all measured in the
SAME engineered Δfur Δsspb Δlpxc strain. The experiment that would
establish partial independence — the dual-release genetic
reconstruction — is REPORT §Future Directions §3, NOT YET DONE.
Speaker_notes on slide 27 escalate to flatly hypothesis-as-fact:
*"any one layer could fail without necessarily collapsing the
others."* The throughline overpromises and the body of the deck
cannot honour it.

Fix (in `00_throughline.md`): replace "partially independent" with
"mechanistically distinct" or "five mechanistically distinct layers
(independence pending genetic reconstruction, Future Direction §3)";
propagate the edit to slide 1 subtitle, slide 27 divider, slide 30
deck_close, and slide 27 speaker_notes.

## B. Claim-evidence load-bearing

### P1

**F001 — `claim_evidence` — slide 1 (title).**
Quote: *"Caulobacter Fur Lipida Loss"*. The title slide is the
project slug verbatim and contains a typo — **"Lipida Loss" should
be "Lipid A Loss"**. The subtitle is the throughline punchline
truncated mid-word with an ellipsis (*"Fur-released…"*). Presenter
and affiliation are TBD. For a peer-audience STRONG-tier talk this
is amateur-hour: the first thing the audience reads is "I did not
finish this".

Fix (in `slide_compose.v1.md`): rewrite to a real title — e.g. "A
single envelope catastrophe: five adaptive layers of Caulobacter
Δlpxc tolerance"; de-truncate the subtitle; fill in presenter and
affiliation; at minimum fix "Lipida" → "Lipid A".

**F002 — `claim_evidence` — slide 4 (Approach).**
Quote: *"Approach: fitness ranking, transcript/proteome panel, and
cross-species annotation screen — five mechanism layers."* Bullet 2
lists the panel topics including **"Lpt repurposing"**. REPORT
§Interpretation §5 explicitly classifies the Lpt arm as **MIXED**
(*"Lpt apparatus repurposing in the Δlpxc state shows
transcript-protein discordance (MIXED)"*) with LptD −0.47 and LptE
−0.78 at protein level. The deck's own Q&A slide 32 instructs the
speaker: *"Do not say Lpt is maintained — say transcript is
consistent with Lpt maintenance; protein requires replication."*
The Approach slide commits to delivering "repurposing" that the
body of the deck then has to walk back.

Fix (in `slide_compose.v1.md`): bullet 2 → "...constitutive
sphingolipid state, **candidate Lpt repurposing (transcript-up,
protein discordant)**, and PG remodel (28 loci)" — same
parenthetical the deck already uses on slide 17.

**F003 — `claim_evidence` (cross-cutting) — slide 7 (S1
data_figure).** Quote: *"NB00: sphingolipid biosynthesis is
constitutive across the rescue strain series."* This is the S1
data_figure slot. S1's substory plan explicitly calls for
*"data_figure (R-slide — Fur–Leaden concordance scatter, A1)"* —
i.e. `figures/NB01_fur_signature_scatter.png`, which directly
visualises the ρ=0.315 concordance that anchors Layer 1. Instead
the slide shows the NB00 sphingolipid heatmap — substantively an
**S3 finding**. S1's defining quantitative finding (the Fur–Leaden
concordance) has **no figure** anywhere in the deck. Slide 9 (S1's
claim slide) is bullets-only. Meanwhile this NB00 heatmap is shown
*again* on slide 16 (F005).

Fix (in `slide_compose.v1.md`): replace slide 7's figure with
`figures/NB01_fur_signature_scatter.png`; retitle to "Fur–Leaden
concordance: ρ=0.315, 71% sign agreement across 93 DEGs — and a
buffered respiratory cluster at y≈0"; reduce the NB00 sphingolipid
orientation point to one bullet on slide 6 since slide 16 carries it.

**F004 — `claim_evidence` — slide 7 caption.**
Quote: *"...pathway is constitutive — neither induced nor
suppressed — ruling out Fur-driven sphingolipid biosynthesis
upregulation."* The caption asserts the NB00 figure **"rules out"**
upregulation. The figure is CPM-normalised and descriptive only —
slide 7's own speaker_notes admit *"this orientation figure uses
CPM normalization from NB00 and is descriptive rather than
statistically DE-tested."* The actual statistical evidence (spt
−0.64 FDR 0.002; sphk −0.40 FDR 0.02; 0/6 biosynthesis genes UP at
FDR<0.05) lives in REPORT §Finding 4 and is on slides 16 and 18 of
this deck. A CPM heatmap cannot "rule out" anything; the audience
sees a rule-out claim the visual does not license.

Fix (in `slide_compose.v1.md`): if slide 7 is not replaced per
F003, soften caption to "pathway is flat across strains in NB00
orientation (CPM-descriptive); FDR-tested formal verdict on slide
16 (0/6 UP; spt −0.64 FDR 0.002)."

**F007 — `claim_evidence` — slide 25 (S5 data_figure).**
Quote: *"Sphingolipid pathway and ChvG-ChvI absent in all three
comparators (NCBI-confirmed)."* Title asserts **NCBI-confirmed**;
the figure is `figures/NB06_comparative_heatmap.png` — the
**PaperBLAST** screen (NB06), not the NCBI confirmation (NB06b).
The audience reads "NCBI-confirmed" in the title and is shown the
very method REPORT §NB06b documents as ~80% false-negative for
known Caulobacter lipid A genes (LpxA 0→11, LpxC 0→15, LpxD 0→15,
LpxB 1→18, LpxK 0→18 from PaperBLAST → NCBI). A hostile reviewer
asks "why does your NCBI-confirmed claim use a PaperBLAST
heatmap?" and the speaker has no clean answer.

Fix (in `slide_compose.v1.md`): either (a) render and use an NB06b
NCBI presence/absence heatmap (data exists in
`data/NB06b_ncbi_presence_bool.csv`), or (b) keep the NB06
figure and retitle to "Sphingolipid pathway and ChvG-ChvI absent
in three comparators (PaperBLAST screen, NCBI-confirmed in NB06b)"
with a footer bullet citing the NB06b numbers (spt 7,0,0,0;
ChvG 5,0,0,0).

## C. Tier-language register

No findings in this class. The deck's register is generally honest:
"marginal", "consistent with", "discordant", "REJECTED", "PILOT",
and "directional" all appear in titles and bullets where the
underlying REPORT evidence is weaker than the throughline-favoured
verbs would imply. The over-claiming that exists is structural (the
"partially independent" word in F009 and the "Lpt repurposing" topic
in F002), not lexical, and is captured under the throughline and
claim_evidence classes.

## D. Q&A anti-strawman check

### P1

**F008 — `qa_softball` — slide 33 (Q&A 2).**
Quote: *"Every layer was characterized in PYE rich medium in one
engineered Δfur Δsspb Δlpxc strain background. Does this
five-layer mechanism operate under iron limitation, minimal medium,
or in naturally isolated Caulobacter strains..."* Q&A 2 is the
closest the deck gets to its central weakness — but it ducks the
sharpest version. The throughline asserts five **PARTIALLY
INDEPENDENT** layers. The Q&A asks about *generalisability* (growth
condition, natural suppressors, other alphaproteobacteria) but
never names the load-bearing missing experiment: REPORT §Future
Directions §3, the **dual-release genetic reconstruction** — does
Δlpxc survive in Δfur-alone? in Δsspb-alone? — which is exactly the
test that would distinguish "partially independent layers" from
"five co-occurring facets of one engineered strain". A hostile
reviewer asks "how do you know these are partially INDEPENDENT and
not co-correlated features of one strain you built?" and the deck
has no anticipated answer. The current Q&A 2 answer mentions the
genetic reconstruction inside Axis 2 prose but does not land it as
the operative concession.

Fix (in `qa_anticipated.v1.md`): add a 4th Q&A slide whose question
is the killshot directly — "You frame the rescue as five PARTIALLY
INDEPENDENT adaptive layers, but every layer was measured in the
same engineered strain. How do you distinguish partial independence
from five correlated facets of one strain?" Answer: concede
independence is hypothesis pending the dual-release reconstruction
(Future Direction §3), name the prediction (Δlpxc must fail in
Δfur-alone AND in Δsspb-alone), and cite Layer 5's NCBI absences as
the only independence evidence that doesn't depend on this strain.
Inoculation, not evasion.

The other two Q&A slides (slide 32 on the Lpt protein discordance;
slide 34 on the NCBI naming-convention false-negative risk) are
sharp questions with grounded, honestly-conceded answers. No findings
on those two.

## E. Substory→slide mapping coherence

### P1

**F005 — `substory_arc` — slide 16 (S3 data_figure).**
Quote: *"Sphingolipid biosynthesis is constitutive: 0 of 6 genes UP;
spt and sphk mildly DOWN."* The slide uses
`figures/00_sphingolipid_locus_heatmap.png` — **the same image
already shown on slide 7**. The audience sees the identical heatmap
twice in a 30-slide deck. REPORT and the S3 substory plan
explicitly call for a different figure here:
`figures/NB04_sphingolipid_locus_heatmap.png` (the "Sphingolipid
biosynthesis + Uchendu transporters detailed heatmap" per REPORT
§Figures table). The NB04 figure includes the Uchendu transporter
genes — the load-bearing detail that distinguishes S3's
substitute-mechanism claim from S1's orientation observation. Both
figures exist on disk; the deck uses neither correctly.

Fix (in `slide_compose.v1.md`): replace slide 16 figure with
`figures/NB04_sphingolipid_locus_heatmap.png`. With F003's slide-7
fix applied, no audience member sees the same image twice.

**F006 — `substory_arc` — slide 17 (S3 data_table).**
Quote: *"Lpt transcript upregulated; LptD/LptE protein decline and
CtpA absence define the layer's limits."* S3's substory plan
explicitly calls for this slot to be *"data_figure (R-slide — Lpt
transcript maintained vs protein discordance, A14/A15)"* — the NB04
Lpt apparatus CPM heatmap, `figures/NB04_lpt_apparatus_heatmap.png`.
The deck emits a data_table with no figure. The Lpt heatmap exists
on disk; REPORT §NB04 caption: *"Canonical LPS-transport apparatus
heatmap — MsbA-like CCNA_00307 visibly UP in 4599 vs others"* — i.e.
the visual that would let the audience SEE the discordance.

Fix (in `slide_compose.v1.md`): split slide 17 into a data_figure
(NB04_lpt_apparatus_heatmap.png, caption framed around "maintained
transcript vs protein decline") followed by a smaller data_table for
the lptC2/CtpA pilots and REJECTED verdict. Or convert slide 17
in-place to data_figure and demote the table to caption/footer.

## F. Citation reality

No findings in this class. Each in-text/footer bib-key on the
slides (Zik2022, Leaden2018, Stein2021, QuinteroYanes2022,
Greenwich2023, Tan2025, Yeh2010, Uchendu2026, OleaOzuna2021,
Hummels2024, Kang2021, Steeghs2001, Gao2008, Price2018) resolves
to an entry in `working/citation_pool.json`, each cited paper's
scope-alignment matches the claim it is pinned to, and the
provenance_pin-equivalent `data_source` fields trace to REPORT
sections that contain the cited content. The S5 NB06b / NB06
attribution issue is about which *figure* the slide shows, not
about a fabricated or drifting citation — flagged as F007
(claim_evidence) on figure-claim coherence.

## G. Missing-slide / coverage gaps

### P0

**F010 — `missing_slide` (deck-level) — NB07 master synthesis
figure absent.** The 4-panel master synthesis figure,
`figures/NB07_synthesis_master.png`, is **not shown anywhere in the
deck**. The throughline evidence map (00_throughline.md) lists it
as load-bearing: *"4-panel synthesis master figure (maps the five
layers) | REPORT.md §Key Findings; NB 07_synthesis.ipynb | ✓
direct."* The S6 substory plan calls for *"data_figure (R-slide —
4-panel synthesis master figure + hypothesis scorecard, A26)"* as
the closing R-slide. REPORT §Figures table marks it the
**"recommended Figure 1 for the manuscript"**, and the very first
image embedded in REPORT.md is this figure. The deck has slide 29
(the scorecard table) and slide 30 (deck_close bullets) but **no
visual that unifies the five layers**. The figure exists on disk
and was named as the deck's closing payload — it is simply not
emitted. The audience never sees the architectural picture the
entire 30-slide arc was supposedly building toward.

Fix (in `slide_compose.v1.md`): insert one `data_figure` slide
between current slide 28 (S6 methods) and slide 29 (scorecard
table) with `figure=figures/NB07_synthesis_master.png`,
`title="Five-layer integrated mechanism: how and why Caulobacter
alone tolerates Δlpxc"`, caption naming the four panels and which
substory each panel maps to. Slide 29 (scorecard) then reads as the
evidence ledger supporting the visual; today it stands alone.

## H. Central objection (peer-reviewer killshot)

**F011 — `central_objection` (deck-level, info).** The deck's
central weakness is the load-bearing phrase **"PARTIALLY
INDEPENDENT"** in the throughline punchline. The five layers are
characterised in ONE engineered strain (Δfur Δsspb Δlpxc) under ONE
growth condition (PYE rich medium). The data design establishes
that the layers **co-occur in this strain**; it does NOT establish
that any layer could fail while the others sustain viability. The
single dataset that would test independence — the **dual-release
genetic reconstruction** (Δlpxc on Δfur-alone vs Δsspb-alone) — is
listed in REPORT §Future Directions §3 as not yet performed. Only
Layer 5 (cross-species NCBI absences) provides evidence that
doesn't depend on this strain. A hostile senior reviewer asks:

> "You have shown five co-occurring features of one engineered
> Caulobacter strain. What entitles you to call them PARTIALLY
> INDEPENDENT layers rather than five correlated facets of a single
> stress response? The Δfur-alone and Δsspb-alone reconstructions
> are listed in your own future directions — until they are done,
> the architecture is a hypothesis you have not tested."

The deck does **not** preempt this. Q&A 2 (slide 33) brushes
strain-background in passing under "Axis 2" but never lands the
operative concession; the "partially independent" phrase is
reasserted in the deck_close. The audience extracts the killshot
themselves and the architecture claim collapses to a single-strain
mechanistic description.

Fix (two-step): (1) per F009, retire "partially independent" from
the throughline punchline and its echoes on slides 1, 27, 30 —
replace with "mechanistically distinct" (a defensible adjective the
data support). (2) per F008, add a 4th Q&A slide that names the
dual-release genetic reconstruction as the test that would
establish independence, conceding that the current data co-observe
the layers in one strain. With both fixes the deck closes on "five
mechanistically distinct layers identified; independence test
forthcoming" instead of inviting the killshot.

## Suggested fixes (consolidated)

### `slide_compose.v1.md`
- **F001** (slide 1): rewrite title — "A single envelope
  catastrophe: five adaptive layers of Caulobacter Δlpxc tolerance";
  de-truncate subtitle; fill presenter/affiliation; minimum: fix
  "Lipida" → "Lipid A".
- **F002** (slide 4): bullet 2 → "...constitutive sphingolipid
  state, candidate Lpt repurposing (transcript-up, protein
  discordant), and PG remodel (28 loci)".
- **F003** (slide 7): replace figure with
  `figures/NB01_fur_signature_scatter.png`; retitle to "Fur–Leaden
  concordance: ρ=0.315, 71% sign agreement across 93 DEGs — and a
  buffered respiratory cluster at y≈0".
- **F004** (slide 7): if not replaced per F003, soften caption to
  "pathway is flat across strains in NB00 orientation
  (CPM-descriptive); FDR-tested formal verdict on slide 16".
- **F005** (slide 16): replace figure with
  `figures/NB04_sphingolipid_locus_heatmap.png`.
- **F006** (slide 17): split into data_figure
  (`NB04_lpt_apparatus_heatmap.png`) + smaller data_table for
  lptC2/CtpA, or convert in-place to data_figure and demote table to
  caption/footer.
- **F007** (slide 25): either render an NB06b NCBI heatmap from
  `data/NB06b_ncbi_presence_bool.csv` and swap the figure, OR
  retitle to "Sphingolipid pathway and ChvG-ChvI absent in three
  comparators (PaperBLAST screen, NCBI-confirmed in NB06b)" with a
  footer bullet for the NB06b numbers.
- **F010** (deck-level missing_slide, P0): insert a new data_figure
  slide between slide 28 (S6 methods) and slide 29 (scorecard) with
  `figure=figures/NB07_synthesis_master.png`, title="Five-layer
  integrated mechanism: how and why Caulobacter alone tolerates
  Δlpxc", caption mapping the four panels to substories S1–S5.

### `00_throughline.md`
- **F009** + **F011** (deck-level central_objection): retire
  "partially independent" from the punchline; replace with
  "mechanistically distinct" or "five mechanistically distinct
  layers (independence pending genetic reconstruction, Future
  Direction §3)". Propagate the edit to slide 1 subtitle, slide 27
  divider, slide 30 deck_close, slide 27 speaker_notes, and the
  substory bullets in slide_spec.json.

### `qa_anticipated.v1.md`
- **F008** (slide 33 + new slide): add a 4th Q&A slide naming the
  killshot directly — "You frame the rescue as five PARTIALLY
  INDEPENDENT adaptive layers, but every layer was measured in the
  same engineered strain. How do you distinguish partial
  independence from five correlated facets of one strain?" Answer:
  concede independence is hypothesis pending the dual-release
  reconstruction (Future Direction §3), name the prediction (Δlpxc
  must fail in Δfur-alone AND in Δsspb-alone), and cite Layer 5's
  NCBI absences as the only strain-independent evidence.
