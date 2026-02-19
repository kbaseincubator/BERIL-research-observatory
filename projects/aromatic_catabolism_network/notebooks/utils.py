"""Shared utilities for the aromatic catabolism network project."""


def categorize_gene(row):
    """Categorize a quinate-specific gene by functional subsystem.

    Uses RAST function description keywords. Validated against co-fitness
    assignments in NB03 — see data/final_network_model.csv for the
    co-fitness-refined categories.
    """
    import pandas as pd
    func = str(row['rast_function']) if pd.notna(row.get('rast_function')) else ''

    if 'NADH' in func and ('ubiquinone' in func or 'oxidoreductase chain' in func):
        return 'Complex I'
    elif any(kw in func.lower() for kw in [
        'protocatechuate', 'catechol', 'muconate', 'muconolactone',
        'ketoadipate', 'quinate', 'dehydroquinate'
    ]):
        return 'Aromatic pathway'
    elif 'PQQ' in func or 'pyrroloquinoline' in func.lower():
        return 'PQQ biosynthesis'
    elif any(kw in func.lower() for kw in [
        'siderophore', 'iron', 'exbd', 'tolr', 'ferrichrome', 'tonb'
    ]):
        return 'Iron acquisition'
    elif 'regulator' in func.lower() or 'regulatory' in func.lower():
        return 'Regulation'
    elif 'hypothetical' in func.lower() or 'DUF' in func or 'Uncharacterized' in func:
        return 'Unknown'
    else:
        return 'Other'
