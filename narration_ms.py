"""漫士风格配音稿 + 合成 + 补时（对应 cauchy_ms.py 的 32 页）。"""
import asyncio
import hashlib
import json
import os
import sys

import av

VOICE = "zh-CN-YunxiNeural"
RATE = "-4%"
ROOT = os.path.dirname(os.path.abspath(__file__))
VOICE_DIR = os.path.join(ROOT, "_work", "voice_ms")
PAGES = os.path.join(ROOT, "_work", "pages_ms.txt")
PAD = os.path.join(ROOT, "pad_ms.json")

LEAD = 0.45      # 页面开始后多久开口（漫士式留白）
TAIL = 0.55      # 说完到翻页余量

NARR = {
    "S1Intro": [
        "一条方程。两个自变量先相加，与分别代入再相加，结果必须一样。"
        "它朴素得几乎不像一个问题。",

        "一八二一年，柯西在《分析教程》里写下了它。"
        "这一年，他正在为整个分析学重新打地基。",

        "柯西说，解只能是 c 乘 x。"
        "他没有说清，为什么。",

        "这个缺口留了八十四年。一九零五年，Hamel 用一组基造出了反例；"
        "又过了六十五年，Solovay 说明，那样的反例必须动用选择公理。",
    ],
    "S2Algebra": [
        "先从方程本身说起。不加任何条件，只看它能推出什么。",

        "令 x 与 y 都等于零。右边是两个 f 零相加，左边是 f 零。"
        "于是 f 零等于零。第一步，方程就交代了自己的原点。",

        "再把 y 换成负 x。两个函数值之和，等于 f 零，也就是零。"
        "所以 f 负 x 等于负的 f x。它是奇函数。",

        "接下来是归纳。n 等于一时显然；n 加一倍的 x，拆成 n x 加 x，"
        "正好多出一个 f x。整数倍成立。再把 x 切成 n 份，有理倍也成立。",

        "于是所有有理点上的值，都由一个常数决定。"
        "方程只说了一件事：它是有理数上的线性映射。除此之外，它什么都没说。",

        "有理点，被钉死了。无理点上，方程沉默。",
    ],
    "S3Regularity": [
        "可是有理点之外，还有整整一片实数。那才是问题真正开始的地方。",

        "后来的两百年，人们不断往方程上加条件。在某一点连续，在某个区间上单调，"
        "在某个区间上有界，或者只要可测。任意一条，都能把解逼成一条直线。",

        "最硬的一步，是「有界」。设 f 在原点附近不超过 M。给一个 epsilon，"
        "取 n 足够大，让 n 分之 M 小于 epsilon。x 一旦缩进 n 分之 delta，"
        "函数值就小于 epsilon。它在原点连续。",

        "有了连续，取一列有理数逼近 x，函数值只能等于 c x。"
        "所有的自由度，在这里被一刀切断。",

        "连续性不是结论。它是前提。",
    ],
    "S4Hamel": [
        "把条件全部拿掉，还剩什么？剩下一片没有地图的丛林。",

        "换一个看法。实数不只是一条数轴，它是有理数上的向量空间。"
        "每个实数，都能唯一写成有限个基元素的有理组合。这组基，叫 Hamel 基。",

        "于是可以任意指定每个基元素被映到哪里，再线性延拓出去。"
        "这样造出来的 f，一定满足方程。自由度，和实数一样多。",

        "取一组含有一和根号二的基。让一映到零，根号二映到一。"
        "那么在整数格点上，f 就等于 n。f 一等于零，f 根号二等于一。"
        "它不可能是 c 乘 x。",

        "在由这两个数张成的平面上，它的图像落在一条条水平线上。"
        "而把整个基补满之后，图像会在整个平面上稠密——任何一个小圆盘里，都有它的点。",

        "处处不连续。处处无界。图像稠密到，画不出来。",

        "佐恩引理造出了这组基。Solovay 证明，不用选择公理，就造不出来。"
        "所以它不是「我们还没找到」，是「必须用公理」。",
    ],
    "S5Measurable": [
        "把条件放松到极致。不要连续，不要单调，只要可测。",

        "思路是把 f 积分一次。积分会把野性磨平。"
        "令 F 等于 f 从零到 x 的积分，它是连续的；而把区间拆开再平移，"
        "就得到 F 的 x 加 y，等于 F x 加 F y，再加 y 倍的 f x。",

        "x 与 y 本来是对称的。换一遍，两式相减，得到 y 乘 f x 等于 x 乘 f y。"
        "于是 f 比 x 只是一个常数。它只能是线性的。",

        "可测。就已经足够好了。",
    ],
    "S6Variants": [
        "同一个方程，换一件外衣，就是另一个熟悉的函数。",

        "加法换成乘法，解是指数；乘法变成可加，解是对数；"
        "中点形式，解是仿射。它们都长得不一样，却都要求同一个前提。",

        "没有正则性，它们都只是怪物换了衣服。",
    ],
    "S7Outlook": [
        "最后一个问题：这件事，为什么值得认真对待？",

        "线性代数里，加性并不自动等于齐性——中间隔着连续性。"
        "泛函分析里，这是可加算子与连续算子的问题。"
        "概率论里，特征函数靠连续性锁定分布。物理里，是叠加原理的唯一性。",

        "它的全部解，是一个巨大、稠密、不可测的家族。"
        "而连续性一刀切下去，只剩一条过原点的直线。",
    ],
}

