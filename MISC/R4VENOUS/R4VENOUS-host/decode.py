#!/usr/bin/env python3
import argparse
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

# 1. Reverse the Argos-2 Mapping
ARGOS2_MAP = {
    'A': ('2','1'), 'B': ('2','2'), 'C': ('2','3'),
    'D': ('3','1'), 'E': ('3','2'), 'F': ('3','3'),
    'G': ('4','1'), 'H': ('4','2'), 'I': ('4','3'),
    'J': ('5','1'), 'K': ('5','2'), 'L': ('5','3'),
    'M': ('6','1'), 'N': ('6','2'), 'O': ('6','3'),
    'P': ('7','1'), 'Q': ('7','2'), 'R': ('7','3'), 'S': ('7','4'),
    'T': ('8','1'), 'U': ('8','2'), 'V': ('8','3'),
    'W': ('9','1'), 'X': ('9','2'), 'Y': ('9','3'), 'Z': ('9','4'),
    '0': ('0',), '1': ('1',), '2': ('2',), '3': ('3',),
    '4': ('4',), '5': ('5',), '6': ('6',), '7': ('7',),
    '8': ('8',), '9': ('9',),
    '{': ('A',), '}': ('B',), '_': ('C',)
}
REVERSE_MAP = {v: k for k, v in ARGOS2_MAP.items()}

# DTMF frequencies
L_FREQS = [697, 770, 852, 941]
H_FREQS = [1209, 1336, 1477, 1633]
KEYS = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]

def butter_bandpass(lowcut, highcut, fs, order=3):
    nyq = fs / 2
    return butter(order, [lowcut / nyq, highcut / nyq], btype='band')

def goertzel(samples, target_freq, sample_rate):
    window_size = len(samples)
    k = int(0.5 + (window_size * target_freq) / sample_rate)
    w = (2 * np.pi / window_size) * k
    coeff = 2 * np.cos(w)
    q1, q2 = 0, 0
    for x in samples:
        q0 = coeff * q1 - q2 + x
        q2, q1 = q1, q0
    return q1**2 + q2**2 - q1 * q2 * coeff

def decode_flag(filepath):
    fs, data = wavfile.read(filepath)
    
    # Convert to float and normalize
    data = data.astype(np.float32) / 32768.0 
    
    # 2. Bandpass Filter (matches the generator's 300-3400Hz limits)
    b, a = butter_bandpass(300, 3400, fs)
    filtered = lfilter(b, a, data)
    
    # 3. Envelope Detection to find tones and measure silences
    # Smooth the amplitude envelope to ignore crackles and minor noise
    envelope = np.abs(filtered)
    window = np.ones(int(fs * 0.02)) / int(fs * 0.02) # 20ms smoothing window
    smoothed = np.convolve(envelope, window, mode='same')
    
    # A threshold of 0.08 easily ignores the 0.04 pink noise
    active = smoothed > 0.08 
    
    # Find start and end indices of active tone regions
    edges = np.diff(active.astype(int))
    starts = np.where(edges == 1)[0]
    ends = np.where(edges == -1)[0]
    
    # Edge case: if audio starts/ends mid-tone
    if active[0]: starts = np.insert(starts, 0, 0)
    if active[-1]: ends = np.append(ends, len(active)-1)
    
    # 4. Extract Tones
    detected_tones = []
    min_len = int(fs * 0.05) # Ignore anything < 50ms (removes the short crackles)
    
    for s, e in zip(starts, ends):
        if (e - s) > min_len:
            # Grab the middle 50% of the tone to avoid fade-in/fade-out artifacts
            mid_s = s + (e - s) // 4
            mid_e = e - (e - s) // 4
            chunk = filtered[mid_s:mid_e]
            
            l_p = [goertzel(chunk, f, fs) for f in L_FREQS]
            h_p = [goertzel(chunk, f, fs) for f in H_FREQS]
            
            key = KEYS[np.argmax(l_p)][np.argmax(h_p)]
            detected_tones.append({'key': key, 'start': s, 'end': e})

    # 5. Group tones based on silence duration
    # Generator uses ~60ms between sequence tones, and ~140ms between characters
    groups = []
    current_group = []
    
    for i, tone in enumerate(detected_tones):
        if i == 0:
            current_group.append(tone['key'])
        else:
            gap_seconds = (tone['start'] - detected_tones[i-1]['end']) / fs
            # 100ms threshold neatly separates the 60ms gap from the 140ms gap
            if gap_seconds < 0.10: 
                current_group.append(tone['key'])
            else:
                groups.append(tuple(current_group))
                current_group = [tone['key']]
                
    if current_group:
        groups.append(tuple(current_group))

    # 6. Map back to flag
    flag = ""
    for group in groups:
        if group in REVERSE_MAP:
            flag += REVERSE_MAP[group]
        else:
            flag += "?" # Unknown sequence

    return flag

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NSC CTF — DTMF Flag Decoder")
    parser.add_argument("--input", default="input.wav", help="Input .wav filename")
    args = parser.parse_args()
    
    print(f"Analyzing: {args.input}...")
    decoded = decode_flag(args.input)
    print(f"\n[+] Extracted Flag: {decoded}\n")