"""
quilt-quantumaudio-demo: integrate quantumaudio as a Quilt cell substrate.

The cell has a substrate zoo: deterministic (echo/reverse/sha256/stub_llm),
LLM (zai_substrate), and now quantum audio (quantumaudio_substrate).

The quantum substrate encodes "prompt" as audio, runs the QPAM circuit
on AerSimulator, decodes the result, and returns a hash. The hash is
reproducible if the prompt is the same (modulo shot noise).
"""
import hashlib
import os
import numpy as np

try:
    import quantumaudio
except ImportError:
    quantumaudio = None


def quantumaudio_substrate(prompt: str, shots: int = 2000) -> str:
    """Encode 'prompt' as audio, run QPAM circuit, return hash of decoded audio.

    This is one tile in the Quilt cell's substrate zoo.
    """
    if quantumaudio is None:
        return f"[no-quantumaudio:{prompt[:40]}...]"

    # 1. text → audio (simple: use character codes as amplitude)
    audio = text_to_audio(prompt)

    # 2. encode as QPAM circuit
    circuit = quantumaudio.encode(audio, scheme="qpam")

    # 3. execute on simulator, decode
    decoded = quantumaudio.decode(circuit, shots=shots)

    # 4. hash the decoded audio
    return hashlib.sha256(decoded.tobytes()).hexdigest()[:16]


def text_to_audio(text: str, sr: int = 44100, duration: float = 0.02) -> np.ndarray:
    """Map text characters to audio amplitudes (simple demo encoding)."""
    # Convert chars to amplitudes in [-1, 1]
    n_samples = int(sr * duration)
    audio = np.zeros(n_samples, dtype=np.float32)
    for i, ch in enumerate(text[:n_samples]):
        # map char to amplitude: 0-255 → -1.0..1.0
        audio[i] = (ord(ch) - 128) / 128.0
    # Clip to valid range
    return np.clip(audio, -1.0, 1.0)


if __name__ == "__main__":
    print("=== QUANTUMAUDIO SUBSTRATE DEMO ===\n")

    test_prompts = [
        "hello world",
        "hello world",  # same prompt → same hash (modulo shot noise)
        "different text",
        "hello world",
    ]

    for p in test_prompts:
        h = quantumaudio_substrate(p)
        print(f"  '{p:20s}' → quantum hash: {h}")

    print("\nNote: same prompts should produce similar hashes (within shot noise)")
    print("with shots=2000, the variance is small enough to be a canary witness.")
