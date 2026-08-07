"""
feature_extraction.py
--------------------
Protein sequence feature extraction for the Per-Stressor Essentiality Predictor.
All functions operate on lists of sequences and return pandas DataFrames.
"""

import logging
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel

log = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Amino acid alphabet
AA_LIST = "ACDEFGHIKLMNPQRSTVWY"

# ----------------------------------------------------------------------
# Physicochemical properties (AAindex)
HYDROPHOBICITY = {
    'A':1.8,'R':-4.5,'N':-3.5,'D':-3.5,'C':2.5,'Q':-3.5,'E':-3.5,
    'G':-0.4,'H':-3.2,'I':4.5,'L':3.8,'K':-3.9,'M':1.9,'F':2.8,
    'P':-1.6,'S':-0.8,'T':-0.7,'W':-0.9,'Y':-1.3,'V':4.2
}
BULKINESS = {
    'A':11.5,'R':14.8,'N':12.8,'D':12.0,'C':11.2,'Q':13.5,'E':13.0,
    'G':6.1,'H':13.6,'I':17.4,'L':16.8,'K':15.0,'M':15.8,'F':17.7,
    'P':16.0,'S':9.5,'T':12.1,'W':19.3,'Y':18.8,'V':14.5
}
POLARITY = {
    'A':8.1,'R':10.5,'N':11.6,'D':13.0,'C':5.5,'Q':10.5,'E':12.3,
    'G':9.0,'H':10.4,'I':5.2,'L':4.9,'K':11.3,'M':5.7,'F':5.2,
    'P':8.0,'S':9.2,'T':8.6,'W':5.4,'Y':6.2,'V':5.9
}
CHARGE = {
    'A':0,'R':1,'N':0,'D':-1,'C':0,'Q':0,'E':-1,'G':0,'H':0.5,
    'I':0,'L':0,'K':1,'M':0,'F':0,'P':0,'S':0,'T':0,'W':0,'Y':0,'V':0
}
ISOELECTRIC_POINT = {
    'A':6.0,'R':10.8,'N':5.4,'D':2.8,'C':5.0,'Q':5.7,'E':3.2,
    'G':6.0,'H':7.6,'I':6.0,'L':6.0,'K':9.7,'M':5.7,'F':5.5,
    'P':6.3,'S':5.7,'T':5.6,'W':5.9,'Y':5.7,'V':6.0
}
SECONDARY_STRUCTURE = {
    'A':1.42,'R':0.98,'N':0.67,'D':1.01,'C':0.70,'Q':1.11,'E':1.51,
    'G':0.57,'H':1.00,'I':1.08,'L':1.21,'K':1.16,'M':1.45,'F':1.13,
    'P':0.57,'S':0.77,'T':0.83,'W':1.08,'Y':0.69,'V':1.06
}
SOLVENT_ACCESSIBILITY = {
    'A':0.74,'R':0.94,'N':0.76,'D':0.62,'C':0.62,'Q':0.88,'E':0.72,
    'G':0.88,'H':0.78,'I':0.88,'L':0.88,'K':0.88,'M':0.85,'F':0.88,
    'P':0.82,'S':0.72,'T':0.74,'W':0.88,'Y':0.88,'V':0.88
}

PHYS_PROPERTIES = [
    HYDROPHOBICITY, BULKINESS, POLARITY, CHARGE,
    ISOELECTRIC_POINT, SECONDARY_STRUCTURE, SOLVENT_ACCESSIBILITY
]
PHYS_NAMES = [
    'hydrophobicity', 'bulkiness', 'polarity', 'charge',
    'isoelectric_point', 'secondary_structure', 'solvent_accessibility'
]

# ----------------------------------------------------------------------
# BLOSUM62 – try to use Biopython, otherwise a rough fallback
try:
    from Bio.SubsMat.MatrixInfo import blosum62 as _blosum62
    _BLOSUM_MATRIX = np.zeros((20, 20))
    for i, aa1 in enumerate(AA_LIST):
        for j, aa2 in enumerate(AA_LIST):
            _BLOSUM_MATRIX[i, j] = _blosum62.get((aa1, aa2), _blosum62.get((aa2, aa1), -4))
