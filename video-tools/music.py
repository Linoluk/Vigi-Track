"""Original upbeat background track for the Vigi-Track demo, generated from code (no samples, royalty free).
Usage: python3 music.py SECONDS OUT.wav"""
import numpy as np, wave, sys

SR = 44100
BPM = 112
BEAT = 60 / BPM
BAR = 4 * BEAT
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 200.0
OUT = sys.argv[2] if len(sys.argv) > 2 else "music.wav"
N = int(DUR * SR) + SR * 4
L = np.zeros(N); R = np.zeros(N); SC = np.ones(N)
rng = np.random.default_rng(11)

def hz(m): return 440 * 2 ** ((m - 69) / 12)
# F  C  Am  G  (one bar each), bright and positive
PROG = [(53, [57, 60, 64, 65]), (48, [55, 60, 64, 67]), (57, [57, 60, 64, 69]), (55, [55, 59, 62, 67])]

def add(buf, start, sig, gain=1.0):
    i = int(start * SR)
    if i >= N or i < 0: return
    j = min(N, i + len(sig)); buf[i:j] += sig[: j - i] * gain

def env(n, a, r):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e

def pad(notes, dur):
    n = int(dur * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for m in notes:
        f = hz(m + 12)
        for det in (-0.1, 0.1):
            ff = f * 2 ** (det / 12)
            ph = (ff * t) % 1.0
            s += (2 * ph - 1) * 0.35 + np.sin(2 * np.pi * ff * t) * 0.6   # soft saw + sine
    # gentle low-pass by moving average
    k = 18; s = np.convolve(s, np.ones(k) / k, mode="same")
    return s * env(n, 0.25, 0.4) / (len(notes) * 2)

def pluck(m, dur=0.5):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(4 * np.pi * f * t) + 0.2 * np.sin(6 * np.pi * f * t)
    return s * np.exp(-t * 9) * np.minimum(1, t * 600)

def bass(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m - 12)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * env(n, 0.01, 0.08)

def kick():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 48 + 110 * np.exp(-t * 35)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)

def noise(dur, decay, hp=True):
    n = int(dur * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n)
    if hp: x = np.diff(np.concatenate([[0], x]))
    return x * np.exp(-t * decay)

def clap():
    s = np.zeros(int(0.25 * SR))
    for o in (0, 0.012, 0.024):
        b = noise(0.2, 22); i = int(o * SR); s[i:i + len(b)] += b[: len(s) - i]
    return s * 0.5

bars = int(DUR / BAR) + 1
intro_bars, outro_bars = 4, 4
for b in range(bars):
    t0 = b * BAR
    root, chord = PROG[b % 4]
    break_ = (bars * 0.42) <= b < (bars * 0.42 + 4)      # short breakdown in the middle
    full = intro_bars <= b < bars - outro_bars and not break_
    p = pad(chord, BAR + 0.3); add(L, t0, p, 0.42); add(R, t0, p, 0.42)
    # arpeggio, 16th notes
    if b >= 2 and b < bars - 2:
        seq = [chord[0], chord[2], chord[1], chord[3], chord[2] + 12, chord[1], chord[3], chord[2]]
        for k in range(16):
            m = seq[k % 8] + 12
            g = 0.10 if not full else 0.13
            pan = 0.5 + 0.3 * np.sin(k * 0.9)
            s = pluck(m); add(L, t0 + k * BEAT / 4, s, g * (1 - pan) * 2); add(R, t0 + k * BEAT / 4, s, g * pan * 2)
    if full or break_:
        for k in range(8):   # offbeat-ish bass in 8ths
            add(L, t0 + k * BEAT / 2, bass(root, BEAT / 2 * 0.9), 0.12 if full else 0.06)
            add(R, t0 + k * BEAT / 2, bass(root, BEAT / 2 * 0.9), 0.12 if full else 0.06)
    if full:
        for k in range(4):
            kk = kick(); add(L, t0 + k * BEAT, kk, 0.36); add(R, t0 + k * BEAT, kk, 0.36)
            i = int((t0 + k * BEAT) * SR); w = int(0.22 * SR)
            if i + w < N: SC[i:i + w] = np.minimum(SC[i:i + w], 0.45 + 0.55 * np.linspace(0, 1, w) ** 1.5)
        for k in (1, 3):
            c = clap(); add(L, t0 + k * BEAT, c, 0.16); add(R, t0 + k * BEAT + 0.006, c, 0.16)
        for k in range(16):
            h = noise(0.05, 70) * (0.05 if k % 2 else 0.028)
            add(L, t0 + k * BEAT / 4, h, 0.9); add(R, t0 + k * BEAT / 4 + 0.003, h, 1.0)
    # riser into the drop after intro and after breakdown
    if b == intro_bars - 1 or (break_ and b == int(bars * 0.42 + 3)):
        n = int(BAR * SR); t = np.arange(n) / SR
        rs = rng.standard_normal(n) * (t / BAR) ** 2 * 0.12
        add(L, t0, rs); add(R, t0, rs)

L *= SC; R *= SC
def delay(x, sec, fb, mix):
    d = int(sec * SR); y = x.copy()
    for i in range(1, 4): y[d * i:] += x[: len(x) - d * i] * (fb ** i) * mix
    return y
L = delay(L, BEAT * 0.75, 0.35, 0.35); R = delay(R, BEAT * 0.5, 0.35, 0.35)
mix = np.stack([L, R], 1)[: int(DUR * SR)]
fi, fo = int(1.5 * SR), int(5 * SR)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
mix = np.tanh(mix / np.max(np.abs(mix)) * 1.3) * 0.9
with wave.open(OUT, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print(OUT, DUR)
