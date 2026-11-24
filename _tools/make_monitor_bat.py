#!/usr/bin/env python3
# make_monitor_bat.py - one-click Render Monitor launcher for a pod render (Joel 24 Nov: no typing pod ids).
# Usage: python3 make_monitor_bat.py "<Name>" <out_dir> <pod_id>:<jupyter_token> [...]
#   -> <out_dir>/Monitor <Name>.bat : double-click on the laptop; opens the monitor watching those pods.
# Claude runs it right after creating the pods and sends the .bat in chat (attached from project files).
import json, os, sys
name, out = sys.argv[1], sys.argv[2]
jobs = [{"kind": "runpod", "pod_id": a.split(":", 1)[0], "token": a.split(":", 1)[1], "name": "%s pod %d" % (name, i + 1),
         "auto_download": False} for i, a in enumerate(sys.argv[3:])]
js = json.dumps({"watch_folders": [], "jobs": jobs, "local_poll_s": 2, "remote_poll_s": 5})
for c in "^&<>|": js = js.replace(c, "^" + c)
js = js.replace("%", "%%")
p = os.path.join(out, "Monitor %s.bat" % name)
open(p, "w", newline="\r\n").write("\n".join([
    "@echo off", "rem Double-click: opens the Render Monitor already watching the %s pods." % name,
    'cd /d "C:\\Users\\frimp\\Downloads\\robloxshorts\\_tools"', "set CFG=%%TEMP%%\\monitor_%s.json" % name.replace(" ", "_"),
    '> "%CFG%" echo ' + js, 'start "" pythonw render_monitor.py --config "%CFG%"']) + "\n")
print(p)