except ImportError:
    # Coarse fallback
    _BLOSUM_MATRIX = np.zeros((20, 20))
    np.fill_diagonal(_BLOSUM_MATRIX, 4)
    hydrophobic_set = set("AILMVFYW")
    for i, aa1 in enumerate(AA_LIST):
        for j, aa2 in enumerate(AA_LIST):
            if i != j:
                if aa1 in hydrophobic_set and aa2 in hydrophobic_set:
                    _BLOSUM_MATRIX[i, j] = 1
                elif aa1 in set("DE") and aa2 in set("DE"):
                    _BLOSUM_MATRIX[i, j] = 2
                elif aa1 in set("KR") and aa2 in set("KR"):
                    _BLOSUM_MATRIX[i, j] = 2
                else:
                    _BLOSUM_MATRIX[i, j] = -2

def _get_blosum_vector(seq):
    """Average BLOSUM62 substitution scores for each amino acid."""
    vec = np.zeros(20)
    if not seq:
        return vec
    for aa in seq.upper():
        if aa in AA_LIST:
            idx = AA_LIST.index(aa)
            vec += _BLOSUM_MATRIX[idx]
    return vec / len(seq)

# ----------------------------------------------------------------------
# Feature extraction functions

def compute_aa_composition(seqs):
    """AA frequencies (20 columns)."""
    arr = []
    for seq in seqs:
        if not isinstance(seq, str) or len(seq) == 0:
            arr.append([0.0] * 20)
            continue
        s = seq.upper()
        length = len(s)
        arr.append([s.count(aa) / length for aa in AA_LIST])
    return pd.DataFrame(arr, columns=[f"aa_{aa}" for aa in AA_LIST])

def compute_kmer_frequencies(seqs, k=2, max_features=None):
    """k‑mer frequencies; for k=3 selects top max_features by global count."""
    if k == 2:
        kmers = [a+b for a in AA_LIST for b in AA_LIST]
    elif k == 3:
        all_kmers = [a+b+c for a in AA_LIST for b in AA_LIST for c in AA_LIST]
        global_counter = Counter()
        for seq in seqs:
            if isinstance(seq, str) and len(seq) >= k:
                global_counter.update(seq[i:i+k] for i in range(len(seq)-k+1))
        if max_features is None:
            max_features = 500
        top_kmers = [kmer for kmer, _ in global_counter.most_common(max_features)]
        if len(top_kmers) < max_features:
            remaining = sorted(set(all_kmers) - set(top_kmers))
            top_kmers.extend(remaining[:max_features - len(top_kmers)])
        kmers = top_kmers
    else:
        raise ValueError("k must be 2 or 3")
    arr = []
    for seq in seqs:
        if not isinstance(seq, str) or len(seq) < k:
            arr.append([0.0] * len(kmers))
            continue
        s = seq.upper()
        counts = Counter(s[i:i+k] for i in range(len(s)-k+1))
        total = max(1, len(s)-k+1)
        arr.append([counts.get(kmer, 0) / total for kmer in kmers])
    return pd.DataFrame(arr, columns=[f"kmer{k}_{kmer}" for kmer in kmers])

def compute_onehot_mean(seqs):
    """Mean one‑hot encoding (20 columns)."""
    arr = []
    for seq in seqs:
        if not isinstance(seq, str) or len(seq) == 0:
            arr.append([0.0] * 20)
            continue
        s = seq.upper()
        onehot = np.zeros(20)
        for aa in s:
            if aa in AA_LIST:
                onehot[AA_LIST.index(aa)] += 1
        onehot /= len(s)
        arr.append(onehot)
    return pd.DataFrame(arr, columns=[f"oh_{aa}" for aa in AA_LIST])

def compute_physicochemical(seqs):
    """Seven AA‑index derived features (mean per property)."""
    arr = []
    for seq in seqs:
        if not isinstance(seq, str) or len(seq) == 0:
            arr.append([0.0] * 7)
            continue
        s = seq.upper()
        vec = []
        for prop in PHYS_PROPERTIES:
            vals = [prop.get(aa, 0.0) for aa in s]
            vec.append(np.mean(vals))
        arr.append(vec)
    return pd.DataFrame(arr, columns=[f"phys_{name}" for name in PHYS_NAMES])

