# Execution

`agc_engine.c` and `agc_engine_init.c`: 2,560,000 machine cycles, 30 simulated seconds. Keyboard input uses channel 015 and KEYRUPT.

| Time (s) | Input or event |
|---|---|
| 3.0–4.2 | `V36E` |
| 8.0 | Fixture load |
| 8.0–10.4 | `V37E63E` |
| 10.451 | `P63LM`, address `32,2776` |
| 11.251 | `1406POO`, address `31,3733` |
| 15.0–17.4 | `V05N09E` |

[Recorded counts](../results/bench/summary.json): 1,547,922 native instructions; 16 native instructions and 22 interpretive pair fetches in the P63 entry region; 35 interpretive pair fetches in the guidance bank.

The trace records native instructions throughout P63 and the guidance bank; elsewhere it samples every thousandth native instruction. Coverage counters count all native instructions. Interpretive pairs are recorded at `NEWOPS` using `LOC` and `BANKSET`.

## Fixture

Loaded once at eight seconds after fresh start. [Memory writes](../results/bench/fixture-writes.csv).

| Item | Fixture value | Representation |
|---|---|---|
| Reference readiness | Set `REFSMBIT` in `FLAGWRD3` | Bit `010000` at erasable `0077` |
| `REFSMMAT` | Identity reference frame | Nine double-precision components, diagonal 0.5, B−1 scaling |
| `RLS` | `(1,737,400, 0, 0)` m | Moon-fixed landing-site vector, B−27 |
| `RN` | `(1,752,400, 0, 0)` m | Hypothetical position, B−27 |
| `VN` | `(0, 1,700, 0)` m/s | Stored in m/centisecond, B−7 |
| `PIPTIME` | 8 s | Centiseconds, B−28 |
| `TLAND` | 900 s | Centiseconds, B−28 |

Addresses and scaling follow the pinned listing. The fixture omits the complete mission pad load, lunar ephemeris, calibrated IMU, radar and spacecraft dynamics. It does not establish a physically consistent descent.

## Controls

| Case | Recorded result |
|---|---|
| Initialized | P63 execution; alarm 01406 |
| Cold | No fixture writes; readiness check reached; no P63 interpretive execution |
| Uninstrumented | DSKY-channel output identical to initialized case |

The tracing callback reads state after timing and interrupt decisions, before execution. [Noninterference result](../results/noninterference.json).

The assembler reports a nonfatal bank-boundary warning. The assembled rope matches the reference binary byte for byte.
