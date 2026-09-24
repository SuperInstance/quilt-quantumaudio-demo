# quilt-quantumaudio-demo

> Demo of MOTH `quantumaudio` (quantum audio encoding) integrated with Quilt cells.

## What is MOTH / quantumaudio?

`MOTH` is `Moth Quantum` (https://mothquantum.com), makers of
`quantumaudio`, an open-source Python package that maps digital
audio onto quantum circuits using Qiskit.

The package provides 5 encoding schemes:

| Scheme | Channels | qubits (10ms) | depth (10ms) | Speed |
|--------|----------|----------------|---------------|-------|
| QSM | 1 | 15 | 2384 | 113ms |
| MQSM | N | 16 | 3408 | 147ms |
| QPAM | 1 | 9 | 2 | 2ms ⚡ |
| MSQPAM | N | 11 | 3072 | 1821ms |
| SQPAM | 1 | 10 | 1536 | 960ms |

**QPAM is the most compact** (depth-2 circuit, just 9 qubits for 10ms).
It encodes each audio sample's value as a *quantum probability
amplitude* over time bins.

## The 30-second demo

```bash
pip install quantumaudio --index-url https://pypi.org/simple/
python3 demo.py
```

This will:
1. Build a 440 Hz sine wave (10 ms)
2. Encode it with QPAM (9-qubit depth-2 circuit)
3. Run the circuit on `AerSimulator` (20000 shots)
4. Decode → reconstructed audio
5. Print Pearson correlation (typically 0.98+)

## Why this matters for Quilt

This is a **substrate** — quantum audio is one tile in the cell's
substrate zoo. Just like `zai_substrate` (LLM), `echo_substrate`
(deterministic), or `sha256_substrate` (cryptographic), a
`quantumaudio_substrate` could be plugged into the cell:

```python
def quantum_audio_substrate(prompt: str) -> str:
    """Encode 'prompt' as audio, run QPAM circuit, decode to hash."""
    audio = text_to_audio(prompt)
    circuit = quantumaudio.encode(audio, scheme='qpam')
    decoded = quantumaudio.decode(circuit, shots=20000)
    return hashlib.sha256(decoded.tobytes()).hexdigest()[:16]
```

This makes the cell capable of **quantum-receipt hashes**:
the audio's content is encoded as a quantum state, and any
tampering with the circuit changes the decoded hash. A canary
that uses quantum audio as its substrate would be tamper-evident
at a level classical substrates can't match.

## Files

- `README.md` — this file
- `demo.py` — minimal round-trip demo
- `bench.py` — compare 5 schemes on same audio
- `quilt_integration.py` — how to wire quantumaudio as a Quilt cell substrate

## API key

`MOTH_API_KEY` is not required for this demo — the package is
fully open-source and runs locally. The API key would be for a
hosted API that's currently 503 (the moth.ai and mothquantum.com
hosted APIs are down). The local package works fine.

## Gotchas (re-confirmed)

- `quantumaudio` data must be in range `[-1.0, 1.0]` (use `np.clip`)
- `quantumaudio.encode()` returns a circuit (Qiskit)
- `quantumaudio.decode(circuit, shots=N)` runs on AerSimulator by default
- QPAM needs `shots` metadata for decoding (stored in circuit.metadata)
- Reconstructed audio quality scales with shots: 2000 shots ≈ noisy,
  20000 shots ≈ 0.98 Pearson correlation
- Multi-channel audio shape must be `(N_channels, N_samples)` for MQSM/MSQPAM
