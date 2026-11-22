# Voice design for new characters (ElevenLabs Voice Design)
Joel (22 Nov): for every new speaking character, Claude writes the Voice Design prompt, preview text and settings.

## Prompt formula (from ElevenLabs' own best practices)
1. Language + regional variant FIRST (stops accent drift). "accent" only for regional dialect; "thick" not "strong".
2. Gender described as a sound ("soft, mid-range female voice"), plus a specific age ("in her mid-30s").
3. Quality: "Studio-quality recording." (drop it for very niche/monster voices).
4. Persona in 2-5 words, then 2-3 emotion adjectives.
5. 1-2 sentences on timbre (warm, airy, gravelly...), pacing and delivery. Keep timbre and emotion separate.
6. Never write effects words (reverb, echo, phone, tape). Effects (doubles, distortion) are added in our mix instead.
- Preview text must MATCH the description, and be a full sentence or short paragraph (longer = steadier voice).
- Guidance: ~30-40%. Higher = stricter accent/tone, lower = better audio and acting.
- Generate, pick the best of the previews, save the voice, then test the hardest line from the script (e.g. the whisper).

## Cast voices
### MUM (Part 2, 22 Nov), one voice for both the fake and the real Mum
Prompt:
British English, Southern England accent. A woman in her mid-30s with a soft, smooth, mid-range voice. Studio-quality recording. A gentle, devoted single mum. Warm, tender and quietly tired. She speaks at a relaxed, conversational pace and you can hear the smile in her words, with a light breathiness that lets her drop into a fragile, intimate whisper while staying clear.
Preview text:
Morning, sweetheart. I made pancakes, your favourite. Come here and give me a hug... I've missed you so much. Now eat up before it goes cold, okay? I love you, bug.
Settings: guidance ~35%. Test lines after saving: "Bug... don't go down there." (whisper) and "Milo! Dinner's ready. Come downstairs." (calling)
Fake Mum = same voice, made "slightly too perfect" in our mix (tiny timing tweaks, faint pitch-shifted double), not in ElevenLabs.


## SFX requests (Joel, 22 Nov 15:25)
**Never fake a real-world sound with synthesised noise** (Part 2's synth pan sizzle read as crackle/static). Joel makes custom SFX in ElevenLabs Sound Effects: for any sound not already in `assets/sfx/`, Claude sends him a request with:
- **Prompt:** start it with the file key (ElevenLabs names the file from the first words, e.g. `Pan_sizzle,_...#1-<id>.mp3`), then the source, distance, room, texture, and "no music, no voices".
- **Duration** and **Prompt influence** (0.6–0.7 for literal sounds), and which of the 4 variants to pick by default.
Joel drops the files in `assets/sfx/` (laptop folder), Claude pushes them and the cue sheet loads them by key + variant. Synthesised audio is only OK for abstract things (low thuds, sub swells).

| Key | Used in | Prompt | Duration | Influence |
|---|---|---|---|---|
| `pan_sizzle` ✅ received 15:31 (#1 used, #4 spare; files arrive ~−48 dB, the cue sheet sets the level) | Part 2 kitchen 1.25–7.0 s (under "Morning, Milo!"), level 0.30 | Pan sizzle, butter and pancake batter frying gently in a hot pan, close-up in a quiet home kitchen, steady soft hiss with small fat pops, morning, no music, no voices | 6 s | 0.65 |

ElevenLabs names downloads like `Pan_sizzle_butter_a_1-<id>.mp3` (no `#`): cue sheets match the key prefix + `[_#]<variant>-`.