def compute_blosum62_profile(seqs):
    """BLOSUM62 average score profile (20 columns)."""
    arr = [_get_blosum_vector(seq) for seq in seqs]
    return pd.DataFrame(arr, columns=[f"blosum_{aa}" for aa in AA_LIST])

def compute_length_and_moments(seqs):
    """Protein length, mean and std of hydrophobicity."""
    arr = []
    for seq in seqs:
        if not isinstance(seq, str) or len(seq) == 0:
            arr.append([0.0, 0.0, 0.0])
            continue
        s = seq.upper()
        hydro = [HYDROPHOBICITY.get(aa, 0.0) for aa in s]
        arr.append([len(s), np.mean(hydro), np.std(hydro)])
    return pd.DataFrame(arr, columns=['length', 'hydrophob_mean', 'hydrophob_std'])

# ----------------------------------------------------------------------
# ESM‑2 embeddings with caching
ESM_MODEL_NAME = "facebook/esm2_t6_8M_UR50D"
ESM_EMBED_DIM = 320
ESM_COLS = [f"esm_{i}" for i in range(ESM_EMBED_DIM)]

_esm_model = None
_esm_tokenizer = None
_esm_device = None

def _load_esm_model(device=None):
    global _esm_model, _esm_tokenizer, _esm_device
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if _esm_model is None or _esm_device != device:
        log.info(f"Loading ESM‑2 model on {device}...")
        _esm_tokenizer = AutoTokenizer.from_pretrained(ESM_MODEL_NAME)
        _esm_model = AutoModel.from_pretrained(ESM_MODEL_NAME).to(device).eval()
        _esm_device = device
    return _esm_model, _esm_tokenizer, device

