# Compact offline runtime

`runtime.tar.xz` contains ordinary vendored files, not a submodule or network loader. `bootstrap.py` extracts it into disposable `test/scratch/runtime-slim`. The supported host is Linux x86_64, Python 3.12, glibc 2.38 or later, with system libz. The runtime was tested in the assignment environment. It needs no package downloads.

- Pillow 12.3.0: Python modules, core/font extensions, required shared libraries, distribution metadata and licenses. Unused AVIF, WebP, color-management and Tk extensions and their exclusive libraries are omitted.
- FFmpeg/FFprobe 7.0.2: small local builds with x264 snapshot 20191217-2245-stable. GPL license texts are in `bin/`. Upstream source: https://ffmpeg.org/releases/ffmpeg-7.0.2.tar.xz and https://download.videolan.org/pub/videolan/x264/snapshots/x264-snapshot-20191217-2245-stable.tar.bz2 .
- DejaVu fonts and license are in `fonts/`. Fonts are subset to ASCII and the punctuation/arrows/stars used by this film.

FFmpeg build: `--disable-everything --disable-autodetect --disable-doc --disable-debug --disable-network --disable-x86asm --enable-gpl --enable-libx264 --enable-small --enable-ffmpeg --enable-ffprobe --enable-protocol=file,pipe,fd --enable-demuxer=mov,rawvideo,mp3,flac,wav --enable-muxer=mp4,ipod,null,flac,wav,f32le --enable-decoder=h264,aac,mp3,mp3float,flac,pcm_s16le,pcm_f32le,rawvideo --enable-encoder=libx264,aac,flac,pcm_s16le,pcm_f32le,wrapped_avframe --enable-parser=h264,aac,mpegaudio,flac --enable-filter=scale,format,aresample,aformat,anull,null,volumedetect,atempo --enable-swscale --enable-swresample`. x264 was built with `--enable-static --enable-pic --disable-cli --disable-asm`.

The previous large runtime included NumPy, an online TTS client, HTTP dependencies, and general-purpose static FFmpeg builds. Those are no longer required: the renderer reads the original deterministic star coordinates from `stars.json`, narration recordings are retained, and optional score resynthesis uses Python's standard library. Compiler sources and temporary build products live only in scratch and are not runtime dependencies.
