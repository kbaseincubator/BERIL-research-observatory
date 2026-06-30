"""Download fitness + experiment files for psRCH2 from FitnessBrowser website.

psRCH2 (P. stutzeri RCH2) is in Spark but only 3 Cd experiments are captured there.
The website shows 50 stress compounds. This script downloads the full dataset.
"""
import sys, time
from pathlib import Path

sys.path.append('/opt/conda/lib/python3.13/site-packages')
from curl_cffi import requests

BASE_URL = "https://fit.genomics.lbl.gov"
ORG = "psRCH2"
OUTDIR = Path("/home/hmacgregor/BERIL-research-observatory/projects/refocus/data/fitness_browser") / ORG

FILES = {
    "experiments": f"{BASE_URL}/cgi-bin/createExpData.cgi?orgId={ORG}",
    "fitness":     f"{BASE_URL}/cgi-bin/createFitData.cgi?orgId={ORG}",
}

sess = requests.Session(impersonate="chrome131")
sess.get(f"{BASE_URL}/")  # cookie init
time.sleep(1)

for name, url in FILES.items():
    out = OUTDIR / f"{ORG}_{name}.txt"
    if out.exists():
        print(f"{name}: already exists ({out.stat().st_size} bytes)")
        continue
    print(f"Downloading {name}...")
    resp = sess.get(url, timeout=120)
    resp.raise_for_status()
    out.write_bytes(resp.content)
    print(f"  Saved {out.stat().st_size} bytes → {out}")
    time.sleep(2)

print("Done.")
