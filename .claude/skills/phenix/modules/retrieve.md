# AlphaFold Structure Retrieval

Retrieve AlphaFold predicted structures from the EBI API and store them in MinIO for downstream use.

## When to Use

- User wants AlphaFold structure files (PDB, mmCIF, PAE) for a protein
- Starting a molecular replacement or cryo-EM docking workflow
- Batch retrieval of structures for pangenome-scale analysis

## Workflow

### Step 1: Look Up the AlphaFold Entry in BERDL

Query `kescience_alphafold.alphafold_entries` to confirm the accession exists and get metadata:

```bash
AUTH_TOKEN=$(grep "KBASE_AUTH_TOKEN" .env | cut -d'"' -f2)

curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT alphafold_id, first_residue, last_residue, model_version FROM kescience_alphafold.alphafold_entries WHERE uniprot_accession = '\''ACCESSION'\'' LIMIT 1",
    "limit": 1
  }' \
  https://hub.berdl.kbase.us/apis/mcp/delta/tables/query
```

Optionally check MSA depth for confidence:

```bash
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT msa_depth FROM kescience_alphafold.alphafold_msa_depths WHERE uniprot_accession = '\''ACCESSION'\'' LIMIT 1",
    "limit": 1
  }' \
  https://hub.berdl.kbase.us/apis/mcp/delta/tables/query
```

### Step 2: Retrieve Structure Files from EBI API

The AlphaFold API provides download URLs for each structure:

```bash
ACCESSION="A0A0H3LN97"

# Get API metadata (includes download URLs)
curl -s "https://alphafold.ebi.ac.uk/api/prediction/${ACCESSION}" | python3 -m json.tool

# Download PDB file
curl -sL "https://alphafold.ebi.ac.uk/files/AF-${ACCESSION}-F1-model_v4.pdb" \
  -o "${ACCESSION}_model.pdb"

# Download mmCIF file
curl -sL "https://alphafold.ebi.ac.uk/files/AF-${ACCESSION}-F1-model_v4.cif" \
  -o "${ACCESSION}_model.cif"

# Download PAE (Predicted Aligned Error) JSON
curl -sL "https://alphafold.ebi.ac.uk/files/AF-${ACCESSION}-F1-predicted_aligned_error_v4.json" \
  -o "${ACCESSION}_pae.json"
```

**Version note**: The URL uses `v4` for most entries. Check the `model_version` from the BERDL query — if it's v6, the database entry is v6 but the file URLs may still use `v4`. The API response contains the correct download URLs.

### Step 3: Validate Retrieved Files

```bash
# Check PDB file is valid (has ATOM records)
grep -c "^ATOM" "${ACCESSION}_model.pdb"

# Check residue count matches expected
grep "^ATOM" "${ACCESSION}_model.pdb" | awk '{print $6}' | sort -un | tail -1

# Quick pLDDT summary from B-factor column (AlphaFold stores pLDDT as B-factor)
grep "^ATOM" "${ACCESSION}_model.pdb" | awk '{print $NF}' | awk '{
  sum+=$1; n++
  if($1>=90) vh++
  else if($1>=70) h++
  else if($1>=50) l++
  else vl++
} END {
  printf "Mean pLDDT: %.1f\n", sum/n
  printf "Very high (>=90): %d (%.1f%%)\n", vh, 100*vh/n
  printf "High (70-89): %d (%.1f%%)\n", h, 100*h/n
  printf "Low (50-69): %d (%.1f%%)\n", l, 100*l/n
  printf "Very low (<50): %d (%.1f%%)\n", vl, 100*vl/n
}'
```

### Step 4: Upload to MinIO

```bash
export https_proxy=http://127.0.0.1:8123
export no_proxy=localhost,127.0.0.1

MINIO_PATH="cdm-lake/tenant-general-warehouse/kescience/structural-biology/alphafold-structures/${ACCESSION}"

mc cp "${ACCESSION}_model.pdb" "berdl-minio/${MINIO_PATH}/model.pdb"
mc cp "${ACCESSION}_model.cif" "berdl-minio/${MINIO_PATH}/model.cif"
mc cp "${ACCESSION}_pae.json" "berdl-minio/${MINIO_PATH}/pae.json"
```

### Step 5: Record in Delta Lake

Prepare a TSV row for `kescience_structural_biology.alphafold_structures`:

| Field | Value |
|-------|-------|
| uniprot_accession | The accession |
| pdb_path | `s3a://cdm-lake/.../model.pdb` |
| cif_path | `s3a://cdm-lake/.../model.cif` |
| pae_path | `s3a://cdm-lake/.../pae.json` |
| n_residues | From PDB ATOM count |
| n_domains | 0 (set after processing) |
| mean_plddt | From B-factor column |
| retrieval_date | Today's date |

## Batch Retrieval

For retrieving multiple structures (e.g., all AlphaFold structures linked to a pangenome cluster):

```bash
#!/bin/bash
# batch_retrieve_af.sh — retrieve AlphaFold structures for a list of accessions
# Usage: bash batch_retrieve_af.sh accessions.txt output_dir/

ACCESSIONS_FILE="$1"
OUTPUT_DIR="$2"
mkdir -p "$OUTPUT_DIR"

while read -r ACC; do
  if [ -f "${OUTPUT_DIR}/${ACC}_model.pdb" ]; then
    echo "SKIP: ${ACC} (already exists)"
    continue
  fi

  echo "Retrieving: ${ACC}"
  curl -sL "https://alphafold.ebi.ac.uk/files/AF-${ACC}-F1-model_v4.pdb" \
    -o "${OUTPUT_DIR}/${ACC}_model.pdb"

  # Check if download succeeded (file should have ATOM records)
  if ! grep -q "^ATOM" "${OUTPUT_DIR}/${ACC}_model.pdb" 2>/dev/null; then
    echo "WARN: ${ACC} — no ATOM records, may not exist in AlphaFold DB"
    rm -f "${OUTPUT_DIR}/${ACC}_model.pdb"
  fi

  sleep 0.5  # Rate limiting
done < "$ACCESSIONS_FILE"
```

## Linking to Pangenome

To find which pangenome proteins have AlphaFold structures:

```sql
SELECT b.gene_cluster_id, b.product, b.uniref100,
       a.alphafold_id, m.msa_depth
FROM kbase_ke_pangenome.bakta_annotations b
JOIN kescience_alphafold.alphafold_entries a
  ON a.uniprot_accession = REPLACE(b.uniref100, 'UniRef100_', '')
LEFT JOIN kescience_alphafold.alphafold_msa_depths m
  ON m.uniprot_accession = a.uniprot_accession
WHERE b.species_id = 'SPECIES_ID'
  AND b.uniref100 IS NOT NULL
  AND m.msa_depth >= 300
ORDER BY m.msa_depth DESC
LIMIT 50;
```

## Output

After retrieval, report to the user:

```
Retrieved AlphaFold structure for {ACCESSION}:
  - Model: {n_residues} residues, mean pLDDT {mean_plddt:.1f}
  - Confidence: {vh}% very high, {h}% high, {l}% low, {vl}% very low
  - MSA depth: {msa_depth} (from BERDL)
  - Stored: s3a://cdm-lake/.../alphafold-structures/{ACCESSION}/

  pLDDT interpretation:
    >= 90: Very high confidence (backbone reliable)
    70-89: High confidence (good for most analyses)
    50-69: Low confidence (caution — loops, disorder)
    < 50:  Very low confidence (likely disordered, do not trust)
```
