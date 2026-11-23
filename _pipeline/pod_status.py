#!/usr/bin/env python3
# pod_status.py - merge key=value pairs into /workspace/render_output.json (atomic), the file the Render Monitor reads.
# Usage: python3 pod_status.py stage=rendering frames=12      (STATUS_OUT overrides the path for local tests)
import json, os, sys, time
p = os.environ.get("STATUS_OUT", "/workspace/render_output.json")
try: d = json.load(open(p))
except (OSError, ValueError): d = {}
for kv in sys.argv[1:]:
    k, v = kv.split("=", 1); d[k] = int(v) if v.isdigit() else v
d["updated"] = time.time(); json.dump(d, open(p + ".tmp", "w")); os.replace(p + ".tmp", p)
