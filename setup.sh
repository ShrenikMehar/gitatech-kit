#!/bin/bash
# One-time setup for the Gita x Tech reel kit (Linux cloud container or macOS). Safe to re-run.
set -u
cd "$(dirname "$0")"
PIP="python3 -m pip install -q"
python3 -c "import skia" 2>/dev/null || $PIP skia-python 2>/dev/null || $PIP --break-system-packages skia-python
python3 -c "import soundfile" 2>/dev/null || $PIP soundfile 2>/dev/null || $PIP --break-system-packages soundfile
python3 -c "import kokoro_onnx" 2>/dev/null || $PIP kokoro-onnx 2>/dev/null || $PIP --break-system-packages kokoro-onnx 2>/dev/null || echo "note: kokoro-onnx (offline voice fallback) not installed"
python3 -c "import edge_tts" 2>/dev/null || $PIP edge-tts 2>/dev/null || $PIP --break-system-packages edge-tts
python3 -c "import PIL, numpy" 2>/dev/null || $PIP pillow numpy 2>/dev/null || $PIP --break-system-packages pillow numpy
command -v ffmpeg >/dev/null || echo "MISSING: ffmpeg (apt-get install -y ffmpeg / brew install ffmpeg)"
python3 - <<'PY'
from PIL import features
import skia
print("skia", skia.__version__, "| raqm (Devanagari shaping):", features.check("raqm"))
if not features.check('raqm'):
    print('WARNING: Pillow has no raqm -> Mac: brew install fribidi | Linux: apt-get install -y libraqm0. Without it Devanagari conjuncts break.')
PY
echo "All set. Voices use Microsoft neural voices (edge-tts, needs network). Offline fallback: Kokoro (model ~350 MB downloads on first use)."
