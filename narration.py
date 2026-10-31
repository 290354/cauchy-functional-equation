"""配音：逐页脚本 + edge-tts 合成 + 页面补时表。

流程
    python narration.py synth    # 生成/复用音频，打印每页时长
    python narration.py pad      # 依据 pages.txt 计算 pad.json
"""
import asyncio
import hashlib
import json
import os
import sys

import av

VOICE = "zh-CN-YunxiNeural"
RATE = "+10%"
ROOT = os.path.dirname(os.path.abspath(__file__))
VOICE_DIR = os.path.join(ROOT, "_work", "voice")
PAGES = os.path.join(ROOT, "_work", "pages.txt")
PAD = os.path.join(ROOT, "pad.json")

LEAD = 0.35      # 页面开始后多久开口
TAIL = 0.30      # 说完到翻页余量

# ---------------------------------------------------------------- 分页脚本
NARR = {
    "S1Intro": [
        "这条方程看上去简单到不需要解释：两个自变量先相加再代入 f，与分别代入再相加，结果必须一样。"
        "可正是它，把连续性、选择公理、不可测集这些概念串在了一起。",

        "一八二一年，柯西在《分析教程》里写下它，并且断言解只能是 c 乘 x。"
        "但这个断言默认了函数是连续的；缺口要到一九零五年，Hamel 用一组基构造出反例，"
        "再到一九七零年，Solovay 说明这种反例必须依赖选择公理，才算彻底看清。",

        "所以真正要问的是：如果只假设这条方程成立，不加任何连续、单调、可测的条件，究竟有多少个解？"
        "直觉给出的线性函数，是全部答案，还是一片巨大丛林里的一小块？",

        "接下来分四步走。先把方程本身榨干，看它到底在说什么；再补上正则性，看线性怎么被逼出来；"
        "然后放开正则性，亲手构造病态解；最后讨论可测性、变体和应用。",
    ],
    "S2Algebra": [
        "我们从零开始，只用方程。把 x 和 y 都取成零，右边就是两个 f 零相加；"
        "于是 f 零等于两倍的 f 零，也就是 f 零等于零。",

        "再把 y 换成负 x：f x 加上 f 负 x，等于 f 零，也就是零。"
        "所以 f 负 x 等于负的 f x——满足柯西方程的函数，一定是奇函数。",

        "接下来用归纳法。n 等于一时显然成立；如果 f 的 n x 等于 n 倍的 f x，"
        "那么 n 加一倍的 x 就是 n x 再加 x，用方程拆开，正好多出一个 f x。"
        "于是对所有正整数成立，负整数由奇性直接得到。",

        "关键的一步，是把 x 切成 n 份。n 个 n 分之 x 加起来正好是 x，"
        "所以 f x 等于 n 倍的 f n 分之 x；反解出来，f n 分之 x 就是 n 分之一倍的 f x。"
        "再叠上整数倍，就得到有理数齐性。特别地，取 x 等于一，所有有理点上的值都被常数 c 唯一确定。",

        "换句话说，柯西方程和「f 是有理数域上的线性映射」完全是一回事。"
        "图上很直观：所有有理点的值，被死死钉在一条过原点的直线上；"
        "可一旦 x 是无理数，方程对它没有任何约束，纵坐标可以随便跑。",

        "而实数作为有理数上的向量空间，是无穷维的。"
        "一个解在有理点上给出的信息，对无理点毫无约束力。"
        "所以真正的问题是：会不会存在不是 c 乘 x 的解？",
    ],
    "S3Regularity": [
        "柯西自己也意识到这里有缺口，所以他悄悄加了假设。这张清单是等价的："
        "在实数上连续、在某一点连续、在某个区间上单调、在某个区间上有界。"
        "这五个条件里的任意一个，都能把解逼成线性。",

        "第一步也是最硬的：只要有界就够。设原点附近 f 的绝对值不超过 M。"
        "给定 epsilon，取 n 使 n 分之 M 小于 epsilon；若 x 小于 n 分之 delta，则 n x 仍在 delta 内。"
        "于是 f x 等于 n 分之 f n x，不超过 n 分之 M，小于 epsilon——f 在原点连续。",

        "一点连续就够了，因为 f 的 x 加 h 减去 f x，就是 f h，随 h 趋于零而趋于零。"
        "有了连续，取一列有理数逼近 x，函数值就等于 c 乘这列有理数，极限就是 c x。"
        "到这里，线性被完全锁死。",

        "把这几步串起来，就是一条链：单调给出有界，有界给出一点连续，一点连续给出处处连续，连续给出线性。"
        "反方向都是显然的。请注意，这五条都是额外假设，方程本身推不出来。",

        "那还能更弱吗？可以。Lebesgue 可测就够了，下一节给证明；"
        "更强一点的结果来自 Sierpiński：只要在一个正测度的集合上有界就够。"
        "甚至 f 只要是某个可测函数的导数，也自动线性。",
    ],
    "S4Hamel": [
        "现在把正则性全部拿掉。换个角度看：实数不只是实数，"
        "它是一个有理数上的向量空间——允许的加法还是实数加法，但允许的数乘只有有理数。",

        "作为向量空间，它有一组基，叫 Hamel 基，存在性由佐恩引理保证。"
        "每个实数都能唯一写成基元素的有理线性组合。所以只要任意指定每个基元素映到哪里，再线性延拓，"
        "造出的 f 就自动满足柯西方程；反过来，f 在基上的值也决定了整个 f。",

        "看一个具体的例子。取基里包含 1 和根号 2，让 1 被映到零，根号 2 被映到一，其余基元素都映到零。"
        "那么在整数格点上，f 的 m 加 n 倍根号 2 就等于 n。"
        "于是 f 一等于零，f 根号 2 等于一——它不可能是 c 乘 x，因为那要求 c 等于 f 一，等于零。",

        "它的图像长这样：在由 1 和根号 2 张成的有理平面上，图像落在一条条水平线上，根本不像直线。"
        "而一旦把整个 Hamel 基补满，图像会在平面上稠密——任何一个小圆盘里，都有它的点。",

        "这类解因此有一整套病态性质：处处不连续；在每个非空开区间上无界；"
        "图像稠密到根本无法作图；也不是 Lebesgue 可测的。",

        "为什么图像一定稠密？因为不连续的可加函数，在每个小区间上都是无界的。"
        "取一个很小、但函数值很大的 u；那么沿着 x 零加 q 倍 u 移动时，横坐标几乎不动，纵坐标却能扫过任意高度。",

        "这一切的代价是选择公理——Hamel 基的存在性本质上要用到它。"
        "Solovay 在一九七零年证明：在一个所有集合都可测的模型里，每个解都必须是 c 乘 x。"
        "所以病态解不是「我们还没找到」，而是「不动用选择公理就造不出来」。",
    ],
    "S5Measurable": [
        "把正则性弱到极致：只要 Lebesgue 可测。思路是把 f 积分一次——积分会把野性磨平。"
        "令 F x 等于 f 从零到 x 的积分；可测保证它有意义，而 F 是连续可微的。",

        "把区间拆开，再平移积分变量，利用 f 的可加性，就得到："
        "F 的 x 加 y 等于 F x 加 F y，再加上 y 倍的 f x。",

        "x 和 y 的地位本来是对称的，换一遍顺序，就得到同一个式子加上 x 倍的 f y。"
        "两式相减：y 乘 f x 等于 x 乘 f y。于是 f x 比 x 是一个与 x 无关的常数，f 只能是线性的。",

        "还有一条更几何的路线。可测集在平移下测度不变；如果两个集合的测度之和超过全空间，它们必然相交。"
        "所以差集 E 减 E 一定包含一个以零为中心的区间。于是 f 在一个区间上有界，回到上一节的定理。",

        "推论很清楚：病态解不可测，所以既画不出来，也构造不出来。"
        "连续性、单调性、有界性、可测性——四种「足够好」，指向的是同一个结论。",
    ],
    "S6Variants": [
        "同一个方程换一件外衣，就变成另一个熟悉的函数。把加法换成乘法：f 的 x 加 y，等于 f x 乘 f y。"
        "非零解一定处处为正，因为 f x 等于 f 二分之 x 的平方。取对数，它就变回柯西方程。"
        "所以连续解只能是指数函数。",

        "对乘法可加，就是对数。把 x 写成 e 的 u 次方，方程变成 h 的 u 加 v 等于 h u 加 h v，回到柯西方程。"
        "连续时解是 c 乘 ln x；没有正则性时，把任意野的加法函数复合上对数，仍然是解。",

        "还有中点型，也叫 Jensen 方程。令 g 等于 f 减去 f 零，取 y 等于 x，可以得到 g 二 x 等于两倍 g x；"
        "再代回去，就变成 g x 加 g y 等于 g 的 x 加 y。所以它和柯西方程完全等价，解是加法函数加常数。",

        "如果乘法两边都可加，得到 f 的 x y 等于 f x 乘 f y，那么令 h u 等于 f 的 e 的 u 次方，"
        "就得到乘性的柯西方程；连续解是指数，回到 x 就是幂函数。"
        "顺带一提：满足柯西方程、并且在区间上凸的函数，也必然线性。",

        "一张表收尾：加法型给线性，乘法型给指数，对数型给对数，中点型给仿射。"
        "每一行的背后，都藏着同一个前提——足够好的正则性。",
    ],
    "S7Outlook": [
        "为什么值得认真对待？线性代数里，线性映射的定义是加性加齐性；"
        "而这条方程说，加性并不自动给出齐性，中间隔着连续性的鸿沟。"
        "泛函分析里，这是可加算子与连续算子的问题；概率论里，特征函数满足乘性柯西方程，靠连续性锁定分布；"
        "物理里的叠加原理，也是同一个定理。",

        "留三个练习。第一个：右边多出一项 x y，怎么化归？提示是减去二分之 x 平方。"
        "第二个：把「区间上有界」换成「在零一区间上有上界」，证明结论仍然成立。"
        "第三个：如果 f 在某个区间上不单调，证明它的图像在平面上稠密——"
        "这题说明，病态解不是例外，而是稠密的一整片。",

        "总结四句话。第一，方程本身只给出有理线性。"
        "第二，连续、单调、有界、可测，任一条就能得到线性。"
        "第三，去掉正则性，Hamel 基能造出稠密、无界、不可测的病态解。"
        "第四，这类解的存在性，必须动用选择公理。"
        "柯西方程的全部解，是一个巨大、稠密、不可测的家族；而连续性一刀切下去，只剩下一条过原点的直线。",
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
            if len(parts) != 4:
                continue
            rows.append((parts[0], int(parts[1]), float(parts[2]), float(parts[3])))
    return rows


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "synth"
    if cmd == "synth":
        asyncio.run(_synth_all())
        d = durations()
        total = 0.0
        for scene in ORDER:
            for idx, _ in enumerate(NARR[scene]):
                total += d[(scene, idx)]
        print("旁白总时长 %.1f s (%.2f min)" % (total, total / 60))

    elif cmd == "pad":
        d = durations()
        rows = read_pages()
        pid = 0
        pad = {}
        audio_total = 0.0
        print("%-14s %3s %7s %7s %6s %6s" % ("scene", "pg", "win", "audio", "pad", "start"))
        for scene, idx, start, end in rows:
            key = (scene, idx)
            if key not in d or d[key] is None:
                print("MISSING", key)
                continue
            dur = d[key]
            audio_total += dur
            win = end - start
            p = max(0.0, dur + LEAD + TAIL - win)
            pad["%s|%d" % (scene, idx)] = round(p, 2)
            print("%-14s %3d %7.2f %7.2f %6.2f %6.2f" % (scene, idx, win, dur, p, start))
        with open(PAD, "w", encoding="utf-8") as fh:
            json.dump(pad, fh, indent=1)
        vsum = rows[-1][3]
        print("页面合计 %.1f s，旁白合计 %.1f s，补时合计 %.1f s"
              % (vsum, audio_total, sum(pad.values())))


if __name__ == "__main__":
    main()
