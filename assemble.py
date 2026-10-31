import os
import subprocess
import sys
import glob
import av
import imageio_ffmpeg

ORDER = ["S1Intro", "S2Algebra", "S3Regularity", "S4Hamel",
         "S5Measurable", "S6Variants", "S7Outlook"]


def find(dirpath):
    files = []
    for name in ORDER:
        hits = glob.glob(os.path.join(dirpath, name + ".mp4"))
        if not hits:
            raise SystemExit(f"missing {name} in {dirpath}")
        files.append(hits[0])
    return files


def duration(f):
    c = av.open(f)
    d = float(c.duration) / av.time_base
    c.close()
    return d


def main():
    src = sys.argv[1]
    out = sys.argv[2]
    files = find(src)
    lst = os.path.join(os.path.dirname(out), "_concat.txt")
    with open(lst, "w", encoding="utf-8") as fh:
        for f in files:
            fh.write("file '%s'\n" % f.replace("\\", "/"))
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-f", "concat", "-safe", "0", "-i", lst,
           "-c", "copy", "-movflags", "+faststart", out]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)
    total = 0.0
    for f in files:
        d = duration(f)
        total += d
        print(f"{os.path.basename(f):22s} {d:7.2f}s")
    print(f"{'TOTAL':22s} {total:7.2f}s  ({total/60:.2f} min)")
    print(f"output: {out}  size={os.path.getsize(out)/1e6:.1f} MB")


if __name__ == "__main__":
    main()
