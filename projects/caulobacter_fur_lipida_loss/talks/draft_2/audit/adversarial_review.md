---
reviewer: BERIL Adversarial Review (Presentation, opus)
type: presentation
date: 2026-06-08
draft_dir: /home/aparkin/BERIL-research-observatory/projects/caulobacter_fur_lipida_loss/talks/draft_2
project_id: caulobacter_fur_lipida_loss
draft_number: 2
prompt_version: adversarial_presentation.v3
tier: STRONG
total_findings: 11
severity_counts:
  P0: 0
  P1: 6
  P2: 4
class_counts:
  throughline: 0
  claim_evidence: 3
  register_drift: 1
  qa_softball: 1
  substory_arc: 2
  citation_reality: 2
  missing_slide: 1
  unbacked_quantitative: 0
  central_objection: 1
---

# Adversarial Review — caulobacter_fur_lipida_loss draft_2

**Reviewer:** beril-adversarial --type presentation v3 (opus)
**Reviewed at:** 2026-06-08T00:00:00Z
**Total findings:** 11 (0 P0, 6 P1, 4 P2) + 1 info (central objection)

**Orienting note (not praise — calibration):** This deck is numerically
honest. Every load-bearing number traces verbatim to REPORT.md
(ρ=0.315, 33.25% background, Path A 1.60×/p=0.016, Path B 1.04×/p=0.515,
spt −0.64 / sphk −0.40), and the deck volunteers its own REJECTED and
PARTIAL pre-registration grades. There are therefore **zero
unbacked_quantitative findings and zero P0 findings**. The exposure is
not fabricated data — it is (1) a placeholder-grade title/acks/refs
layer that will embarrass the speaker in a senior room, (2) one
register overclaim, (3) a buried "which genes" answer, and (4) a
single deep narrative soft spot: the word **driver** is licensed by
Zik 2022, not by this project's own (correlational, marginal) new
evidence. Fix the narrative framing and the placeholder layer and the
deck is defensible.

## A. Throughline integrity

No throughline-integrity findings. Each substory delivers a
load-bearing punchline traceable to the evidence map (S1 Leaden
concordance + strain contrast; S2 Path A over calibrated background
with Path B falling out; S3 ChvI/sphingolipid/PG as downstream
consequences). The throughline's honesty about ✗-contradicts rows
(A7 SspB arm, A10 SigU-as-driver, A13 CtpA) carries into the deck as
explicit limitations slides rather than being buried. The deepest
problem with the spine is not integrity but the causal load on the
word "driver" — that is escalated as the single central objection in
section H, not here.

## B. Claim-evidence load-bearing

### P1

