from flask import Flask, request
import numpy as np
import librosa
import scipy.signal as sig

app = Flask(__name__)

SAMPLE_RATE = 44100
VAD_RMS_TH = 0.010
TH_FLUX_MIN = 0.0003
TH_PERIODICITY = 0.40
ENVE_FS = 1000

def compute_rms(x):
    return np.sqrt(np.mean(x**2))

def spectral_flux_mean(x):
    N_FFT = 512
    HOP = 128
    stft = np.abs(librosa.stft(x, n_fft=N_FFT, hop_length=HOP, window='hamming'))**2
    diff = np.diff(stft, axis=1)
    diff[diff < 0] = 0
    return np.mean(np.mean(diff, axis=0))

def detect_trill_R(x):
    e = np.zeros_like(x)
    alpha = 0.99
    for i in range(1, len(x)):
        e[i] = alpha * e[i-1] + (1-alpha)*abs(x[i])
    step = int(SAMPLE_RATE / ENVE_FS)
    env_ds = e[::step]
    env_ds /= (np.max(env_ds)+1e-9)
    lag_min = int(ENVE_FS*0.005)
    lag_max = int(ENVE_FS*0.015)
    env_ds -= np.mean(env_ds)
    r = np.correlate(env_ds, env_ds, mode='full')
    r = r[len(r)//2:]
    r /= (np.max(r)+1e-9)
    per_idx = np.max(r[lag_min:lag_max])
    peaks, _ = sig.find_peaks(env_ds, height=0.5)
    num_peaks = len(peaks)
    is_trill = per_idx >= TH_PERIODICITY and 2 <= num_peaks <= 5
    return is_trill, per_idx, num_peaks

@app.route("/audio", methods=["POST"])
def process_audio():
    raw = request.data
    data = np.frombuffer(raw, dtype=np.float32)
    if len(data)==0:
        return "0"
    data /= (np.max(np.abs(data))+1e-9)
    rms = compute_rms(data)
    if rms < VAD_RMS_TH:
        return "0"
    flux = spectral_flux_mean(data)
    is_trill, per_idx, num_peaks = detect_trill_R(data)
    r_detected = is_trill and flux >= TH_FLUX_MIN
    print(f"RMS={rms:.3f} | Flux={flux:.6f} | Per={per_idx:.3f} | Peaks={num_peaks} | R={r_detected}")
    return "1" if r_detected else "0"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

