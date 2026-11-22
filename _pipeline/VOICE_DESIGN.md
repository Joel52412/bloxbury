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
