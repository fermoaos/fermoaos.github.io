#!/usr/bin/env bash
# Assemble the hero film draft from segment clips: re-encode concat (never -c copy), then finalize 1280x720@24.
set -euo pipefail
cd "$(dirname "$0")/../../.."
D=outputs/omni-video/fermoa-hero
S1=${S1:-$D/seg_01_v2.mp4}; S2=${S2:-$D/seg_02_v2.mp4}; S3=${S3:-$D/seg_03a_v2.mp4}; S4=${S4:-$D/seg_04.mp4}
for f in "$S1" "$S2" "$S3" "$S4"; do [ -s "$f" ] || { echo "missing $f"; exit 1; }; done
printf "file '%s'\nfile '%s'\nfile '%s'\nfile '%s'\n" "$PWD/$S1" "$PWD/$S2" "$PWD/$S3" "$PWD/$S4" > $D/concat.txt
ffmpeg -v error -y -f concat -safe 0 -i $D/concat.txt -c:v libx264 -crf 16 -preset medium -pix_fmt yuv420p -r 24 -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2" -c:a aac -b:a 160k $D/draft_raw.mp4
ffmpeg -v error -y -i $D/draft_raw.mp4 -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -c:a copy $D/draft_v1.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 $D/draft_v1.mp4
ffmpeg -v error -y -i $D/draft_v1.mp4 -vf "fps=0.5,scale=320:-1,tile=6x3" $D/qa/draft_v1-contact.jpg
echo "draft: $D/draft_v1.mp4"
