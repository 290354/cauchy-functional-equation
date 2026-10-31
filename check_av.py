"""成片音画同步自检：检查每页旁白是否都在预期时间点响起。"""
import json
import os
import subprocess
import sys

import numpy as np
import imageio_ffmpeg

import importlib, os
N = importlib.import_module(os.environ.get("NARR_MOD", "narration"))

FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 16000


def audio_of(path):
    raw = subprocess.run(
        [FF, "-v", "quiet", "-i", path, "-vn", "-ar", str(SR), "-ac", "1",
         "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def expected(pages_file, pad_file, media_dir=None):
    rows = []
    with open(pages_file, encoding="utf-8") as fh:
        for line in fh:
            p = line.split()
            if len(p) == 4:
                rows.append((p[0], int(p[1]), float(p[2]), float(p[3])))
    # pages.txt 里的时间已经包含补时：场景内绝对时间
    by = {}
    for sc, i, st, en in rows:
        by.setdefault(sc, []).append((i, st, en))
    durs = {}
    if media_dir:
        import av as _av
        for sc in N.ORDER:
            c = _av.open(os.path.join(media_dir, sc + ".mp4"))
            durs[sc] = float(c.duration) / _av.time_base
            c.close()

    out = []
    off = 0.0
    for sc in N.ORDER:
        pages = sorted(by[sc])
        for i, st, en in pages:
            out.append((sc, i, off + st))
        off += durs.get(sc, max(en for _, _, en in pages))
    return out, off


def main():
    video = sys.argv[1]
    pages = sys.argv[2]
    x = audio_of(video)
    dur = len(x) / SR
    print("音轨时长 %.2f s，峰值 %.3f" % (dur, float(np.abs(x).max())))
    clips, vdur = expected(pages, N.PAD, sys.argv[3] if len(sys.argv) > 3 else None)
    print("预期视频时长 %.2f s" % vdur)
    bad = 0
    for sc, i, at in clips:
        s = int((at + N.LEAD + 0.45) * SR)
        w = x[s:s + int(1.2 * SR)]
        rms = float(np.sqrt((w ** 2).mean())) if len(w) else 0.0
        flag = "ok" if rms > 0.02 else "!!"
        if rms <= 0.02:
            bad += 1
        print("%s %-14s %2d  起 %.2f  rms=%.4f" % (flag, sc, i, at, rms))
    print("异常页数:", bad)


if __name__ == "__main__":
    main()
