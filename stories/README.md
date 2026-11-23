# Stories
One folder per story. A thread reads CLAUDE.md + ONE story's STORY.md, never the others, so each story stays small.

## Start a new story (one-off, spin-off or new series)
1. `cp -r stories/_template stories/<name>` (lowercase, no spaces). Pick a unique 2-3 letter **id tag** (check `ls stories/*/data`): parts are `<tag>1`, `<tag>2`... A one-off is just `<tag>1`.
2. Fill `STORY.md` (premise, genre, cast, world, status). Keep it under ~400 words; rules belong in CLAUDE.md, not here.
3. Write the script into `part1/` (~1 minute, max 1:10) (workflow step 1). Voices go to `part1/voice/<who>_<tag>1.mp3`.
4. Audio: `align_full.py` / `split_lines.py` → `data/<tag>1/lines_<who>.json`; copy `prep_template.py` to `audio/prep_<tag>1.py`.
5. Scene: copy `scene_template.py` to `scripts/<tag>1.py`. `restore.sh` and `pod_setup.sh` pick up every story's `scripts/` and `data/` automatically.
6. Exports land in `stories/<name>/exports/` on the laptop (`download_to` in render_job.json).

## Reuse
- **Spin-off in an existing world:** `boot("<tag>1", world="bloxbury", ...)` and reuse its cards (`make_milo`, `make_rae`...). Mention the parent story's STORY.md only for the facts you need (copy them into yours).
- **New setting:** build it from library sets/props, or register `@world("<name>")` in your scene script before `boot()` (see `_pipeline/ENGINE.md`). Anything Joel approves goes to the library, so the next story gets it for free.
- New recurring characters: asset sheet → Joel OK → card in `recurring.py` (shared library), listed in your STORY.md.
