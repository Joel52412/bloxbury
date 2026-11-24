# Voice design for new characters (ElevenLabs Voice Design)
Every new speaking character gets a Voice Design prompt, preview text and settings from Claude.

## Prompt formula (from ElevenLabs' own best practices)
1. Language + regional variant FIRST (stops accent drift). "accent" only for regional dialect; "thick" not "strong".
2. Gender described as a sound ("soft, mid-range female voice"), plus a specific age ("in her mid-30s").
3. Quality: "Studio-quality recording." (drop it for very niche/monster voices).
4. Persona in 2-5 words, then 2-3 emotion adjectives.
5. 1-2 sentences on timbre (warm, airy, gravelly...), pacing and delivery. Keep timbre and emotion separate.
6. Pace + pitch live in the prompt (j 24 Nov): ask for quick, energetic, slightly higher delivery there. The mix never speeds up or pitch-shifts voices.
7. Never write effects words (reverb, echo, phone, tape). Effects (doubles, distortion) are added in our mix instead.
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


## SFX requests
Real-world sounds always come from Joel's ElevenLabs Sound Effects (synth only for abstract thuds/swells). Request: prompt starting with the file key, then source, distance, room, texture, duration (no "no music, no voices" tail, j 24 Nov); prompt influence 0.6–0.7. Files arrive as `Key_words_N-<id>.mp3` in `assets/sfx/`; cue sheets match the key prefix + `[_#]N-` and set the level by RMS.

| Key | Used | Prompt | Dur | Infl |
|---|---|---|---|---|
| `pan_sizzle` (#1 used, #4 spare) | Part 2 kitchen 1.25–7.0 s, `SIZZLE_DB` −46 | Pan sizzle, butter and pancake batter frying gently in a hot pan, close-up in a quiet home kitchen, steady soft hiss with small fat pops, morning, no music, no voices | 6 s | 0.65 |
