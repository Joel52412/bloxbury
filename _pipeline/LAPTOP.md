# Laptop folder = git clone (replaces copying files by hand)
`C:\Users\frimp\Downloads\robloxshorts` tracks `main` on GitHub. Laptop-only files (exports, voice clones, inspo,
approval sheets, `_tmp`, `_to_delete`, `sort through`) are in `.gitignore`, so git never touches them.

## One-time setup (Joel, ~3 min)
1. Install Git: open PowerShell, `winget install --id Git.Git -e`, then close PowerShell.
2. Double-click `_tools\Setup Git Clone.bat` (copy it over from GitHub first if the folder predates it). It links the
   folder to GitHub without deleting anything and lists files that differ from GitHub.
3. If that list only shows old copies of repo files, run `git checkout -- .` in the folder (or tell Claude the list).

## Every update
After a PR merges, double-click `_tools\Pull Latest.bat`. If it stops, a laptop copy of a repo file was edited:
send Claude the list it prints.

## Claude
Never push from the laptop (GitHub is the source). To pull on Joel's behalf via `device_bash`
(`git -C ~/mnt/robloxshorts pull --ff-only`), ask Joel first and request delete permission once (git replaces files by
deleting them). Before the clone exists, keep copying with `device_commit_files`.
