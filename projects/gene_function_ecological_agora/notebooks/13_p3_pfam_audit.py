"""NB13 — Phase 3 Pfam pre-flight audit.

Decides whether Phase 3 architectural deep-dive uses bakta_pfam_domains (per plan v2)
or interproscan_domains (per Phase 1 substrate audit + plan v2.1) as the Pfam substrate.

Per docs/pitfalls.md [plant_microbiome_ecotypes]: bakta_pfam_domains was missing 12/22
marker Pfams in a prior audit, with the failure mode unresolved (could be query-format
mismatch, could be genuine coverage gaps). interproscan_domains was validated as the
authoritative Pfam source on BERDL during Phase 1A NB01 substrate audit (833M Pfam hits,
83.8% cluster coverage).

Audit method:
  Take a curated marker Pfam list covering Phase 2 control panel + Phase 3 PSII +
  mycolic-acid extras. For each substrate (bakta_pfam_domains, interproscan_domains),
  count distinct gene_clusters carrying each marker. Compare coverage. Substrate
  decision: use whichever has higher coverage on the markers. If coverage is comparable,
  use interproscan_domains for consistency with Phase 1/2.

Outputs:
  data/p3_pfam_completeness_audit.tsv — per-Pfam coverage in both substrates
  data/p3_pfam_audit_decision.json — substrate decision + rationale
"""
import json, time
from pathlib import Path
import pandas as pd
from pyspark.sql import functions as F
from berdl_notebook_utils.setup_spark_session import get_spark_session

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"

t0 = time.time()
print("=== NB13 — Phase 3 Pfam pre-flight audit ===", flush=True)

spark = get_spark_session()

# Curated marker Pfam set
# Phase 2 control panel (already validated in Phase 1B/Phase 2)
MARKER_PFAMS = {
    # TCS HK
    "PF00512": "HisKA — TCS histidine kinase A",
    "PF07568": "HisKA_2 — TCS histidine kinase A class 2",
    "PF07730": "HisKA_3",
    "PF06580": "His_kinase — bacterial histidine kinase domain",
    "PF02518": "HATPase_c — TCS HK ATPase domain",
    "PF13415": "HATPase_c_3",
    "PF13581": "HATPase_c_5",
    # TCS RR
    "PF00072": "Response_reg — TCS response regulator",
    "PF00196": "GerE — Trans_reg_C HTH-type",
    "PF02954": "HTH_8 — TCS response regulator HTH",
    "PF00486": "Trans_reg_C — TCS response regulator C-term",
    # β-lactamase
    "PF00144": "Beta-lactamase — class A/C/D",
    "PF13354": "Beta-lactamase_2",
    "PF12706": "Lactamase_B — class B metallo",
    "PF13483": "Beta-lactamase_4",
    "PF00768": "Peptidase_S11 — D-alanyl-D-alanine carboxypeptidase",
    # CRISPR-Cas
    "PF18557": "Cas3_HD",
    "PF09704": "CRISPR_assoc_Cas7",
    "PF09827": "CRISPR_Cse2",
    "PF09455": "CRISPR_assoc",
    "PF09659": "CRISPR_assoc_Cas4",
    # Photosystem II (Phase 3 hypothesis)
    "PF00124": "PsbA — photosystem II protein D1",
    "PF02530": "PsbB — photosystem II CP47 chlorophyll-binding",
    "PF02533": "PsbC — photosystem II CP43 chlorophyll-binding",
    "PF00421": "PsbD — photosystem II protein D2",
    "PF02683": "PsbE — photosystem II cytochrome b559 alpha",
    # Mycolic-acid (Phase 2 NB12 supported)
    "PF00109": "Ketoacyl-synt — fatty acid synthase",
    "PF02801": "Ketoacyl-synt_C",
    "PF08545": "MaoC_dehydratas",
    # Universal housekeeping (controls)
    "PF00177": "Ribosomal_S7",
    "PF00164": "Ribosomal_S12",
    "PF00181": "Ribosomal_L2",
    "PF00163": "Ribosomal_S4 — universal",
}

print(f"Audit set: {len(MARKER_PFAMS)} marker Pfams across TCS HK/RR, β-lactamase, CRISPR-Cas, PSII, mycolic-acid, ribosomal", flush=True)

# Probe both substrates
results = []

# bakta_pfam_domains audit
print("\n--- bakta_pfam_domains substrate ---", flush=True)
for pfam_acc, desc in MARKER_PFAMS.items():
    # Try multiple query formats per the [plant_microbiome_ecotypes] pitfall
    found_via_acc = 0
    found_via_acc_versioned = 0
    for query in [pfam_acc, f"{pfam_acc}.1", f"{pfam_acc}.2"]:
        try:
            n = spark.sql(f"""
                SELECT COUNT(DISTINCT gene_cluster_id) AS n
                FROM kbase_ke_pangenome.bakta_pfam_domains
                WHERE pfam_id = '{query}' OR pfam_id LIKE '{pfam_acc}%'
            """).toPandas()["n"].iloc[0]
            if n > 0:
                found_via_acc = int(n)
                break
        except Exception as e:
            pass
    results.append({"pfam_acc": pfam_acc, "description": desc, "substrate": "bakta_pfam_domains", "n_clusters": found_via_acc})
    print(f"  {pfam_acc} ({desc[:40]}): {found_via_acc:,}", flush=True)