def compute_esm2(seqs, protein_ids, id_to_seq, cache_path=None, batch_size=32,
                 save_every_n_batches=10, device=None):
    done = pd.DataFrame(columns=ESM_COLS, dtype=float)
    if cache_path and Path(cache_path).exists():
        done = pd.read_parquet(cache_path)
        if done.index.name != 'id':
            done = done.reset_index().rename(columns={'index': 'id'}).set_index('id')
        done = done[done.index.isin(protein_ids)]
        done = done[~done.index.duplicated(keep='first')]
        log.info(f"Loaded {len(done)} cached embeddings from {cache_path}.")

    missing = [pid for pid in protein_ids if pid not in done.index]
    if not missing:
        log.info("All embeddings already cached.")
        return done.loc[protein_ids]

    log.info(f"Computing {len(missing)} ESM‑2 embeddings...")
    model, tokenizer, dev = _load_esm_model(device)

    accum_emb = []
    accum_ids = []
    n_batches = (len(missing) + batch_size - 1) // batch_size
    for batch_idx, batch_start in enumerate(range(0, len(missing), batch_size)):
        batch_ids = missing[batch_start:batch_start + batch_size]
        print(f"Batch {batch_idx+1}/{n_batches}...", end=" ", flush=True)
        try:
            batch_seqs = [id_to_seq[pid] for pid in batch_ids]
        except KeyError as e:
            log.error(f"Missing sequence for protein_id: {e}")
            continue
        try:
            # Truncate to 1024 tokens – prevents OOM on very long proteins
            inputs = tokenizer(
                batch_seqs,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=1024
            )
            inputs = {k: v.to(dev) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = model(**inputs)
            emb = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            accum_emb.append(emb)
            accum_ids.extend(batch_ids)
        except Exception as e:
            log.error(f"Error on batch {batch_idx+1}: {e}. Skipping this batch.")
            # continue to next batch without saving these IDs
            continue

        if (batch_idx + 1) % save_every_n_batches == 0 or batch_start + batch_size >= len(missing):
            if accum_emb:
                partial = np.concatenate(accum_emb, axis=0)
                chunk = pd.DataFrame(partial, index=accum_ids, columns=ESM_COLS)
                done = pd.concat([done, chunk])
                done = done[~done.index.duplicated(keep='first')]
            if cache_path:
                done.to_parquet(cache_path)
                log.info(f"Saved {len(done)} embeddings ({100*len(done)/len(protein_ids):.1f}%).")
            accum_emb, accum_ids = [], []

    return done.loc[protein_ids]


# ----------------------------------------------------------------------
# Genome-level nucleotide features
# ----------------------------------------------------------------------
def compute_genome_dna_features(genome_nt_dir, organisms, cache_path=None):
    """
    Parse *_genome_nt.txt files and compute per-organism DNA features.
    Returns a DataFrame indexed by organism name.
    """
    features = {}
    for org in organisms:
        nt_file = Path(genome_nt_dir) / org / f"{org}_genome_nt.txt"
        if not nt_file.exists():
            continue
        with open(nt_file, 'r') as f:
            seq = ''.join(line.strip() for line in f if not line.startswith('>'))
        if not seq:
            continue
        seq = seq.upper()
        total = len(seq)
        gc = (seq.count('G') + seq.count('C')) / total if total > 0 else 0

        # Dinucleotide frequencies (16 features)
        dinucs = [a+b for a in 'ACGT' for b in 'ACGT']
        dinuc_counts = Counter(seq[i:i+2] for i in range(total-1))
        dinuc_freqs = {f"dna_di_{d}": dinuc_counts.get(d, 0) / max(1, total-1) for d in dinucs}

        features[org] = {
            'genome_size': total,
            'gc_content': gc,
            **dinuc_freqs
        }

    df = pd.DataFrame.from_dict(features, orient='index')
    df.index.name = 'organism'
    if cache_path:
        df.to_parquet(cache_path)
    return df

# ----------------------------------------------------------------------
# High‑level feature builder
_FEATURE_FUNCTIONS = {
    'aa': lambda seqs, **kwargs: compute_aa_composition(seqs),
    'kmer2': lambda seqs, **kwargs: compute_kmer_frequencies(seqs, k=2),
    'kmer3': lambda seqs, **kwargs: compute_kmer_frequencies(seqs, k=3, max_features=kwargs.get('max_kmer3', 500)),
    'onehot': lambda seqs, **kwargs: compute_onehot_mean(seqs),
    'physicochemical': lambda seqs, **kwargs: compute_physicochemical(seqs),
    'blosum62': lambda seqs, **kwargs: compute_blosum62_profile(seqs),
    'length_moments': lambda seqs, **kwargs: compute_length_and_moments(seqs),
    'esm2': lambda seqs, ids, cache, **kwargs: compute_esm2(
        seqs, ids, id_to_seq=id_to_seq, cache_path=cache, batch_size=kwargs.get('esm_batch_size', 32),
        device=kwargs.get('device', None)
    )
}

def compute_features(seqs, organism_name, best_combo, train_columns,
                     protein_ids=None, esm_cache_path=None, **kwargs):
    """
    Compute all feature sets listed in best_combo for given sequences.
    Returns a DataFrame with columns matching `train_columns` (organism omitted).
    """
    if protein_ids is None:
        protein_ids = [f"seq_{i}" for i in range(len(seqs))]
    id_to_seq = {pid: seq for pid, seq in zip(protein_ids, seqs)}

    feature_dfs = {}
    for name in best_combo:
        log.info(f"Computing feature: {name}")
        if name == 'esm2':
            df = compute_esm2(seqs, protein_ids, id_to_seq, cache_path=esm_cache_path, **kwargs)
            if df.index.name != 'id' and len(df) == len(protein_ids):
                df.index = protein_ids
        else:
            df = _FEATURE_FUNCTIONS[name](seqs, **kwargs)
            if len(df) == len(protein_ids):
                df.index = protein_ids
        feature_dfs[name] = df

    X = None
    for name in best_combo:
        df = feature_dfs[name]
        if X is None:
            X = df
        else:
            X = pd.concat([X, df], axis=1)

    # Align with training columns (organism column already excluded from train_columns)
    X = X.reindex(columns=train_columns, fill_value=0.0)
    return X
    