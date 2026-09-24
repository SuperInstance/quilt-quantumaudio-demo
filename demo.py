"""
quilt-quantumaudio-demo: minimal round-trip.

Build audio → encode as quantum circuit → execute → decode → compare.
"""
import numpy as np

try:
    import quantumaudio
except ImportError:
    print("quantumaudio not installed. Run:")
    print("  pip install quantumaudio --index-url https://pypi.org/simple/")
    raise


def main():
    # 1. Build audio: 440 Hz sine, 10 ms, 16-bit equivalent
    sr = 44100
    duration = 0.01
    samples = int(sr * duration)
    t = np.linspace(0, duration, samples, endpoint=False)
    audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    print(f"Original: {len(audio)} samples, range [{audio.min():.3f}, {audio.max():.3f}]")

    # 2. Encode as quantum circuit (QPAM scheme)
    print("\nEncoding as QPAM circuit...")
    circuit = quantumaudio.encode(audio, scheme="qpam")
    print(f"  circuit: {circuit.num_qubits} qubits, depth {circuit.depth()}")

    # 3. Run on simulator and decode
    print("\nDecoding (20000 shots on AerSimulator)...")
    decoded = quantumaudio.decode(circuit, shots=20000)
    print(f"  decoded: {len(decoded)} samples, range [{decoded.min():.3f}, {decoded.max():.3f}]")

    # 4. Compare
    pearson = np.corrcoef(audio, decoded[: len(audio)])[0, 1]
    mse = np.mean((decoded[: len(audio)] - audio) ** 2)
    print(f"\nReconstruction quality:")
    print(f"  Pearson correlation: {pearson:.4f}")
    print(f"  MSE:                 {mse:.4f}")

    # 5. The canary: hash the audio + decoded
    import hashlib
    orig_hash = hashlib.sha256(audio.tobytes()).hexdigest()[:16]
    deco_hash = hashlib.sha256(decoded.tobytes()).hexdigest()[:16]
    print(f"\nCanary hashes (witness the encoding):")
    print(f"  original:  {orig_hash}")
    print(f"  quantum:   {deco_hash}")
    print(f"  (they differ — quantum encoding is lossy, but reproducible)")

    print(f"\n=== DEMO COMPLETE ===")


if __name__ == "__main__":
    main()
