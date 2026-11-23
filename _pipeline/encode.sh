# encode.sh - ONE set of export settings for every final mp4 (sourced by make_part, join_segments, make_tiktok,
# pod_range, make_youtube). Dark horror frames band badly after YouTube/TikTok re-compression, so:
#  * x264 slow, CRF 15, aq-mode=3 (spends bits on dark flat areas)
#  * fine temporal luma grain, strength 2 (23 Nov test on Part 3: dark banding plateaus after a YouTube-like re-encode
#    32% -> 14%; file ~2.5x bigger, ~135 MB per 80 s. GRAIN=1 = 24%, same size as none)
# GRAIN=0 turns the grain off (use it when re-encoding a file that already has grain, e.g. TikTok/YouTube cuts).
X264="-c:v libx264 -preset ${PRESET:-slow} -crf ${CRF:-15} -x264-params aq-mode=3 -pix_fmt yuv420p -movflags +faststart"
G=${GRAIN:-2}; GRAIN_VF=""; [ "$G" != "0" ] && GRAIN_VF="noise=c0s=$G:c0f=t,"
