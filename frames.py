import sys, os
import av

def grab(path, times, outdir="frames"):
    os.makedirs(outdir, exist_ok=True)
    c = av.open(path)
    st = c.streams.video[0]
    dur = float(c.duration) / av.time_base if c.duration else 0
    targets = sorted(times)
    idx = 0
    n = 0
    for frame in c.decode(video=0):
        t = float(frame.pts * st.time_base)
        if idx < len(targets) and t >= targets[idx]:
            img = frame.to_image()
            name = os.path.join(outdir, f"f{targets[idx]:07.2f}.png")
            img.save(name)
            n += 1
            idx += 1
        if idx >= len(targets):
            break
    print(f"duration={dur:.2f}s saved={n}")

if __name__ == "__main__":
    path = sys.argv[1]
    ts = [float(x) for x in sys.argv[2].split(",")]
    grab(path, ts, sys.argv[3] if len(sys.argv) > 3 else "frames")
