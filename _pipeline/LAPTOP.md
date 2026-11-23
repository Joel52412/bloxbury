# Laptop folder = git clone of `main` (since 23 Nov)
`C:\Users\frimp\Downloads\robloxshorts` is a git clone. Laptop-only files (exports, voice clones, inspo, approval
sheets, `_tmp`, `_to_delete`, `sort through`, banners) are ignored or untracked, so git never touches them.
Old audio copies replaced at setup are backed up in `_tmp/laptop_backup_23nov/`.

## Claude updates it (after every merge)
The laptop shell can't reach GitHub (proxy 403), so ship a bundle:
1. Here: `git -C $HOME/mnt/robloxshorts log -1 --format=%H` (laptop HEAD, via device_bash) = `OLD`. In a FULL (not
   `--depth 1`) clone: `git bundle create /mnt/project-files/upd.bundle OLD..main` (split -b 20m if over 25 MB).
2. `device_commit_files` it to `robloxshorts\_tmp\upd.bundle`, then on the laptop:
   `git fetch _tmp/upd.bundle main:refs/remotes/bundle/main && git merge --ff-only bundle/main && rm _tmp/upd.bundle`
   (a plain `git pull <bundle> main` printed "Already up to date" and left HEAD unmoved, 23 Nov). Stash any
   hand-copied files first (`git stash push -- <files>`), so nothing unmerged is lost.
3. git needs delete permission in that folder (device_request_delete_permission) or it leaves `.lock` files.

## Joel (optional)
With Git for Windows installed (`winget install --id Git.Git -e`), double-click `_tools\Pull Latest.bat`.
