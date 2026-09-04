#!/usr/bin/env bash
# Assemble the hero film draft from segment clips: re-encode concat (never -c copy), then finalize 1280x720@24.
# Round 2: 8 segments (S1, S2, S3 x5 destinations, S4). Override any with env vars.
set -euo pipefail
cd "$(dirname "$0")/../.."          # -> parent repo root (ai-strategy-private)
D=outputs/omni-video/fermoa-hero
OUTDIR=${OUTDIR:-fermoa-site/brand/film}
TAG=${TAG:-v2}
S1=${S1:-$D/seg_01_v2.mp4}
S2=${S2:-$D/seg_02_r2.mp4}
S3=${S3:-$D/seg_03a_r2c.mp4}
S3B=${S3B:-$D/seg_03b_r2.mp4}
S3C=${S3C:-$D/seg_03c_r2.mp4}
S3D=${S3D:-$D/seg_03d_r2.mp4}
S3E=${S3E:-$D/seg_03e_r2.mp4}
S4=${S4:-$D/seg_04.mp4}
SEGS=(); for f in "$S1" "$S2" "$S3" "$S3B" "$S3C" "$S3D" "$S3E" "$S4"; do
  [ -n "$f" ] || continue; [ -s "$f" ] || { echo "missing $f"; exit 1; }; SEGS+=("$f"); done
mkdir -p "$D/qa" "$OUTDIR"
: > $D/concat.txt; for f in "${SEGS[@]}"; do printf "file '%s'\n" "$PWD/$f" >> $D/concat.txt; done
ffmpeg -v error -y -f concat -safe 0 -i $D/concat.txt -c:v libx264 -crf 16 -preset medium -pix_fmt yuv420p -r 24 \
  -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2" \
  -c:a aac -b:a 160k $D/draft_raw_$TAG.mp4
ffmpeg -v error -y -i $D/draft_raw_$TAG.mp4 -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -movflags +faststart \
  -c:a copy $D/draft_$TAG.mp4
LEN=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $D/draft_$TAG.mp4)
SEC=$(printf '%.0f' "$LEN")
cp $D/draft_$TAG.mp4 "$OUTDIR/draft-$TAG-${SEC}s.mp4"
ffmpeg -v error -y -i $D/draft_$TAG.mp4 -vf "select=not(mod(n\,48)),scale=320:-1,tile=6x4" -frames:v 1 "$OUTDIR/draft-$TAG-contact.jpg"
echo "draft: $OUTDIR/draft-$TAG-${SEC}s.mp4  (${LEN}s, ${#SEGS[@]} segments)"
