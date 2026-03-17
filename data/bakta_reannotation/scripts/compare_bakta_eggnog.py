#!/usr/bin/env python3
"""
Compare bakta vs eggnog annotation coverage and test the UniRef50 bridge
to UniProt's curated cross-references.

All joins stay in Spark — no .collect() on large results.
Only aggregated counts are collected to driver.

Usage:
    python compare_bakta_eggnog.py
"""

from berdl_notebook_utils.setup_spark_session import get_spark_session

DB = "kbase_ke_pangenome"
UNIPROT = "kbase_uniprot"


def main():
    spark = get_spark_session()

    # ----------------------------------------------------------------
    # 1. Basic coverage comparison
    # ----------------------------------------------------------------
    print("=" * 70)
    print("BAKTA vs EGGNOG ANNOTATION COVERAGE")
    print("=" * 70)

    # Total cluster count
    total = spark.sql(f"SELECT COUNT(*) as c FROM {DB}.bakta_annotations").collect()[0].c
    eggnog_total = spark.sql(f"SELECT COUNT(*) as c FROM {DB}.eggnog_mapper_annotations").collect()[0].c
    print(f"\nTotal bakta rows:   {total:>15,}")
    print(f"Total eggnog rows:  {eggnog_total:>15,}")
    print(f"EggNOG missing:     {total - eggnog_total:>15,} clusters ({100*(total-eggnog_total)/total:.1f}%)")

    # Per-field coverage: bakta vs eggnog
    print(f"\n{'Annotation':<25} {'Bakta':>15} {'%':>7} {'EggNOG':>15} {'%':>7} {'Winner':>8}")
    print("-" * 80)

    coverage_query = f"""
    SELECT
        SUM(CASE WHEN b.gene IS NOT NULL AND b.gene != '' THEN 1 ELSE 0 END) as bakta_gene,
        SUM(CASE WHEN e.Preferred_name IS NOT NULL AND e.Preferred_name != '' THEN 1 ELSE 0 END) as eggnog_gene,
        SUM(CASE WHEN b.hypothetical = false THEN 1 ELSE 0 END) as bakta_product,
        SUM(CASE WHEN e.Description IS NOT NULL AND e.Description != '' THEN 1 ELSE 0 END) as eggnog_product,
        SUM(CASE WHEN b.ec IS NOT NULL AND b.ec != '' THEN 1 ELSE 0 END) as bakta_ec,
        SUM(CASE WHEN e.EC IS NOT NULL AND e.EC != '' AND e.EC != '-' THEN 1 ELSE 0 END) as eggnog_ec,
        SUM(CASE WHEN b.cog_id IS NOT NULL AND b.cog_id != '' THEN 1 ELSE 0 END) as bakta_cog,
        SUM(CASE WHEN e.COG_category IS NOT NULL AND e.COG_category != '' AND e.COG_category != '-' AND e.COG_category != 'S' THEN 1 ELSE 0 END) as eggnog_cog,
        SUM(CASE WHEN b.kegg_orthology_id IS NOT NULL AND b.kegg_orthology_id != '' THEN 1 ELSE 0 END) as bakta_kegg,
        SUM(CASE WHEN e.KEGG_ko IS NOT NULL AND e.KEGG_ko != '' AND e.KEGG_ko != '-' THEN 1 ELSE 0 END) as eggnog_kegg,
        SUM(CASE WHEN b.uniref50 IS NOT NULL AND b.uniref50 != '' THEN 1 ELSE 0 END) as bakta_uniref50,
        SUM(CASE WHEN b.go IS NOT NULL AND b.go != '' THEN 1 ELSE 0 END) as bakta_go,
        SUM(CASE WHEN e.GOs IS NOT NULL AND e.GOs != '' AND e.GOs != '-' THEN 1 ELSE 0 END) as eggnog_go
    FROM {DB}.bakta_annotations b
    LEFT JOIN {DB}.eggnog_mapper_annotations e
        ON b.gene_cluster_id = e.query_name
    """
    r = spark.sql(coverage_query).collect()[0]

    fields = [
        ("Gene name", r.bakta_gene, r.eggnog_gene),
        ("Product/Description", r.bakta_product, r.eggnog_product),
        ("EC number", r.bakta_ec, r.eggnog_ec),
        ("COG (informative)", r.bakta_cog, r.eggnog_cog),
        ("KEGG KO", r.bakta_kegg, r.eggnog_kegg),
        ("GO terms", r.bakta_go, r.eggnog_go),
        ("UniRef50", r.bakta_uniref50, 0),
    ]
    for name, b_val, e_val in fields:
        b_pct = 100 * b_val / total
        e_pct = 100 * e_val / total if e_val else 0
        winner = "bakta" if b_val > e_val else "eggnog" if e_val > b_val else "tie"
        print(f"{name:<25} {b_val:>15,} {b_pct:>6.1f}% {e_val:>15,} {e_pct:>6.1f}% {winner:>8}")

    # ----------------------------------------------------------------
    # 2. Pfam coverage
    # ----------------------------------------------------------------
    print(f"\n--- Pfam coverage ---")
    pfam_bakta = spark.sql(f"""
        SELECT COUNT(DISTINCT gene_cluster_id) as c FROM {DB}.bakta_pfam_domains
    """).collect()[0].c
    pfam_eggnog = spark.sql(f"""
        SELECT SUM(CASE WHEN PFAMs IS NOT NULL AND PFAMs != '' AND PFAMs != '-' THEN 1 ELSE 0 END) as c
        FROM {DB}.eggnog_mapper_annotations
    """).collect()[0].c
    print(f"  Bakta Pfam (HMMER, hypotheticals only): {pfam_bakta:>12,}  ({100*pfam_bakta/total:.1f}%)")
    print(f"  EggNOG PFAMs (orthology transfer):      {pfam_eggnog:>12,}  ({100*pfam_eggnog/total:.1f}%)")

    # Bakta pfam is only on hypotheticals — verify
    pfam_by_hyp = spark.sql(f"""
        SELECT
            b.hypothetical,
            COUNT(DISTINCT p.gene_cluster_id) as has_pfam
        FROM {DB}.bakta_annotations b
        LEFT JOIN (SELECT DISTINCT gene_cluster_id FROM {DB}.bakta_pfam_domains) p
            ON b.gene_cluster_id = p.gene_cluster_id
        WHERE p.gene_cluster_id IS NOT NULL
        GROUP BY b.hypothetical
    """).collect()
    for row in pfam_by_hyp:
        print(f"    hypothetical={str(row.hypothetical):5s}: {row.has_pfam:>12,} clusters with Pfam hits")

    # ----------------------------------------------------------------
    # 3. Rescue analysis: what bakta adds where eggnog fails
    # ----------------------------------------------------------------
    print(f"\n--- Rescue analysis ---")

    # Clusters missing from eggnog entirely
    rescue = spark.sql(f"""
        SELECT
            COUNT(*) as no_eggnog,
            SUM(CASE WHEN b.hypothetical = false THEN 1 ELSE 0 END) as bakta_product,
            SUM(CASE WHEN b.gene IS NOT NULL AND b.gene != '' THEN 1 ELSE 0 END) as bakta_gene,
            SUM(CASE WHEN b.ec IS NOT NULL AND b.ec != '' THEN 1 ELSE 0 END) as bakta_ec,
            SUM(CASE WHEN b.uniref50 IS NOT NULL AND b.uniref50 != '' THEN 1 ELSE 0 END) as bakta_uniref50
        FROM {DB}.bakta_annotations b
        LEFT JOIN {DB}.eggnog_mapper_annotations e ON b.gene_cluster_id = e.query_name
        WHERE e.query_name IS NULL
    """).collect()[0]
    print(f"  Clusters with NO eggnog:      {rescue.no_eggnog:>12,}")
    print(f"    Bakta provides product:     {rescue.bakta_product:>12,}  ({100*rescue.bakta_product/rescue.no_eggnog:.1f}%)")
    print(f"    Bakta provides gene name:   {rescue.bakta_gene:>12,}  ({100*rescue.bakta_gene/rescue.no_eggnog:.1f}%)")
    print(f"    Bakta provides EC:          {rescue.bakta_ec:>12,}  ({100*rescue.bakta_ec/rescue.no_eggnog:.1f}%)")
    print(f"    Bakta provides UniRef50:    {rescue.bakta_uniref50:>12,}  ({100*rescue.bakta_uniref50/rescue.no_eggnog:.1f}%)")

    # EggNOG hypotheticals rescued by bakta
    hyp_rescue = spark.sql(f"""
        SELECT
            COUNT(*) as eggnog_no_desc,
            SUM(CASE WHEN b.hypothetical = false THEN 1 ELSE 0 END) as bakta_rescued
        FROM {DB}.eggnog_mapper_annotations e
        JOIN {DB}.bakta_annotations b ON e.query_name = b.gene_cluster_id
        WHERE e.Description IS NULL OR e.Description = '' OR e.Description = '-'
    """).collect()[0]
    print(f"\n  EggNOG with no description:   {hyp_rescue.eggnog_no_desc:>12,}")
    print(f"    Bakta provides annotation:  {hyp_rescue.bakta_rescued:>12,}  ({100*hyp_rescue.bakta_rescued/hyp_rescue.eggnog_no_desc:.1f}%)")

    # ----------------------------------------------------------------
    # 4. UniRef50 bridge to UniProt cross-references
    # ----------------------------------------------------------------
    print(f"\n{'=' * 70}")
    print("UNIREF50 BRIDGE: bakta → uniprot_identifier → external DBs")
    print("=" * 70)

    # Get distinct bakta UniRef50 count
    n_bakta_uniref = spark.sql(f"""
        SELECT COUNT(DISTINCT uniref50) as c
        FROM {DB}.bakta_annotations
        WHERE uniref50 IS NOT NULL AND uniref50 != ''
    """).collect()[0].c
    print(f"\nDistinct bakta UniRef50 IDs:  {n_bakta_uniref:>12,}")

    # Check overlap with uniprot_identifier (use count of matching IDs, not full join)
    # Register bakta UniRef50 IDs as a temp table for the bridge queries
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW bakta_uniref_ids AS
        SELECT DISTINCT uniref50 as uniref50_id
        FROM {DB}.bakta_annotations
        WHERE uniref50 IS NOT NULL AND uniref50 != ''
    """)

    # Match bakta UniRef50 → uniprot entries
    matched = spark.sql(f"""
        SELECT COUNT(DISTINCT b.uniref50_id) as c
        FROM bakta_uniref_ids b
        JOIN (
            SELECT DISTINCT xref
            FROM {UNIPROT}.uniprot_identifier
            WHERE db = 'UniRef50'
        ) u ON b.uniref50_id = u.xref
    """).collect()[0].c
    print(f"Found in uniprot_identifier: {matched:>12,}  ({100*matched/n_bakta_uniref:.1f}% of bakta UniRef50 IDs)")

    # For each target database, count reachable UniRef50 IDs via the bridge.
    # Disable auto-broadcast to force sort-merge joins on these large tables.
    # The broadcast exchange exceeds maxResultSize (1GB) on uniprot_identifier.
    print(f"\n  Bridge coverage by target database:")

    spark.sql("SET spark.sql.autoBroadcastJoinThreshold = -1")

    bridge_counts = spark.sql(f"""
        SELECT u2.db, COUNT(DISTINCT b.uniref50_id) as cnt
        FROM bakta_uniref_ids b
        JOIN {UNIPROT}.uniprot_identifier u1
            ON b.uniref50_id = u1.xref AND u1.db = 'UniRef50'
        JOIN {UNIPROT}.uniprot_identifier u2
            ON u1.uniprot_id = u2.uniprot_id
        WHERE u2.db IN ('KEGG', 'Gene_Name', 'OrthoDB', 'STRING', 'Reactome', 'BioCyc', 'RefSeq')
        GROUP BY u2.db
        ORDER BY cnt DESC
    """).collect()

    # Restore default broadcast threshold
    spark.sql("SET spark.sql.autoBroadcastJoinThreshold = 10485760")

    print(f"\n  {'Database':<20} {'UniRef50 IDs':>15} {'% of matched':>15} {'~Est clusters':>15}")
    print(f"  {'-'*68}")
    for row in bridge_counts:
        pct = 100 * row.cnt / matched if matched > 0 else 0
        est_clusters = int(row.cnt / n_bakta_uniref * 104978855) if n_bakta_uniref > 0 else 0
        print(f"  {row.db:<20} {row.cnt:>15,} {pct:>14.1f}% {est_clusters:>15,}")

    # ----------------------------------------------------------------
    # 5. Combined coverage estimate: eggnog + bakta + bridge
    # ----------------------------------------------------------------
    print(f"\n{'=' * 70}")
    print("COMBINED COVERAGE ESTIMATE")
    print("=" * 70)

    # KEGG: eggnog direct + bakta direct + bridge (unique)
    # Use Spark to count clusters with KEGG from ANY source
    kegg_combined = spark.sql(f"""
        SELECT COUNT(DISTINCT gene_cluster_id) as c
        FROM (
            -- Bakta direct KEGG
            SELECT gene_cluster_id FROM {DB}.bakta_annotations
            WHERE kegg_orthology_id IS NOT NULL AND kegg_orthology_id != ''
            UNION
            -- EggNOG KEGG
            SELECT query_name as gene_cluster_id FROM {DB}.eggnog_mapper_annotations
            WHERE KEGG_ko IS NOT NULL AND KEGG_ko != '' AND KEGG_ko != '-'
        )
    """).collect()[0].c
    print(f"\n  KEGG coverage:")
    print(f"    EggNOG alone:          {51028024:>12,}  (38.5%)")
    print(f"    Bakta alone:           {22936033:>12,}  (17.3%)")
    print(f"    Union (either):        {kegg_combined:>12,}  ({100*kegg_combined/total:.1f}%)")

    # EC: combined
    ec_combined = spark.sql(f"""
        SELECT COUNT(DISTINCT gene_cluster_id) as c
        FROM (
            SELECT gene_cluster_id FROM {DB}.bakta_annotations
            WHERE ec IS NOT NULL AND ec != ''
            UNION
            SELECT query_name FROM {DB}.eggnog_mapper_annotations
            WHERE EC IS NOT NULL AND EC != '' AND EC != '-'
        )
    """).collect()[0].c
    print(f"\n  EC coverage:")
    print(f"    EggNOG alone:          {25925434:>12,}  (19.6%)")
    print(f"    Bakta alone:           {19040536:>12,}  (14.4%)")
    print(f"    Union (either):        {ec_combined:>12,}  ({100*ec_combined/total:.1f}%)")

    # GO: combined
    go_combined = spark.sql(f"""
        SELECT COUNT(DISTINCT gene_cluster_id) as c
        FROM (
            SELECT gene_cluster_id FROM {DB}.bakta_annotations
            WHERE go IS NOT NULL AND go != ''
            UNION
            SELECT query_name FROM {DB}.eggnog_mapper_annotations
            WHERE GOs IS NOT NULL AND GOs != '' AND GOs != '-'
        )
    """).collect()[0].c
    print(f"\n  GO coverage:")
    print(f"    EggNOG alone:          {r.eggnog_go:>12,}  ({100*r.eggnog_go/total:.1f}%)")
    print(f"    Bakta alone:           {r.bakta_go:>12,}  ({100*r.bakta_go/total:.1f}%)")
    print(f"    Union (either):        {go_combined:>12,}  ({100*go_combined/total:.1f}%)")

    # Any functional annotation at all
    any_annot = spark.sql(f"""
        SELECT COUNT(DISTINCT gene_cluster_id) as c
        FROM (
            SELECT gene_cluster_id FROM {DB}.bakta_annotations WHERE hypothetical = false
            UNION
            SELECT query_name FROM {DB}.eggnog_mapper_annotations
            WHERE Description IS NOT NULL AND Description != '' AND Description != '-'
        )
    """).collect()[0].c
    print(f"\n  Any functional annotation:")
    print(f"    EggNOG alone:          {r.eggnog_product:>12,}  ({100*r.eggnog_product/total:.1f}%)")
    print(f"    Bakta alone:           {r.bakta_product:>12,}  ({100*r.bakta_product/total:.1f}%)")
    print(f"    Union (either):        {any_annot:>12,}  ({100*any_annot/total:.1f}%)")

    print(f"\n{'=' * 70}")
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
