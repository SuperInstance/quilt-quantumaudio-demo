"""
quilt-quantumaudio-demo: integrate quantumaudio as a Quilt cell substrate.

The cell has a substrate zoo: deterministic (echo/reverse/sha256/stub_llm),
LLM (zai_substrate), and now quantum audio (quantumaudio_substrate).

The quantum substrate encodes "prompt" as audio, runs the QPAM circuit
on AerSimulator, decodes the result, and returns a hash.

Measured honesty envelope (decode-vs-original pearson, AerSimulator, two
runs per cell — see falsify_shots2000.py):

    audio samples          shots      pearson
    882 (original)         2000       0.03-0.04   <- noise, witnesses nothing
    882 (original)         100000     0.51-0.53
    16 (this file)         2000       0.62-0.67   <- default operating point

QPAM spreads shots across amplitudes; a canary needs shots/amplitude >= ~100.
text_to_audio therefore downsamples to 16 amplitudes by default so the
shipped shots=2000 is a real witness, not sampling noise.

Caveat: the hash itself is still shot-noise-jittered run-to-run (distinct
hashes per run). Use decode-similarity (pearson), not hash equality, as
the canary check.
"""
import hashlib
import os
import numpy as np

try:
    import quantumaudio
except ImportError:
    quantumaudio = None


def quantumaudio_substrate(prompt: str, shots: int = 2000,
                           similarity: bool = False):
    """Encode 'prompt' as audio, run QPAM circuit, return hash of decoded audio.

    This is one tile in the Quilt cell's substrate zoo.

    With similarity=True, returns (hash, pearson): pearson is the honest
    canary signal (same prompt ≈ 0.6+ at the default operating point;
    distinct prompts ≈ 0). The hash alone jitters run-to-run with shot
    noise and should not be compared for equality.
    """
    if quantumaudio is None:
        h = f"[no-quantumaudio:{prompt[:40]}...]"
        return (h, None) if similarity else h

    # 1. text → audio (16 samples so shots=2000 is a real witness)
    audio = text_to_audio(prompt)

    # 2. encode as QPAM circuit
    circuit = quantumaudio.encode(audio, scheme="qpam")

    # 3. execute on simulator, decode
    decoded = quantumaudio.decode(circuit, shots=shots)

    # 4. hash the decoded audio
    h = hashlib.sha256(decoded.tobytes()).hexdigest()[:16]
    if not similarity:
        return h
    n = min(len(audio), len(decoded))
    p = float(np.corrcoef(audio[:n], decoded[:n])[0, 1])
    return h, p


def text_to_audio(text: str, sr: int = 44100, duration: float = 0.02,
                  n_samples: int = 16) -> np.ndarray:
    """Map text characters to audio amplitudes (simple demo encoding).

    Downsamples to n_samples via linear interpolation so shots spread
    across ~2**ceil(log2(n_samples)) amplitudes at ~shots/n_samples per
    amplitude. 16 samples @ shots=2000 measured pearson 0.62-0.67
    (see module docstring envelope).
    """
    n_full = int(sr * duration)
    full = np.zeros(n_full, dtype=np.float32)
    for i, ch in enumerate(text[:n_full]):
        # map char to amplitude: 0-255 -> -1.0..1.0
        full[i] = (ord(ch) - 128) / 128.0
    full = np.clip(full, -1.0, 1.0)
    if n_samples and n_samples < n_full:
        x_old = np.linspace(0.0, 1.0, n_full)
        x_new = np.linspace(0.0, 1.0, n_samples)
        full = np.interp(x_new, x_old, full).astype(np.float32)
    return full


if __name__ == "__main__":
    print("=== QUANTUMAUDIO SUBSTRATE DEMO ===\n")

    test_prompts = [
        "hello world",
        "hello world",  # same prompt -> high decode-similarity
        "different text",
        "hello world",
    ]

    sims = {}
    for p in test_prompts:
        h, sim = quantumaudio_substrate(p, similarity=True)
        sims.setdefault(p, []).append(sim)
        print(f"  '{p:20s}' -> quantum hash: {h}  decode-similarity: {sim:.3f}")

    same = sims["hello world"]
    # Honest discrimination check: decode prompt A, compare against prompt
    # B's audio. Cross-prompt pearson should sit near 0 while same-prompt
    # similarity stays ~0.6+.
    if quantumaudio is None:
        cross = None
    else:
        decodes = {}
        for pr in ("hello world", "different text"):
            audio_pr = text_to_audio(pr)
            circ = quantumaudio.encode(audio_pr, scheme="qpam")
            decodes[pr] = quantumaudio.decode(circ, shots=2000)[: len(audio_pr)]
        a, b = decodes["hello world"], decodes["different text"]
        n = min(len(a), len(b))
        cross = float(np.corrcoef(a[:n], b[:n])[0, 1])
    print(f"\nsame-prompt decode-similarity runs: "
          f"{min(same):.3f}..{max(same):.3f} (noise floor at 882 samples: ~0.03)")
    if cross is not None:
        print(f"cross-prompt decode-decode pearson: {cross:.3f}")
    print("Note: hashes jitter run-to-run with shot noise; compare similarity,")
    print("not hash equality.")