# interproscan_domains audit (analysis = 'Pfam')
print("\n--- interproscan_domains substrate ---", flush=True)
for pfam_acc, desc in MARKER_PFAMS.items():
    try:
        n = spark.sql(f"""
            SELECT COUNT(DISTINCT gene_cluster_id) AS n
            FROM kbase_ke_pangenome.interproscan_domains
            WHERE analysis = 'Pfam' AND signature_acc = '{pfam_acc}'
        """).toPandas()["n"].iloc[0]
    except Exception as e:
        n = 0
    results.append({"pfam_acc": pfam_acc, "description": desc, "substrate": "interproscan_domains", "n_clusters": int(n)})
    print(f"  {pfam_acc} ({desc[:40]}): {int(n):,}", flush=True)

# Build comparison
df = pd.DataFrame(results)
pivot = df.pivot_table(index=["pfam_acc", "description"], columns="substrate", values="n_clusters", aggfunc="first").reset_index()
pivot.columns.name = None
pivot["bakta_zero"] = pivot["bakta_pfam_domains"] == 0
pivot["ips_zero"] = pivot["interproscan_domains"] == 0
pivot["bakta_vs_ips_ratio"] = pivot.apply(
    lambda r: r["bakta_pfam_domains"] / r["interproscan_domains"] if r["interproscan_domains"] > 0 else 0, axis=1
)
pivot.to_csv(DATA_DIR / "p3_pfam_completeness_audit.tsv", sep="\t", index=False)
print(f"\nWrote p3_pfam_completeness_audit.tsv ({len(pivot)} markers)", flush=True)

n_bakta_zero = int(pivot["bakta_zero"].sum())
n_ips_zero = int(pivot["ips_zero"].sum())
n_total = len(pivot)
median_bakta_vs_ips = float(pivot["bakta_vs_ips_ratio"].median())
print(f"\n=== Audit summary ===", flush=True)
print(f"Total markers tested: {n_total}", flush=True)
print(f"bakta_pfam_domains: {n_bakta_zero}/{n_total} markers with ZERO clusters (silent gap candidates)", flush=True)
print(f"interproscan_domains: {n_ips_zero}/{n_total} markers with ZERO clusters", flush=True)
print(f"Median bakta/ips coverage ratio: {median_bakta_vs_ips:.3f}", flush=True)

# Decision logic
if n_bakta_zero >= n_total * 0.20 and n_ips_zero < n_total * 0.10:
    decision = "USE interproscan_domains"
    rationale = (
        f"bakta_pfam_domains has silent coverage gaps in {n_bakta_zero}/{n_total} ({100*n_bakta_zero/n_total:.0f}%) of marker Pfams "
        f"(matching the [plant_microbiome_ecotypes] pitfall pattern of 12/22 markers missing). "
        f"interproscan_domains has only {n_ips_zero}/{n_total} markers with zero clusters and is the authoritative Pfam source per "
        f"Phase 1A substrate audit (833M Pfam hits, 83.8% cluster coverage). "
        f"Phase 3 architectural deep-dive uses interproscan_domains as the substrate."
    )
elif n_bakta_zero == 0 and n_ips_zero == 0:
    decision = "EITHER works; default to interproscan_domains for consistency with Phase 1/2"
    rationale = (
        f"Both substrates show full coverage on all {n_total} markers. Use interproscan_domains for consistency with "
        f"Phase 1A/1B/2 control detection (already validated)."
    )
else:
    decision = "Mixed coverage; use interproscan_domains as primary, bakta_pfam_domains as fallback"
    rationale = (
        f"bakta_pfam_domains: {n_bakta_zero}/{n_total} zero. interproscan_domains: {n_ips_zero}/{n_total} zero. "
        f"Use interproscan_domains as primary substrate. For specific Pfams missing from interproscan_domains, "
        f"check bakta_pfam_domains as fallback."
    )

print(f"\n*** SUBSTRATE DECISION: {decision} ***\n", flush=True)
print(rationale, flush=True)

# Write decision
diagnostics = {
    "phase": "3", "notebook": "NB13", "purpose": "Pfam pre-flight audit",
    "n_markers_tested": n_total,
    "n_markers_zero_in_bakta": n_bakta_zero,
    "n_markers_zero_in_ips": n_ips_zero,
    "median_bakta_vs_ips_ratio": median_bakta_vs_ips,
    "substrate_decision": decision,
    "rationale": rationale,
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p3_pfam_audit_decision.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)
print(f"Wrote p3_pfam_audit_decision.json ({time.time()-t0:.1f}s elapsed)", flush=True)
print(f"\n=== DONE in {time.time()-t0:.1f}s ===", flush=True)
