"""
cofactor_overlap_audit.py
=========================
Q2 audit: verify completeness of non-metal cofactor KO removal.

Cross-references every KO in the KEGG 'cofactors and vitamins' category
(382 KOs, from NB18 KEGG_CATEGORIES) against:
  1. The full 730-KO curated metal gene list (all tiers)
  2. BacMet2 experimental database (source_bacmet flag in curated list)
  3. Pfam metal-binding clan membership (pfam_qc_results.csv, covers primary 140 KOs)

Outputs data/cofactor_overlap_audit.csv.
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# ── 382 cofactor/vitamin KOs from NB18 ────────────────────────────────────────
COFACTOR_VITAMIN_KOS = [
    'K00002', 'K00012', 'K00059', 'K00072', 'K00077', 'K00082', 'K00097',
    'K00103', 'K00128', 'K00208', 'K00225', 'K00226', 'K00228', 'K00230',
    'K00231', 'K00254', 'K00275', 'K00278', 'K00287', 'K00288', 'K00300',
    'K00355', 'K00382', 'K00435', 'K00452', 'K00453', 'K00457', 'K00463',
    'K00486', 'K00515', 'K00568', 'K00589', 'K00591', 'K00595', 'K00600',
    'K00606', 'K00608', 'K00609', 'K00610', 'K00643', 'K00647', 'K00652',
    'K00699', 'K00762', 'K00763', 'K00767', 'K00768', 'K00788', 'K00789',
    'K00793', 'K00794', 'K00796', 'K00798', 'K00826', 'K00831', 'K00833',
    'K00858', 'K00859', 'K00861', 'K00867', 'K00868', 'K00877', 'K00878',
    'K00939', 'K00940', 'K00941', 'K00944', 'K00946', 'K00949', 'K00950',
    'K00953', 'K00954', 'K00963', 'K00966', 'K00969', 'K01012', 'K01053',
    'K01077', 'K01113', 'K01195', 'K01307', 'K01432', 'K01440', 'K01465',
    'K01491', 'K01495', 'K01497', 'K01498', 'K01500', 'K01556', 'K01579',
    'K01591', 'K01598', 'K01599', 'K01633', 'K01661', 'K01664', 'K01665',
    'K01698', 'K01719', 'K01737', 'K01749', 'K01756', 'K01772', 'K01809',
    'K01845', 'K01885', 'K01906', 'K01911', 'K01916', 'K01918', 'K01919',
    'K01920', 'K01922', 'K01930', 'K01935', 'K01937', 'K01938', 'K01939',
    'K01947', 'K01950', 'K01954', 'K01955', 'K01956', 'K02169', 'K02170',
    'K02188', 'K02189', 'K02190', 'K02191', 'K02201', 'K02224', 'K02225',
    'K02226', 'K02227', 'K02228', 'K02229', 'K02230', 'K02231', 'K02232',
    'K02233', 'K02257', 'K02259', 'K02302', 'K02303', 'K02304', 'K02318',
    'K02372', 'K02492', 'K02495', 'K02496', 'K02548', 'K02549', 'K02551',
    'K02552', 'K02619', 'K02823', 'K02858', 'K03146', 'K03147', 'K03148',
    'K03149', 'K03150', 'K03151', 'K03153', 'K03179', 'K03181', 'K03182',
    'K03183', 'K03184', 'K03185', 'K03186', 'K03342', 'K03394', 'K03399',
    'K03472', 'K03473', 'K03474', 'K03517', 'K03525', 'K03635', 'K03637',
    'K03638', 'K03639', 'K03644', 'K03707', 'K03750', 'K03793', 'K03794',
    'K03795', 'K03800', 'K03801', 'K03809', 'K03831', 'K04032', 'K04487',
    'K04719', 'K05357', 'K05884', 'K05895', 'K05928', 'K05934', 'K05936',
    'K05979', 'K06034', 'K06042', 'K06125', 'K06126', 'K06127', 'K06134',
    'K06210', 'K06215', 'K06897', 'K06914', 'K06982', 'K06989', 'K07072',
    'K07130', 'K07144', 'K07758', 'K08097', 'K08281', 'K08310', 'K08679',
    'K08680', 'K08681', 'K08973', 'K09007', 'K09458', 'K09680', 'K09698',
    'K09722', 'K09733', 'K09789', 'K09833', 'K09834', 'K09882', 'K09883',
    'K09903', 'K10046', 'K10047', 'K10105', 'K10106', 'K10810', 'K10977',
    'K10978', 'K11146', 'K11152', 'K11153', 'K11161', 'K11204', 'K11205',
    'K11212', 'K11540', 'K11541', 'K11752', 'K11753', 'K11754', 'K11780',
    'K11781', 'K11782', 'K11783', 'K11784', 'K11785', 'K12073', 'K12234',
    'K12501', 'K12502', 'K13038', 'K13039', 'K13248', 'K13367', 'K13369',
    'K13402', 'K13403', 'K13421', 'K13540', 'K13541', 'K13542', 'K13543',
    'K13799', 'K13800', 'K13809', 'K13939', 'K13940', 'K13941', 'K13950',
    'K13998', 'K14153', 'K14154', 'K14163', 'K14190', 'K14263', 'K14652',
    'K14654', 'K14655', 'K14759', 'K14760', 'K14941', 'K15376', 'K15734',
    'K15740', 'K16593', 'K16792', 'K16793', 'K16869', 'K17364', 'K17497',
    'K17744', 'K17745', 'K17828', 'K17872', 'K18240', 'K18278', 'K18284',
    'K18285', 'K18286', 'K18482', 'K18532', 'K18533', 'K18534', 'K18586',
    'K18800', 'K18853', 'K18933', 'K19221', 'K19222', 'K19267', 'K19560',
    'K19561', 'K19562', 'K19563', 'K19642', 'K19793', 'K19965', 'K20457',
    'K20810', 'K20860', 'K20861', 'K20862', 'K20884', 'K20967', 'K21063',
    'K21064', 'K21142', 'K21219', 'K21220', 'K21456', 'K21479', 'K21610',
    'K21611', 'K21612', 'K21977', 'K22011', 'K22012', 'K22099', 'K22100',
    'K22101', 'K22225', 'K22226', 'K22227', 'K22316', 'K22391', 'K22699',
    'K22911', 'K22912', 'K22949', 'K23094', 'K23095', 'K23734', 'K23735',
    'K23750', 'K23763', 'K24843', 'K24844', 'K24845', 'K24866', 'K25033',
    'K25570', 'K28034', 'K28925', 'K28926',
]

print(f"Cofactor/vitamin KOs (NB18 list): {len(COFACTOR_VITAMIN_KOS)}")

# ── Load reference datasets ────────────────────────────────────────────────────
curated = pd.read_csv(DATA / "curated_mrg_ko_ids_v2.csv", low_memory=False)
curated["KO"] = curated["KO"].astype(str)
bacmet_only = pd.read_csv(DATA / "bacmet_only_kos.csv", low_memory=False)
bacmet_only["KO"] = bacmet_only["KO"].astype(str)

pfam_qc = pd.read_csv(DATA / "pfam_qc_results.csv", low_memory=False)
pfam_qc["KO"] = pfam_qc["KO"].astype(str)

# Sets for fast lookup
kos_730 = set(curated["KO"].tolist())
kos_primary_140 = set(curated[curated["evidence_tier"].isin(["Tier 1", "Tier 2"])]["KO"].tolist())
kos_bacmet = set(
    curated[curated["source_bacmet"].notna() & (curated["source_bacmet"] != "")]["KO"].tolist()
) | set(bacmet_only["KO"].tolist())

# KOs with confirmed Pfam metal clan (only for KOs in pfam_qc_results)
pfam_metal_clan_kos = set(
    pfam_qc[pfam_qc["has_metal_clan"] == True]["KO"].tolist()
)
pfam_covered_kos = set(pfam_qc["KO"].tolist())

# KO → gene_name / definition from curated list (where available)
curated_info = curated.set_index("KO")[["gene_name", "definition"]].to_dict("index")

print(f"Full 730-KO list: {len(kos_730)}")
print(f"Primary 140-KO list: {len(kos_primary_140)}")
print(f"BacMet-flagged KOs: {len(kos_bacmet)}")
print(f"Pfam metal-clan KOs (primary 140 coverage): {len(pfam_metal_clan_kos)}")

# ── Build audit table ──────────────────────────────────────────────────────────
rows = []
for ko in COFACTOR_VITAMIN_KOS:
    in_140 = ko in kos_primary_140
    in_730 = ko in kos_730
    in_bacmet = ko in kos_bacmet
    in_pfam_covered = ko in pfam_covered_kos
    has_pfam_metal = (ko in pfam_metal_clan_kos) if in_pfam_covered else None

    info = curated_info.get(ko, {})
    gene_name = info.get("gene_name", "")
    definition = info.get("definition", "")

    flag = in_140 or in_730 or in_bacmet or (has_pfam_metal is True)

    rows.append({
        "KO": ko,
        "gene_name": gene_name,
        "definition": definition,
        "in_primary_140": in_140,
        "in_full_730": in_730,
        "in_bacmet": in_bacmet,
        "pfam_coverage": in_pfam_covered,
        "has_pfam_metal_clan": has_pfam_metal,
        "flag_metal_associated": flag,
        "removed_from_original_nonmetal_set": in_140,
        "additionally_flagged": (in_730 or in_bacmet or (has_pfam_metal is True)) and not in_140,
    })

audit = pd.DataFrame(rows)

out = DATA / "cofactor_overlap_audit.csv"
audit.to_csv(out, index=False)
print(f"\nSaved: {out}")

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n=== SUMMARY ===")
print(f"Total KOs in cofactor/vitamin category: {len(audit)}")
print(f"  In primary 140 (already removed): {audit['in_primary_140'].sum()}")
print(f"  In full 730-KO list (Tiers 1-5): {audit['in_full_730'].sum()}")
print(f"  Flagged in BacMet2: {audit['in_bacmet'].sum()}")
print(f"  Covered by Pfam QC analysis: {audit['pfam_coverage'].sum()}")
print(f"  Has Pfam metal clan (among covered): {audit['has_pfam_metal_clan'].sum()}")
print(f"  Total metal-associated flags: {audit['flag_metal_associated'].sum()}")
print(f"  Newly flagged (beyond primary 140): {audit['additionally_flagged'].sum()}")

newly = audit[audit["additionally_flagged"]]
if len(newly):
    print("\nNewly flagged KOs (beyond primary 140):")
    for _, r in newly.iterrows():
        flags = []
        if r["in_full_730"]: flags.append("730-KO list")
        if r["in_bacmet"]: flags.append("BacMet2")
        if r["has_pfam_metal_clan"]: flags.append("Pfam metal clan")
        print(f"  {r['KO']:8s}  {str(r['gene_name']):15s}  [{', '.join(flags)}]")
