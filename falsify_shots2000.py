"""Honest-falsification bench for quilt-quantumaudio-demo issue #1.

Measures the decode-vs-original pearson envelope for the shipped text_to_audio
pipeline (882 samples) vs a downsampled variant (<=64 samples), at several
shot counts. Every number survives a second run here (mean over N runs).
"""
import hashlib
import numpy as np
import quantumaudio

from quilt_integration import text_to_audio

REPS = 2  # meta-rule: every recorded number must survive a second run


def run(text, shots, samples):
    audio = text_to_audio(text)
    if samples:
        idx = np.linspace(0, len(audio) - 1, samples).round().astype(int)
        audio = audio[idx]
    circuit = quantumaudio.encode(audio, scheme="qpam")
    decoded = quantumaudio.decode(circuit, shots=shots)
    n = min(len(audio), len(decoded))
    p = float(np.corrcoef(audio[:n], decoded[:n])[0, 1])
    h = hashlib.sha256(decoded.tobytes()).hexdigest()[:16]
    return p, h


def envelope(text, shots, samples):
    ps, hs = [], set()
    for _ in range(REPS):
        p, h = run(text, shots, samples)
        ps.append(p)
        hs.add(h)
    return float(np.mean(ps)), min(ps), max(ps), len(hs)


print(f"reps per cell = {REPS}\n")
print(f"{'audio_len':>9s} {'shots':>7s} {'pearson_mean':>13s} {'pearson_min':>12s} {'pearson_max':>12s} {'distinct_hashes':>16s}")
print("-" * 75)
for samples in (None, 64):
    for shots in (2000, 20000, 100000):
        m, lo, hi, nd = envelope("hello world", shots, samples)
        lab = "882 (shipped)" if samples is None else str(samples)
        print(f"{lab:>9s} {shots:>7d} {m:>13.4f} {lo:>12.4f} {hi:>12.4f} {nd:>16d}")
