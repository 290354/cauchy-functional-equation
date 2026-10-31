"""把逐页旁白铺到时间轴上，生成整轨 WAV，再与视频合成。"""
import json
import os
import subprocess
import sys
import wave

import numpy as np
import imageio_ffmpeg

import importlib, os
N = importlib.import_module(os.environ.get("NARR_MOD", "narration"))

FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 44100
ROOT = os.path.dirname(os.path.abspath(__file__))


def decode(mp3):
    raw = subprocess.run(
        [FF, "-v", "quiet", "-i", mp3, "-ar", str(SR), "-ac", "1", "-f", "s16le", "-"],
        capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def build(out_wav, pages_file, pad_file, tail=1.0):
    rows = []
    with open(pages_file, encoding="utf-8") as fh:
        for line in fh:
            p = line.split()
            if len(p) == 4:
                rows.append((p[0], int(p[1]), float(p[2]), float(p[3])))
    pad = {}
    if os.path.exists(pad_file):
        pad = json.load(open(pad_file, encoding="utf-8"))

    by_scene = {}
    for sc, idx, st, en in rows:
        by_scene.setdefault(sc, []).append((idx, st, en))

    # 场景是分别渲染后拼接的：全局时间 = 前面所有场景时长之和
    place = []
    off = 0.0
    for sc in N.ORDER:
        cum = 0.0
        pages = sorted(by_scene[sc])
        for idx, st, en in pages:
            place.append((sc, idx, off + st + cum))
            cum += float(pad.get("%s|%d" % (sc, idx), 0.0))
        off += max(en for _, _, en in pages) + cum

    total = off + tail
    buf = np.zeros(int(total * SR) + SR, dtype=np.float32)

    for (scene, idx, at) in place:
        text = N.NARR[scene][idx]
        mp3 = N._path(scene, idx, text)
        x = decode(mp3)
        n = min(int(0.005 * SR), len(x) // 2)
        if n > 0:
            x[:n] *= np.linspace(0, 1, n)
            x[-n:] *= np.linspace(1, 0, n)
        s = int((at + N.LEAD) * SR)
        e = min(len(buf), s + len(x))
        buf[s:e] += x[:e - s]
        if e - s < len(x):
            print("WARN 溢出:", scene, idx)

    peak = float(np.abs(buf).max()) or 1.0
    buf *= 0.89 / peak
    pcm = (np.clip(buf, -1, 1) * 32767).astype(np.int16)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("视频总长应为 %.2f s；音频轨 %.2f s" % (off, len(pcm) / SR))
    return len(pcm) / SR


def mux(video, audio, out):
    cmd = [FF, "-y", "-i", video, "-i", audio,
           "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
           "-af", "aresample=44100", "-shortest", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print("成片:", out, "%.1f MB" % (os.path.getsize(out) / 1e6))


if __name__ == "__main__":
    pages = sys.argv[1]
    wav = os.path.join(ROOT, "_work", "voice_track.wav")
    out = sys.argv[2]
    build(wav, pages, N.PAD)
    mux(sys.argv[3], wav, out)
