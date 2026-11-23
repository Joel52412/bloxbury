# Lighting playbook (all stories) (Joel 22 Nov 22:44: "film-grade, keeps viewers intrigued, render time must not double")
Pick the palette that serves the scene (not always cold blue). Every shot:
1. **One motivated key** with a story reason: moon through a window, a practical (lamp, door gap, screen, torch, street lamp).
2. **Key on the SHORT side** (the side of the face turned away from camera) for tension; broad/even light only for safe, happy beats.
3. **Low fill** (shadows dark, never crushed); **rim/edge** in the opposite temperature for separation (cool moon edge vs warm key, or warm practical edge vs cool key).
4. **Texture:** cookies from real geometry (window bars, `p6_branches` limb outside the window, sway it), practicals in frame with bloom.
5. **Palette by beat:** warm = safety/memory (drawing, Rae's hall); cool moon = dread; sodium orange street light vs blue night for exteriors; red 3AM clock = small danger accent only.
6. **Grade:** `lookdev.cinematic_look()` (AgX contrast, bloom on practicals, vignette, cool-shadow/warm-highlight split, slight lens fringe). Per-shot `exposure` when white paper / bright studio would blow out.
7. **Cost:** lights + grade only (no volumes, no extra bounces): measured +3 % render time. Spots far away need high energy (inverse square): moon spot ~45 000 W at ~30 units.
8. Check every moon line with a ray cast: window rails/muntins, sill props and the cookie must not black out the subject.
9. Exteriors: the town's street lamps (`street_lamps()`) and the night sun light everything; drop them, then add ONE tight spot as the key. A wide area light floods walls and grass = day look.
