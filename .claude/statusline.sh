#!/usr/bin/env bash
python3 -c '
import json, sys
d = json.load(sys.stdin)
model = d.get("model", {}).get("display_name", "")
cwd = d.get("workspace", {}).get("current_dir", "")
print(f"BERIL | {model} | {cwd}")
'
