"""Probe exact SQL identifiers for all NMDC-labeled databases and their tables."""
import berdl_notebook_utils as bnu

dbs = bnu.get_databases(return_json=False)
nmdc_dbs = [d for d in dbs if "nmdc" in d.lower()]
print("=== ALL databases containing 'nmdc' ===")
for d in nmdc_dbs:
    print(" ", repr(d))

print("\n=== tables per nmdc database ===")
for d in nmdc_dbs:
    try:
        tbls = bnu.get_tables(d, return_json=False)
        print(f"\n## {d}  ({len(tbls)} tables)")
        for t in tbls:
            print("   -", t)
    except Exception as e:
        print(f"\n## {d}  ERROR: {type(e).__name__}: {str(e)[:200]}")
