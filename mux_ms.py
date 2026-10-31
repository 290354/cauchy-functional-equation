"""漫士版合成：按「实测场景时长 + 页内时间」精确铺音轨。

页面时间（pages.txt）已包含补时；场景偏移用渲染出来的 mp4 实测时长，
避免任何累计误差。
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np
import av
import imageio_ffmpeg

import narration_ms as N

FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 44100


def decode(mp3):
    raw = subprocess.run(
        [FF, "-v", "quiet", "-i", mp3, "-ar", str(SR), "-ac", "1", "-f", "s16le", "-"],
        capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def scene_durations(dirpath):
    out = {}
    for sc in N.ORDER:
        p = os.path.join(dirpath, sc + ".mp4")
        c = av.open(p)
        out[sc] = float(c.duration) / av.time_base
        c.close()
    return out


def read_pages(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            p = line.split()
            if len(p) == 4:
                rows.append((p[0], int(p[1]), float(p[2]), float(p[3])))
    return rows


def main():
    pages_file, media_dir, out = sys.argv[1], sys.argv[2], sys.argv[3]
    rows = read_pages(pages_file)
    by = {}
    for sc, i, st, en in rows:
        by.setdefault(sc, []).append((i, st, en))
    durs = scene_durations(media_dir)

    place = []
    off = 0.0
    for sc in N.ORDER:
        for i, st, en in sorted(by[sc]):
            place.append((sc, i, off + st))
        off += durs[sc]
    video_total = off
    print("场景时长:", {k: round(v, 2) for k, v in durs.items()})
    print("视频合计 %.2f s" % video_total)

    total = video_total + 1.0
    buf = np.zeros(int(total * SR) + SR, dtype=np.float32)

    for sc, i, at in place:
        text = N.NARR[sc][i]
        mp3 = N._path(sc, i, text)
        x = decode(mp3)
        n = min(int(0.005 * SR), len(x) // 2)
        if n:
            x[:n] *= np.linspace(0, 1, n)
            x[-n:] *= np.linspace(1, 0, n)
        s = int((at + N.LEAD) * SR)
        e = min(len(buf), s + len(x))
        buf[s:e] += x[:e - s]
        if e - s < len(x):
            print("WARN 溢出:", sc, i)

    peak = float(np.abs(buf).max()) or 1.0
    buf *= 0.89 / peak
    pcm = (np.clip(buf, -1, 1) * 32767).astype(np.int16)
    wav = os.path.join("_work", "ms_voice.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("音轨 %.2f s -> %s" % (len(pcm) / SR, wav))

    silent = os.path.join("_work", "ms_silent.mp4")
    subprocess.run([FF, "-y", "-i", silent, "-i", wav,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-af", "aresample=44100", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print("成片:", out, "%.1f MB" % (os.path.getsize(out) / 1e6))


if __name__ == "__main__":
    main()
