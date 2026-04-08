#!/bin/sh
# Auto-detect available VRAM and pull the best-fitting Gemma 4 variant.
#
#   <  9 GB  -> gemma4:2b      (mobile/edge tier)
#   < 14 GB  -> gemma4:9b
#   < 22 GB  -> gemma4:12b
#   >=22 GB  -> gemma4:26b     (full SOTA, MoE)
#
# Falls back to gemma4:9b if nvidia-smi is unavailable.
set -eu

VARIANT="gemma4:9b"

if command -v nvidia-smi >/dev/null 2>&1; then
    VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1 | tr -d ' ')
    VRAM_GB=$(( VRAM_MB / 1024 ))
    echo "[veritas] detected ${VRAM_GB} GB VRAM"
    if   [ "$VRAM_GB" -lt 9  ]; then VARIANT="gemma4:2b"
    elif [ "$VRAM_GB" -lt 14 ]; then VARIANT="gemma4:9b"
    elif [ "$VRAM_GB" -lt 22 ]; then VARIANT="gemma4:12b"
    else                              VARIANT="gemma4:26b"
    fi
else
    echo "[veritas] nvidia-smi not found — defaulting to ${VARIANT}"
fi

echo "[veritas] pulling ${VARIANT}"
ollama pull "$VARIANT"
echo "[veritas] ready: ${VARIANT}"