ORDER = ["S1Intro", "S2Algebra", "S3Regularity", "S4Hamel",
         "S5Measurable", "S6Variants", "S7Outlook"]


def _path(scene, idx, text):
    h = hashlib.md5((VOICE + RATE + text).encode("utf-8")).hexdigest()[:10]
    return os.path.join(VOICE_DIR, "%s_%02d_%s.mp3" % (scene, idx, h))


async def _synth_all():
    import edge_tts
    os.makedirs(VOICE_DIR, exist_ok=True)
    for scene in ORDER:
        for idx, text in enumerate(NARR[scene]):
            p = _path(scene, idx, text)
            if os.path.exists(p) and os.path.getsize(p) > 2000:
                continue
            c = edge_tts.Communicate(text, VOICE, rate=RATE)
            await c.save(p)
            print("  tts", os.path.basename(p))
    print("TTS 完成")


def durations():
    out = {}
    for scene in ORDER:
        for idx, text in enumerate(NARR[scene]):
            p = _path(scene, idx, text)
            if not os.path.exists(p):
                out[(scene, idx)] = None
                continue
            c = av.open(p)
            out[(scene, idx)] = float(c.duration) / av.time_base
            c.close()
    return out


def read_pages():
    rows = []
    with open(PAGES, encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) == 4:
                rows.append((parts[0], int(parts[1]), float(parts[2]), float(parts[3])))
    return rows


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "synth"
    if cmd == "synth":
        asyncio.run(_synth_all())
        d = durations()
        total = sum(d[(s, i)] for s in ORDER for i in range(len(NARR[s])))
        print("旁白总时长 %.1f s (%.2f min)" % (total, total / 60))
    elif cmd == "pad":
        d = durations()
        rows = read_pages()
        pad = {}
        audio_total = 0.0
        print("%-14s %3s %7s %7s %6s" % ("scene", "pg", "win", "audio", "pad"))
        for scene, idx, start, end in rows:
            key = (scene, idx)
            if d.get(key) is None:
                print("MISSING", key)
                continue
            dur = d[key]
            audio_total += dur
            win = end - start
            p = max(0.0, dur + LEAD + TAIL - win)
            pad["%s|%d" % (scene, idx)] = round(p, 2)
            print("%-14s %3d %7.2f %7.2f %6.2f" % (scene, idx, win, dur, p))
        with open(PAD, "w", encoding="utf-8") as fh:
            json.dump(pad, fh, indent=1)
        vsum = sum(r[3] for r in rows)
        print("画面合计 %.1f s，旁白合计 %.1f s，补时合计 %.1f s，预计成片 %.1f s"
              % (vsum, audio_total, sum(pad.values()), vsum + sum(pad.values())))


if __name__ == "__main__":
    main()
