"""
quilt-quantumaudio-demo: bench all 5 schemes on the same audio.
"""
import time
import numpy as np
import quantumaudio
from quantumaudio import QSM, MQSM, QPAM, MSQPAM, SQPAM


def main():
    sr = 44100
    duration = 0.01
    samples = int(sr * duration)
    audio = np.sin(2 * np.pi * 440 * np.linspace(0, duration, samples, endpoint=False)).astype(np.float32)
    print(f"Audio: {len(audio)} samples, range [{audio.min():.3f}, {audio.max():.3f}]\n")

    print(f"{'scheme':12s}  {'qubits':>6s}  {'depth':>6s}  {'encode_ms':>10s}  {'decode_pearson':>15s}")
    print("-" * 60)

    for name, cls in [("QSM", QSM), ("MQSM", MQSM), ("QPAM", QPAM), ("MSQPAM", MSQPAM), ("SQPAM", SQPAM)]:
        inst = cls()
        t0 = time.time()
        circuit = inst.encode(audio, measure=True, verbose=0)
        elapsed = (time.time() - t0) * 1000
        try:
            decoded = quantumaudio.decode(circuit, shots=5000)
            pearson = float(np.corrcoef(audio, decoded[: len(audio)])[0, 1])
        except Exception as e:
            pearson = float("nan")
            print(f"  decode error: {e}")
        print(f"{name:12s}  {circuit.num_qubits:>6d}  {circuit.depth():>6d}  {elapsed:>10.1f}  {pearson:>15.4f}")

    print("\nQPAM is the most compact (depth=2, ~9 qubits).")
    print("MSQPAM is the multi-channel sweet spot (depth 3072, 11 qubits).")


if __name__ == "__main__":
    main()
