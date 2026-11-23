# Studio asset library (catalogue)
Approved assets only (Joel signs off every one). Shared by every story; a story may reuse anything here.

- `engine/`: Blender Python that builds every asset + `scene_kit.py`. `studio.py` is the registry: only what's listed there gets used.
- `approval_sheets/`: the images Joel approved. `manifest.json`: the same list, machine-readable.
- New assets go through an asset sheet and Joel's sign-off before they're added.

## Registry (`studio.py`)
CAST tags F1–F6, B1–B6, C1–C24, K1–K12 via `studio_character(tag)` (random extras). Keep a/b versions of B4, C19, K11.

## Approved
- **Faces:** M2 (+12 emotions, `faces4.RARE`). Banned: faces A–E, M1.
- **Hair:** H2 H3 H4 H8, M1–M6, X1–X6 (under-hat hair for hats). Banned: H1, H5, H6, H7, downloaded .obj hair.
- **Outfits:** O1–O4 + role/kids/teen.
- **Props:** batches 1–6. 4 = set dressing (`dress_kitchen/hallway/bedroom`, two-tone walls, frames, shelves, coats, sconces, calendar/drawing); 5 = town detail (`detail_town`/`detail_house`); 6 = note, pencil, drawing, bedroom door + light gap, side window, fence gap, branches cookie, torch, phone, door set. `lookdev` grade.
- **Sets:** Bloxbury Town, a kid's bedroom (Milo's), kitchen, hallway (mirror), hollow closet.
- **Cards** (`recurring.py`, from BLOXBURY; reusable in spin-offs): MILO (`rig2.make_milo`), RAE, MAYOR, DAN, NEIGHBOUR, MUM. **Monster:** THE KNOCKER (`monster.make_knocker`).
- Night lighting template: `stories/bloxbury/scripts/part3_assets.py` (`night()`, `spot()`, `cookie_on()`, `street_lamps()`).
