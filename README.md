# IMD — From Pet to Possibility

**Video: [artifacts/video.mp4](artifacts/video.mp4)** (`video/mp4`). A 90-second narrated motion-comic origin film, from a dramatic keyboard opening and Fren Pet's early game world to a fictional cyborg Pepe escape, agent swarm, published projects and cosmic market-swallowing finale.

## Delivery

- Duration: **90.000 seconds**, 2,160 frames at 24 fps.
- Dimensions: **1280 × 720**, landscape 16:9.
- Video: **H.264**, `yuv420p`, MP4 with the `moov` atom before media data for browser streaming.
- Audio: **AAC stereo, 48 kHz, 160 kb/s**; English synthetic narration, original procedural synth music, keyboard/UI/impact/glass effects. Encoded size: **15,015,013 bytes (14.32 MiB)**. FFmpeg volume detection: mean **−22.4 dBFS**, peak **−4.8 dBFS**. Full results are in [verification.json](artifacts/verification.json).
- Captions: burned into the film, with [SRT sidecar](artifacts/captions.srt). Caption timing is estimated by sentence word count within each fitted narration clip, not forced alignment.
- [Contact sheet](artifacts/contact-sheet.jpg), [research and sources](production/SOURCES.md), [artwork and sound provenance](production/ARTWORK.md), and [scene script](production/scenes.json) accompany the video.

## Editorial and visual limitations

The historical timeline is based on IMD's official token page and Fren Pet documentation. The film marks the robot, AI hats, lab, cyborgs, orchestrator, escape, network takeover and market consumption as fictional imagery. Solana is labeled a vision; the sources confirm token connectivity for Base, Ethereum and Robinhood. No top-chain ranking, investment outcome or guaranteed 24/7 worker availability is asserted. The 2,000 identity seats are real according to the official source; the art shows representative crowds, not 2,000 individually rendered figures.

This is a **motion comic with animated overlays and camera movement**, not fully articulated character animation. The video prediction service timed out, so no generated video footage from that service is included. The opening is a photorealistic generated still animated with camera jitter, key glows, terminal text and typing audio, rather than a filmed person. Growing artwork is conveyed by egg-to-pet cuts, camera enlargement, color/style evolution and animated illustrative game statistics. The source storyboard panels are smaller than the final frame and have been upscaled. Some action beats use tableau images. Project panels are labeled stylized previews of published repositories, not live screenshots.

## Local checks

`production/check.py` reads the **actual MP4**, checks codecs, pixel format, dimensions, frame rate, exact frame count, duration, stereo sample rate, file size, MP4 atom order, and decodes the full video/audio without reported errors. It saves the result and SHA-256 in `artifacts/verification.json`. Frames from the encoded video were also inspected for layout and readable text. These are local checks, not independent certification.

## Offline reproduction

The delivered MP4 needs only a compatible player. Editable scenes, compressed artwork, narration recordings, a compressed mixed soundtrack, subset fonts and the compact offline runtime are included. See [runtime contents and platform requirements](production/DEPENDENCIES.md).

From the repository root:

```sh
python3 production/render.py --preview
python3 production/render.py --output test/scratch/rebuilt.mp4
python3 production/check.py
```

Omit `--output` to rebuild `artifacts/video.mp4`. The renderer extracts its bundled dependencies automatically; it does not fetch anything. Optional `python3 production/audio.py` resynthesizes the score and mixes the included narration using the standard library. This changes the noise sequence from the original NumPy score and overwrites the editable soundtrack and timing data. New spoken text requires new recordings; no online voice client is bundled.

## Bundle-size repair

The original finished MP4 was preserved byte for byte. The 59 MB general-purpose runtime was replaced by a compact runtime containing the capabilities actually used. Editable artwork is now JPEG, the mixed source soundtrack is AAC, and fonts are subset to this film's characters. These lossy source conversions affect future rebuilds, not the delivered video. Rebuilds are therefore visually comparable rather than byte-identical. Original voice clips, story, sources, provenance, timing and rendering logic are retained. Temporary compiler files and caches are confined to `test/scratch/`, which is excluded from submission.

The source package is checked separately against the 8 MiB limit; the required video remains a separate named output, untracked for the delivery daemon.

Repair checks passed: a fresh offline 2,160-frame rebuild, full decode and format checks on both exports, and optional standard-library audio resynthesis. The scratch rebuild is not substituted for the original named video. [Repair results](artifacts/repair-verification.json) and [bundle size](artifacts/bundle-verification.json) record these local checks. Run `python3 production/check_bundle.py` to repeat the size check.