**F002 (Slide 1, title) — placeholder title slide ships embarrassments.**
The title "Caulobacter Fur Lipida Loss" is a degenerate auto-title
from the directory name: "Lipida" is a non-word; the subject is
"lipid A," per REPORT's own title "The regulatory and proteomic
architecture of Δ*fur*-permitted lipid A loss in *Caulobacter
crescentus*." presenter and affiliation are both literal "TBD." The
subtitle is truncated mid-sentence ("…and everything…"). The first
slide a senior room sees signals an unfinished deck and a garbled
subject noun. *Fix:* real title (e.g. "Δfur derepression drives the
lipid A-loss-permissive envelope state in Caulobacter crescentus"),
populate presenter/affiliation, complete or cleanly truncate the
subtitle.

### P2

**F008 (Slide 10, methods_summary) — tool versions are literal
"unknown."** Slide 10 lists Fitness Browser "unknown"; slide 14
edgeR "unknown"; same pattern on slides 18/24 (Biopython, PaperBLAST).
For a reproducibility-minded peer audience, "version: unknown" on the
statistical engine (edgeR) and the fitness compendium undercuts the
deck's otherwise-strong pre-registration discipline. *Fix:* populate
real versions, or state an access date where a version is genuinely
unrecoverable — never "unknown."

**F009 (Slide 33, acknowledgments) — acks unpopulated.** contributors
= ['TBD - populated by production orchestrator']; tenant_attribution
= 'TBD'. The data and the question originate with the Kathy Ryan lab
(strains 4580/4584/4599 and the transcriptome/proteome are theirs).
Shipping placeholder acks fails to credit the data provider on the
audience-facing slide. *Fix:* populate Ryan-lab data providers +
analysis contributors; set tenant_attribution to 'beril'. Must be
resolved before presentation.

## C. Tier-language register

### P1

**F001 (Slide 7, data_figure) — "confirms constitutive derepression"
overclaims a 0.315 correlation.** The title attaches two overclaims
to one modest correlation:

- Slide 7 title: *"Spearman ρ=0.315 concordance with Leaden Δfur
  signal confirms constitutive derepression (n=93 DEGs)"* — and the
  speaker_notes themselves concede the speaker "must be ready to
  defend ρ=0.315 … a modest correlation."
- REPORT §Finding 1: *"correlates with Leaden 2018's Δfur signal at
  Spearman ρ = 0.315 … confirming Fur derepression as a major
  driver"* — i.e. a *major component*, not the sole driver.

Worse, "confirms **constitutive** derepression" imports throughline
sub-claim A2 ("constitutive Δfur derepression, not an
iron-limitation response … ⚠ partial — single growth condition"),
which is established by the iron-discrimination comparison on the
**next** slide (8), not by this concordance scatter. The figure
shows correlation with Leaden's Δfur signal; it does not by itself
discriminate constitutive derepression from an iron-status readout.
*Fix:* scope the verb to what the scatter shows and move
constitutivity to slide 8: "Spearman ρ=0.315 (p=2.08e-03, 71% sign
concordance) confirms Fur derepression as a major component of our
signal (n=93 Leaden DEGs)."

## D. Q&A anti-strawman check

### P1

**F006 (Q&A set, slides 30–32) — the sharpest objection to "driver"
is missing.** The three anticipated Q&A (single-condition scope; Lpt
transcript-up/protein-down discordance; Path A marginal-enrichment
power) are genuinely strong and land their concessions honestly — no
softball among them. The gap is what is *absent*: no Q&A defends the
deck's central word. The causal framing ("Δfur derepression is the
demonstrable driver") rests, in this project's own new data, on a
correlation (ρ=0.315) plus a marginal enrichment (1.60×); the causal
*necessity* that licenses "driver" is imported wholesale from Zik
2022 (A25, "✓ direct — establishes Fur as the precondition this arc
characterizes"). A hostile reviewer asks: *"Your data show
correlation and marginal enrichment; the necessity that licenses the
word driver is Zik 2022. What does THIS work demonstrate causally
that Zik 2022 did not already establish?"* There is no anticipated
answer. *Fix:* add a fourth Q&A that draws the line explicitly — Zik
2022 established Δfur necessity; this work contributes the
regulon-to-envelope mechanistic map at graded confidence. The new
contribution is the graded mechanism, not the causal necessity.

## E. Substory→slide mapping coherence

### P2

**F007 (deck-level) — 34 slides vs the throughline's own 26-slide
talk-30 budget (~31% over).** That is ~10 slides past the budget the
spine was designed around for a hard-limited peer slot. The four
methods_summary slides (10, 14, 18, 24) plus five section dividers
are the most compressible. *Fix:* fold each methods_summary into the
adjacent result slide's footer/notes or merge thin dividers; protect
the result slides (7, 11, 15, 19, 20, 22, 25, 27).

**F010 (deck-level, confidence medium) — design artifact disagrees
with the shipped deck on Q&A scope.** narrative/02_substories.md
records "qa_anticipated not requested," yet the deck contains three
qa_anticipated slides (positions 30–32) plus a working/03_slides/
qa_anticipated.json. The Q&A content is good, so this is not a
content defect — but the substory design artifact disagreeing with
slide_spec will confuse the review-rewrite loop about whether Q&A is
in scope. *Fix:* reconcile 02_substories.md to mark qa_anticipated as
requested/in-scope.

## F. Citation reality

### P1

**F004 (Slide 34, references) — references slide omits the keystone
citation (Leaden 2018).** Leaden 2018 (PMID 30210482) is pinned
in-text on slides 4, 7, and 8 and is the source of the ρ=0.315
concordance the entire S1 driver claim rests on — yet it is NOT in
refs_short. Also absent though cited in-text: Price2018 (slide 12),
QuinteroYanes2022 (slide 16), Greenwich2023 (slides 16, 26). The
slide sets `full_pool_in_speaker_notes: true`, i.e. the complete list
lives in speaker notes the audience never sees. A peer who wants to
look up the foundational Leaden concordance cannot find it on the
references slide. *Fix:* add the four in-text-cited-but-unlisted keys
to refs_short — at minimum Leaden 2018 (PMID 30210482), Price et al.
2018, Quintero-Yanes 2022, Greenwich 2023. Do not rely on
`full_pool_in_speaker_notes` for citations referenced on content
slides.

**F005 (Slide 16, claim_evidence) — citation pins don't match
content.** The citations array is [QuinteroYanes2022, Greenwich2023],
but **Greenwich2023 supports nothing on slide 16** — its load-bearing
role is the ChvG-ChvI alphaproteobacterial-conservation claim on
slide 26 (per slide 26 speaker notes: "consistent with Greenwich et
al. 2023's review documenting alphaproteobacterial conservation of
this envelope-stress regulatory circuit"). Meanwhile the slide-16
bullet that *does* need a citation — "ChvR sRNA (Fröhlich 2018,
adversarial review N3) is an untested post-transcriptional
alternative" — attributes ChvR to **Fröhlich 2018, which is absent
from the citations array AND from references slide 34.** So slide 16
cites a paper it does not use (Greenwich2023 = citation drift) and
names a paper it does not list (Fröhlich 2018 = dangling
attribution). *Fix:* drop Greenwich2023 from slide 16's citations
(it belongs to slide 26), add Fröhlich 2018 to back the ChvR bullet,
and ensure Fröhlich 2018 lands in refs_short on slide 34.

## G. Missing-slide / coverage gaps

### P1

**F003 (deck-level) — the deck promises to name which Fur targets
matter, then never shows them.** Goal slide 3 asks "Which of the 93
Fur-released DEGs are operationally required—not merely incidentally
derepressed?" and the S2 punchline is "only the Fur-released Path A
enriches for envelope-stress fitness." But the only S2 result slide
(11) is an enrichment-statistics table (Path A 1.60× p=0.016 vs Path
B 1.04× p=0.515) — it never names the operationally-important genes.
The single highest-priority functional target, **ChvT (CCNA_03108)
at |t|=43.7 under envelope stress** (REPORT §Finding 2), appears
ONLY in the Q&A answer_detail (slide 32), which the audience sees
only if someone asks. A peer who buys the Path A enrichment
immediately asks "which genes, and what do they do?" and there is no
slide to point at. *Fix:* add one claim_evidence slide in S2
(between 11 and 12) naming the top Path A genes with functions —
ChvT (CCNA_03108, |t|=43.7) and the leading TonB-dependent
transporters — so the question posed on slide 3 is answered on a
visible slide, not buried in Q&A.

## H. Central objection (peer-reviewer killshot)

**F011 (info) — the load-bearing word is "driver," and the causality
that licenses it is borrowed.** The throughline, title, big_idea,
deck_close, and synthesis scorecard all assert "Δfur derepression is
the demonstrable driver of the lipid A-loss-permissive envelope
state." But this project's OWN new evidence for that claim is
correlational and marginal: a modest cross-study concordance
(Spearman ρ=0.315) and a marginal, adversarially-reproduced fitness
enrichment (1.60×, p=0.016). The causal *necessity* that actually
licenses "driver" — that Δfur is required for lipid A-loss viability
— comes entirely from Zik 2022, prior work this team did not perform.
A hostile reviewer asks: *"Strip out Zik 2022 and what does your
data demonstrate? Correlation and a 1.6-fold enrichment. Where is
the causal driver result that is yours?"* The deck does not preempt
this anywhere — it leans on Zik 2022's necessity throughout while
branding the contribution as a demonstrated driver. **The honest and
stronger framing is already inside the deck's own graded scorecard:**
this work's contribution is the regulon-to-envelope mechanistic MAP
at graded confidence, built on top of Zik 2022's established Δfur
precondition. *Suggested structural fix:* reframe the contribution
claim once early (big_idea/goal) and once in close — "Zik 2022
established Δfur is required; we map what that derepression sets in
motion — at graded, pre-registered confidence" — which converts the
soft spot (borrowed causality) into the deck's actual strength (the
graded mechanism) and inoculates the speaker against the driver
objection. Pair this reframing with the F006 fourth Q&A as the
rehearsed verbal defense.

## Suggested fixes (consolidated)

### slide_compose.v1.md
- **F001 (Slide 7):** rescope the verb and drop "constitutive" — "Spearman ρ=0.315 (p=2.08e-03, 71% sign concordance) confirms Fur derepression as a major component of our signal (n=93 Leaden DEGs)"; reserve the constitutive-vs-iron claim for slide 8.
- **F002 (Slide 1):** replace placeholder title with "Δfur derepression drives the lipid A-loss-permissive envelope state in Caulobacter crescentus"; populate presenter/affiliation; complete or cleanly truncate the subtitle.
- **F003 (deck-level missing_slide):** add a claim_evidence slide in S2 (between 11 and 12) naming top Path A genes with functions — ChvT (CCNA_03108, |t|=43.7) and leading TonB-dependent transporters.
- **F004 (Slide 34):** add in-text-cited-but-unlisted keys to refs_short — Leaden 2018 (PMID 30210482), Price 2018, Quintero-Yanes 2022, Greenwich 2023.
- **F005 (Slide 16):** drop Greenwich2023 from citations (belongs to slide 26); add Fröhlich 2018 to back the ChvR sRNA bullet; ensure Fröhlich 2018 is in refs_short on slide 34.
- **F008 (Slide 10 + slides 14/18/24):** populate real tool versions (edgeR, Fitness Browser, Biopython, PaperBLAST); use access dates if a version is unrecoverable, never "unknown."
- **F009 (Slide 33):** populate contributors with Ryan-lab data providers + analysis contributors; set tenant_attribution to 'beril'.
- **F011 (deck-level central_objection):** reframe the contribution claim early (big_idea/goal) and in close — "Zik 2022 established Δfur is required; we map what that derepression sets in motion, at graded pre-registered confidence."

### qa_anticipated.v1.md
- **F006 (Q&A set):** add a fourth Q&A drawing the Zik-2022-vs-this-work line — Zik established Δfur necessity; this work contributes the graded regulon-to-envelope mechanistic map, not the causal necessity.

### substory_design.v1.md
- **F007 (deck-level):** trim toward the 26-slide budget by folding methods_summary slides into adjacent result-slide footers/notes and merging thin dividers; protect result slides (7, 11, 15, 19, 20, 22, 25, 27).
- **F010 (deck-level):** reconcile 02_substories.md with the shipped deck — mark qa_anticipated as requested/in-scope so the design artifact and slide_spec agree.
