# Hamilton

Assemble Luminary 099, execute its real P63 ignition logic, and watch the instruction trace beside a DSKY decoded from the emulator's output channels.

[Watch the 50-second demo](demo/hamilton.mp4) · [Execution trace](results/bench/trace.csv) · [Measured result](results/bench/summary.json)

![Real P63 execution and DSKY output](demo/execution.png)

The initialized test executes P63 and its guidance equations, then reports **01406**, a bad return from the time-to-go root solver. That failure is the actual result. This project does not simulate a completed landing.

## Run

Requires Python 3.12, Git, GCC, Make, FFmpeg (with ffprobe), and the DejaVu fonts at the Debian/Ubuntu `fonts-dejavu-core` paths under `/usr/share/fonts/truetype/dejavu/`. The simulation runs on a CPU and takes about a second for 30 simulated seconds in this environment.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch.py
python scripts/build.py
python scripts/run.py
python scripts/render_demo.py
python scripts/verify.py
```

The fetch is pinned to VirtualAGC commit `ebd8695d23bde6eb9f26933ddf244b8d18987f21`. Building uses the actual yaYUL assembler, converts the reference `Luminary099.binsource` with `oct2bin`, and compares both binary images. All **73,728 bytes match**. The built public-domain flight binary and its SHA-256 manifest are included in `results/`.

## What executes

The harness links the real `agc_engine.c` and `agc_engine_init.c`. It runs 2,560,000 machine cycles, corresponding to 30 seconds at 12/1,024,000 seconds per cycle. Keyboard inputs enter channel 015 with the real KEYRUPT interrupt. The sequence is:

| AGC time | Action |
|---|---|
| 3.0–4.2 s | `V36E`: flight-program fresh start |
| 8.0 s | Load the documented synthetic state fixture below |
| 8.0–10.4 s | `V37E63E`: request program 63 |
| 10.451 s | Enter `P63LM` at `32,2776` |
| 10.4–11.3 s | P63 initialization and real guidance computations |
| 15.0–17.4 s | `V05N09E`: ask the flight program to display alarm registers |

The recorded run executes **1,547,922 native instructions**. Within the P63 entry region it executes 16 native instructions and fetches 22 interpretive opcode pairs. The lunar guidance equations fetch another 35 interpretive pairs. These include `IGNALG`, the site transformation call, `GUIDINIT`, `LEMPREC`, gravity calculation, `?GUIDSUB`, `CALCRGVG`, and `TTF/8CL`. The native trace records the actual `1406POO` error exit; the DSKY subsequently shows verb 05, noun 09 and register 1 equal to `01406`.

The AGC's interpreter is itself flight software running on the emulated CPU. Its paired instructions are recorded at the real `NEWOPS` dispatcher using `LOC` and `BANKSET`; they are not reimplemented in Python. Native instructions in the P63 region and guidance bank are traced in full; elsewhere the native trace samples every thousandth instruction. Coverage counters count every native instruction.

## Initial conditions

This is a **synthetic software test fixture**, not recovered Apollo 11 telemetry. It is loaded once, at eight simulated seconds, after the actual fresh-start routine. The flight program is unchanged. `results/bench/fixture-writes.csv` records every inserted memory word.

| Item | Fixture value | Representation |
|---|---|---|
| Reference readiness | Set `REFSMBIT` in `FLAGWRD3` | Bit `010000` at erasable `0077` |
| `REFSMMAT` | Identity reference frame | Nine double-precision components, diagonal 0.5, B−1 scaling |
| `RLS` | `(1,737,400, 0, 0)` m | Moon-fixed landing-site vector, B−27 |
| `RN` | `(1,752,400, 0, 0)` m | Hypothetical position, B−27 |
| `VN` | `(0, 1,700, 0)` m/s | Stored in m/centisecond, B−7 |
| `PIPTIME` | 8 s | Centiseconds, B−28 |
| `TLAND` | 900 s | Centiseconds, B−28 |

The representation and addresses come from the pinned flight listing. This fixture supplies an aligned reference and nonzero trial vectors so P63 runs beyond its readiness check. It does not supply a complete mission pad load, lunar ephemeris, calibrated IMU, radar or spacecraft dynamics. These numbers do not establish a physically consistent descent. The guidance root failure is retained and displayed, rather than patched out or replaced with a scripted trajectory.

## Evidence and controls

`run.py` executes three cases:

- **Initialized bench:** the fixture above, genuine P63/guidance execution and 01406 output.
- **Cold control:** no fixture writes. P63 reaches its readiness check but does not reach its interpretive ignition logic.
- **Uninstrumented engine:** the same initialized case using the unchanged upstream CPU source. Its complete captured DSKY-channel stream is byte-identical to the instrumented run.

The tracing change consists only of a callback after instruction timing and interrupt decisions, before execution. It reads state and writes trace records. The passive-tracing control verifies that it does not change the captured output stream.

`verify.py` checks the reference binary digest, actual instruction and interpreter addresses, the 01406 branch, decoded program 63 and alarm display, the cold-start control, fixture audit, tracing noninterference and video format. The original assembler emits a nonfatal bank-boundary warning; the resulting rope still matches every reference byte.

## Demo

The video shows original listing text next to the relay-decoded DSKY. The 0.84-second computation interval is played at 0.04× speed so it can be read; the AGC timestamp remains visible. Pauses between logged source dispatches retain the last recorded source line. Indicator lamps, digit blanking and verb/noun flashing follow captured channel values. The custom panel is an explanatory rendering, not a photograph or exact mechanical replica of the hardware.

Every displayed digit comes from `results/bench/io.csv`. The renderer does not supply a landing altitude, velocity, target solution or success state. The final alarm is a useful demonstration of the limits of these initial conditions.

## Sources and licensing

- [VirtualAGC source](https://github.com/virtualagc/virtualagc) and [emulator documentation](https://www.ibiblio.org/apollo/yaAGC.html).
- [Luminary source history](https://www.ibiblio.org/apollo/Luminary.html), including the Apollo 11 listing's provenance.
- Pinned source files `THE_LUNAR_LANDING.agc`, `LUNAR_LANDING_GUIDANCE_EQUATIONS.agc`, `INTERPRETER.agc`, `ERASABLE_ASSIGNMENTS.agc` and `PLANETARY_INERTIAL_ORIENTATION.agc` supply addresses, logic and scaling conventions.
- The DSKY relay map and annunciators follow the upstream `yaDSKY2` implementation and `LM.ini`.

Original Hamilton code and graphics are MIT-licensed. VirtualAGC's emulator is GPL-2.0-or-later; its license and notice are preserved under `licenses/`, and combined emulator executables carry those terms. The original flight source is marked public domain upstream. The downloaded source and compiled emulator stay in ignored `vendor/` and `build/` directories. The project name acknowledges Margaret Hamilton; it does not attribute every routine to her or imply NASA endorsement.
