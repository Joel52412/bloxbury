"""Part 1 cue sheet: where every voice line and sound effect goes (final video time, seconds).

Voice cues: (file, src_start, src_end, dest_start, caption_text, style, effect)
style: "w" white, "r" red. Words in HIGHLIGHT turn yellow in white captions.
"""

VOICE = [
    ("milo", 0.26, 2.33, 0.05, "Never open the door after 3 A.M.", "r", None),
    ("milo", 2.99, 4.58, 2.30, "We moved to Bloxbury on a Tuesday.", "w", None),
    ("milo", 4.93, 5.59, 4.80, "By Wednesday,", "w", None),
    ("milo", 5.80, 7.05, 5.67, "I knew something was wrong.", "w", None),
    ("milo", 7.28, 8.51, 9.20, "Mum said she'd be home late.", "w", None),
    ("milo", 8.75, 9.62, 12.10, "She always was.", "w", None),
    ("milo", 9.97, 11.25, 13.40, "...I never actually saw her.", "w", None),
    ("milo", 11.57, 13.98, 15.60, "The girl next door, Rae, didn't even say hello.", "w", None),
    ("rae", 0.00, 0.52, 18.20, "New kid?", "w", None),
    ("rae", 0.96, 1.50, 18.95, "One rule.", "w", None),
    ("rae", 1.96, 3.45, 20.20, "Three knocks after 3 A.M....", "w", None),
    ("rae", 3.84, 4.71, 22.10, "you don't answer.", "w", None),
    ("rae", 5.14, 5.48, 23.40, "EVER.", "r", None),
    ("milo", 14.24, 16.59, 25.75, "I thought she was joking. She wasn't.", "w", None),
    ("rae", 5.96, 6.65, 28.45, "I keep a list.", "w", None),
    ("rae", 6.98, 7.81, 29.30, "Of who's left.", "w", None),
    ("milo", 16.94, 17.55, 30.50, "...Who's left?", "w", None),
    ("milo", 17.89, 20.23, 31.95, "That afternoon, everyone boarded up their windows.", "w", None),
    ("milo", 20.48, 22.06, 35.95, "And the Mayor's house had no door.", "w", None),
    ("milo", 22.32, 24.71, 40.40, "At 2:57, every light in Bloxbury...", "w", None),
    ("milo", 25.01, 25.61, 43.75, "went off.", "w", None),
    ("milo", 25.91, 26.66, 45.95, "Except mine.", "r", None),
    ("milo", 27.06, 27.58, 51.50, "3 A.M.", "r", None),
    ("milo", 27.90, 30.59, 57.75, "KNOCK. KNOCK. KNOCK.", "w", None),
    ("milo", 30.83, 33.57, 60.75, "I checked the window. Nobody was there.", "w", None),
    ("milo", 33.84, 35.19, 63.60, "Then it went quiet.", "w", None),
    ("closet", 0.28, 1.67, 66.90, "Then the knocking came again.", "w", None),
    ("closet", 2.20, 3.62, 69.00, "From INSIDE my closet.", "r", None),
    ("milo", 35.43, 36.51, 73.95, "And a voice whispered...", "w", None),
    ("milo", 36.99, 38.61, 76.00, "\"Milo... let me out.\"", "r", "echo"),
    ("milo", 38.93, 40.12, 78.75, "It knew my name.", "r", None),
    ("outro", 0.00, 1.68, 80.80, "Want to find out who was in my closet?", "w", None),
    ("outro", 1.94, 3.29, 82.75, "FOLLOW and LIKE for PART 2!", "w", None),
    ("outro", 3.62, 4.41, 84.60, "...and whatever you do...", "w", None),
    ("outro", 5.02, 5.81, 86.00, "don't open the door.", "r", None),
]

HIGHLIGHT = {"FOLLOW", "LIKE", "PART", "2!", "NEVER", "ALWAYS", "RAE", "EVER", "LEFT", "LEFT?", "OFF", "MINE", "NOBODY", "INSIDE",
             "CLOSET", "NAME", "KNOCK", "DOOR"}

# Sound effects: (key, dest_start, max_len, volume, fade_in, fade_out, filter)
SFX = [
    ("knock1", 0.0, 3.0, 0.55, 0, 0.3, None),
    ("hammer", 32.2, 3.4, 0.45, 0.1, 0.6, None),
    ("drone", 38.5, 27.2, 0.22, 2.0, 1.5, "loop"),
    ("tick", 47.8, 3.6, 0.45, 0.2, 0.4, None),
    ("buzz", 53.0, 3.0, 0.8, 0, 0.3, None),
    ("buzz", 54.7, 2.2, 0.7, 0, 0.5, None),
    ("knock2", 68.35, 2.2, 0.85, 0, 0.3, "muffled"),
    ("drone", 68.6, 9.9, 0.30, 1.0, 1.0, None),
    ("creak", 70.45, 3.4, 2.2, 0, 0.5, None),
    ("sting", 78.5, 2.0, 0.90, 0, 0.3, None),
    ("sting", 86.0, 2.0, 0.55, 0, 0.4, None),
]

SFX_FILES = {
    "knock1": "sfx_three_heavy_do.mp3", "knock2": "sfx_three_heavy_do_2.mp3", "hammer": "sfx_Sharp__rhythmi.mp3",
    "drone": "sfx_low_horror_dro.mp3", "tick": "sfx_clock_ticking_.mp3", "buzz": "sfx_buzzing_street.mp3",
    "creak": "sfx_creaking_woode.mp3", "sting": "sfx_a_sharp_horror.mp3",
}

TOTAL = 88.1

# Animation retime: old timeline second -> extra seconds inserted (cumulative)
WARP = [(15.55, 1.6), (20.5, 0.6), (25.4, 0.6), (54.4, -1.0)]
