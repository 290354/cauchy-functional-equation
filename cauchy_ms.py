"""
柯西函数方程 —— 漫士风格重制版

视觉原则
    极简 / 衬线 / 慢 / 留白 / 书面语。
    一页只说一件事；公式居中，四周留白；转场用黑场，不用飞散。

    字体：STZhongsong（标题） SimSun（正文） KaiTi（批注） Georgia（西文小字）
    配色：墨黑 #0B0B0C / 纸白 #EDE6DA / 灰褐 #8A8175 / 朱砂 #B4483C / 赭金 #C8A05A
"""
from manim import *
import numpy as np
import os
import json

# ---------------------------------------------------------------- 视觉常量
BG = "#0B0B0C"
INK = "#EDE6DA"
DIM = "#8A8175"
FAINT = "#4A443C"
RED = "#B4483C"
GOLD = "#C8A05A"
LINE = "#2A2724"

SERIF = "STZhongsong"
SONG = "SimSun"
KAI = "KaiTi"

config.background_color = BG
config.no_latex_cleanup = True

PACE = 1.55
PAD = {}
_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pad_ms.json")
if os.path.exists(_p):
    with open(_p, encoding="utf-8") as _fh:
        PAD = json.load(_fh)

PAGELOG = []


# ---------------------------------------------------------------- 文字工具
def tx(s, size=26, color=INK, font=SONG):
    return Text(s, font=font, font_size=size, color=color)


def kai(s, size=20, color=DIM):
    return Text(s, font=KAI, font_size=size, color=color)


def serif(s, size=34, color=INK):
    return Text(s, font=SERIF, font_size=size, color=color)


def en(s, size=13, color=FAINT):
    t = Text(s, font="Georgia", font_size=size, color=color)
    return t


def mt(s, size=40, color=INK):
    return MathTex(s, font_size=size, color=color)


def spaced(s, font=SERIF, size=64, color=INK, gap=0.12):
    """逐字排开，做出字距很松的标题感。"""
    g = VGroup(*[Text(ch, font=font, font_size=size, color=color) for ch in s])
    g.arrange(RIGHT, buff=gap)
    return g


def rule(width=2.2, color=LINE, sw=1.0):
    return Line(ORIGIN, RIGHT * width, stroke_width=sw, color=color)


def quote(s, size=34, color=INK, key=None, key_color=RED):
    """金句：逐字成组，可高亮其中一段。"""
    chars = []
    start = s.find(key) if key else -1
    for i, ch in enumerate(s):
        c = key_color if (key and 0 <= start <= i < start + len(key)) else color
        chars.append(Text(ch, font=SERIF, font_size=size, color=c))
    g = VGroup(*chars)
    g.arrange(RIGHT, buff=size * 0.004 + 0.02)
    return g


# ---------------------------------------------------------------- 基类
class Base(Scene):
    CHAPTERS = 7

    def construct(self):
        self.body()
        extra = float(PAD.get("%s|%d" % (type(self).__name__, self._pidx), 0.0))
        if extra > 0:
            super().wait(extra)

    def setup(self):
        super().setup()
        self._pidx = 0
        self._pstart = 0.0
        self._wtotal = 0.0
        self._foot = None

    def wait(self, duration=DEFAULT_WAIT_TIME, stop_condition=None):
        self._wtotal += duration * PACE
        return super().wait(duration * PACE, stop_condition)

    # ---- 页脚：七个点，标记当前章
    def foot(self, n):
        if self._foot is not None:
            self.remove(self._foot)
        dots = VGroup()
        for i in range(self.CHAPTERS):
            r = 0.045 if i == n - 1 else 0.028
            c = INK if i == n - 1 else FAINT
            dots.add(Dot(radius=r, color=c))
        dots.arrange(RIGHT, buff=0.22)
        dots.move_to(DOWN * 3.62)
        self._foot = dots
        self.add(dots)

    def wipe(self, keep=(), run_time=0.9):
        cls = type(self).__name__
        t = self.renderer.time
        extra = float(PAD.get("%s|%d" % (cls, self._pidx), 0.0))
        if extra > 0:
            super().wait(extra)
        end = t + max(extra, 0.0)
        PAGELOG.append((cls, self._pidx, round(self._pstart, 3), round(end, 3)))
        if os.environ.get("MN_DUMP"):
            with open(os.environ["MN_DUMP"], "a", encoding="utf-8") as fh:
                fh.write("%s\t%d\t%.3f\t%.3f\n" % PAGELOG[-1])
        self._pidx += 1
        outs = [m for m in self.mobjects if m not in keep and m is not self._foot]
        if outs:
            self.play(*[FadeOut(m) for m in outs], run_time=run_time)
        self._pstart = self.renderer.time

    def tear_down(self):
        cls = type(self).__name__
        if self.renderer.time - self._pstart > 0.05:   # 收尾若已翻页，就不再记一页
            PAGELOG.append((cls, self._pidx, round(self._pstart, 3),
                            round(self.renderer.time, 3)))
            if os.environ.get("MN_DUMP"):
                with open(os.environ["MN_DUMP"], "a", encoding="utf-8") as fh:
                    fh.write("%s\t%d\t%.3f\t%.3f\n" % PAGELOG[-1])
        print("[[WAITS]] %s %.2f" % (cls, self._wtotal))
        super().tear_down()

    # ---- 常用演出
    def soft(self, *mobs, run_time=1.5):
        self.play(*[FadeIn(m, shift=UP * 0.12) for m in mobs], run_time=run_time)

    def chapter_card(self, num, phrase, english, idx):
        self.foot(idx)
        n = kai(num, 17, DIM)
        n.move_to(LEFT * 4.2 + UP * 1.55)
        p = spaced(phrase, size=62, color=INK, gap=0.16)
        p.next_to(n, DOWN, buff=0.42)
        p.align_to(n, LEFT)
        r = rule(2.4)
        r.next_to(p, DOWN, buff=0.5)
        r.align_to(p, LEFT)
        e = en(english, 12, FAINT)
        e.next_to(r, DOWN, buff=0.3)
        e.align_to(r, LEFT)

        self.play(FadeIn(n), run_time=1.0)
        self.wait(0.6)
        for ch in p:
            self.play(FadeIn(ch, shift=UP * 0.08), run_time=0.16)
        self.wait(0.5)
        self.play(Create(r), FadeIn(e), run_time=1.2)
        self.wait(2.2)

    def lead_quote(self, lines, run_time=2.2):
        """整页金句，逐字浮现。"""
        g = VGroup(*lines).arrange(DOWN, buff=0.55)
        g.move_to(UP * 0.15)
        for ln in lines:
            self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.06) for c in ln],
                                  lag_ratio=0.055), run_time=run_time)
            self.wait(1.0)
        return g


# ================================================================ 壹
class S1Intro(Base):
    def body(self):
        self.foot(1)
        # ---------------- 封面
        kick = kai("数学 · 函数方程", 17, DIM)
        kick.to_corner(UL, buff=0.75)
        title = spaced("柯西函数方程", size=66, color=INK, gap=0.2)
        title.move_to(UP * 0.35)
        r = rule(6.4, LINE, 1.2)
        r.next_to(title, DOWN, buff=0.55)
        e = en("THE CAUCHY FUNCTIONAL EQUATION", 13, DIM)
        e.next_to(r, DOWN, buff=0.42)

        self.play(FadeIn(kick), run_time=1.4)
        self.wait(0.8)
        for ch in title:
            self.play(FadeIn(ch, shift=UP * 0.08), run_time=0.2)
        self.wait(0.8)
        self.play(Create(r), run_time=1.6)
        self.play(FadeIn(e), run_time=1.2)
        self.wait(3.0)
        self.wipe()

        # ---------------- 方程
        eq = mt(r"f(x+y)=f(x)+f(y)", size=86, color=INK)
        eq.move_to(UP * 0.45)
        cap = kai("对一切实数 x 与 y", 19, DIM)
        cap.next_to(eq, DOWN, buff=0.85)
        src = kai("A.-L. Cauchy，1821", 15, FAINT)
        src.move_to(DOWN * 2.5)

        self.play(Write(eq), run_time=3.0)
        self.wait(1.2)
        self.play(FadeIn(cap), run_time=1.2)
        self.play(FadeIn(src), run_time=1.0)
        self.wait(3.4)
        self.wipe()

        # ---------------- 金句一
        q1 = quote("柯西说，解只能是", 38, INK)
        q2 = quote("c 乘 x。", 38, INK)
        gg = VGroup(q1, q2).arrange(DOWN, buff=0.55).move_to(UP * 0.35)

        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.06) for c in q1],
                              lag_ratio=0.05), run_time=2.2)
        self.wait(0.8)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.06) for c in q2],
                              lag_ratio=0.05), run_time=1.4)
        self.wait(2.2)

        q3 = quote("他没有说清，为什么。", 38, DIM, key="为什么", key_color=RED)
        q3.next_to(q2, DOWN, buff=1.1)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.06) for c in q3],
                              lag_ratio=0.05), run_time=2.2)
        self.wait(4.0)
        self.wipe()

        # ---------------- 时间线
        y = 0.9
        ln = Line(LEFT * 4.6 + UP * y, RIGHT * 4.6 + UP * y, stroke_width=1.0, color=LINE)
        self.play(Create(ln), run_time=1.8)

        marks = [(-3.6, "1821", "柯西写下它", "默认了连续"),
                 (0.0, "1905", "Hamel", "用一组基造出反例"),
                 (3.6, "1970", "Solovay", "说明必须用选择公理")]
        for x, yr, who, what in marks:
            d = Dot(np.array([x, y, 0.0]), radius=0.05, color=INK)
            y1 = en(yr, 20, INK).next_to(d, UP, buff=0.35)
            w1 = serif(who, 22, INK).next_to(y1, UP, buff=0.16)
            w2 = kai(what, 16, DIM).next_to(d, DOWN, buff=0.32)
            self.play(FadeIn(d, scale=0.4), FadeIn(y1), FadeIn(w1), FadeIn(w2),
                      run_time=1.3)
            self.wait(1.6)
        self.wait(3.0)
        self.wipe()


# ================================================================ 贰
class S2Algebra(Base):
    def body(self):
        self.chapter_card("第一章", "方程在说什么", "WHAT THE EQUATION SAYS", 2)
        self.wipe()

        # ---------------- f(0)=0
        a = kai("令 x = y = 0", 19, DIM).move_to(UP * 1.85)
        e1 = mt(r"f(0)=f(0)+f(0)\ \Longrightarrow\ f(0)=0", size=44)
        self.play(FadeIn(a), run_time=1.0)
        self.play(Write(e1), run_time=2.6)
        self.wait(3.0)
        self.wipe()

        # ---------------- 奇性
        a = kai("再把 y 换成 -x", 19, DIM).move_to(UP * 1.85)
        e2 = mt(r"f(x)+f(-x)=f(0)=0\ \Longrightarrow\ f(-x)=-f(x)", size=42)
        self.play(FadeIn(a), run_time=1.0)
        self.play(Write(e2), run_time=2.8)
        c2 = kai("它一定是奇函数", 19, DIM)
        c2.next_to(e2, DOWN, buff=1.0)
        self.play(FadeIn(c2), run_time=1.2)
        self.wait(3.0)
        self.wipe()

        # ---------------- 整数倍 / 有理倍
        a = kai("整数倍，用归纳法", 19, DIM).move_to(UP * 2.0)
        e3 = mt(r"f(nx)=n\,f(x),\qquad n\in\mathbb{Z}", size=42)
        e3.move_to(UP * 0.95)
        self.play(FadeIn(a), run_time=1.0)
        self.play(Write(e3), run_time=2.2)
        self.wait(2.4)

        b = kai("有理倍，把 x 切成 n 份", 19, DIM).move_to(DOWN * 0.35)
        e4 = mt(r"f(x)=n\,f\!\left(\tfrac{x}{n}\right)\ \Longrightarrow\ "
                r"f\!\left(\tfrac{x}{n}\right)=\tfrac{1}{n}f(x)", size=40)
        e4.move_to(DOWN * 1.35)
        self.play(FadeIn(b), run_time=1.0)
        self.play(Write(e4), run_time=2.4)
        self.wait(3.2)
        self.wipe()

        # ---------------- 结论
        e5 = mt(r"f(q)=c\,q", size=76, color=INK)
        e5.move_to(UP * 0.9)
        t1 = serif("方程只说了一件事：", 28, DIM)
        t1.next_to(e5, DOWN, buff=1.0)
        t2 = quote("它是有理数上的线性映射。", 32, INK, key="线性", key_color=GOLD)
        t2.next_to(t1, DOWN, buff=0.4)

        self.play(Write(e5), run_time=2.8)
        self.wait(1.4)
        self.play(FadeIn(t1), run_time=1.2)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.05) for c in t2],
                              lag_ratio=0.05), run_time=2.2)
        self.wait(4.2)
        self.wipe()

        # ---------------- 金句
        l1 = quote("有理点，被钉死。", 40, INK, key="钉死", key_color=GOLD)
        l2 = quote("无理点上，方程沉默。", 40, INK, key="沉默", key_color=RED)
        g = VGroup(l1, l2).arrange(DOWN, buff=0.75)
        g.move_to(UP * 0.1)
        for ln in (l1, l2):
            self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.06) for c in ln],
                                  lag_ratio=0.05), run_time=2.4)
            self.wait(1.2)
        self.wait(4.2)
        self.wipe()


# ================================================================ 叁
class S3Regularity(Base):
    def body(self):
        self.chapter_card("第二章", "一道裂缝", "THE GAP", 3)
        self.wipe()

        # ---------------- 四个条件
        a = kai("后来的两百年，人们往方程上加了各种条件", 19, DIM)
        a.move_to(UP * 2.55)
        self.play(FadeIn(a), run_time=1.4)
        self.wait(1.0)

        rows = ["在某一点连续", "在某个区间上单调", "在某个区间上有界",
                "Lebesgue 可测"]
        g = VGroup()
        for i, s in enumerate(rows):
            num = en("0%d" % (i + 1), 14, FAINT)
            body = serif(s, 26, INK)
            g.add(VGroup(num, body).arrange(RIGHT, buff=0.55))
        g.arrange(DOWN, buff=0.62, aligned_edge=LEFT)
        g.next_to(a, DOWN, buff=0.85).align_to(a, LEFT)

        for r in g:
            self.play(FadeIn(r, shift=RIGHT * 0.1), run_time=1.2)
            self.wait(1.0)
        self.wait(1.6)

        res = mt(r"\Longrightarrow\quad f(x)=c\,x", size=44, color=RED)
        res.next_to(g, DOWN, buff=0.95).align_to(g, LEFT)
        self.play(Write(res), run_time=2.4)
        self.wait(3.4)
        self.wipe()

        # ---------------- ε-δ
        a = kai("最硬的一步，是「有界」", 19, DIM).move_to(UP * 2.6)
        self.play(FadeIn(a), run_time=1.2)
        self.wait(0.8)

        l1 = mt(r"\exists\,M>0,\ \delta>0:\quad |f(t)|\le M\quad (|t|<\delta)", size=32, color=DIM)
        l2 = mt(r"\varepsilon>0\ \Longrightarrow\ \exists\,n:\ \frac{M}{n}<\varepsilon", size=32)
        l3 = mt(r"|x|<\frac{\delta}{n}\ \Longrightarrow\ |f(x)|\le\frac{M}{n}<\varepsilon",
                size=32, color=INK)
        grp = VGroup(l1, l2, l3).arrange(DOWN, buff=0.75, aligned_edge=LEFT)
        grp.next_to(a, DOWN, buff=0.85).align_to(a, LEFT).shift(RIGHT * 0.2)

        self.play(Write(l1), run_time=2.2)
        self.wait(2.0)
        self.play(Write(l2), run_time=2.2)
        self.wait(2.0)
        self.play(Write(l3), run_time=2.4)
        self.wait(1.2)

        fin = kai("f 在原点连续。", 20, INK)
        fin.next_to(grp, DOWN, buff=1.0)
        self.play(FadeIn(fin), run_time=1.4)
        self.wait(3.6)
        self.wipe()

        # ---------------- 有理逼近
        e = mt(r"q_n\in\mathbb{Q},\quad q_n\to x", size=40)
        e.move_to(UP * 1.9)
        self.play(Write(e), run_time=2.0)
        self.wait(1.0)

        e2 = mt(r"f(x)=\lim_{n\to\infty}f(q_n)=c\,x", size=48, color=GOLD)
        e2.next_to(e, DOWN, buff=1.0)
        self.play(Write(e2), run_time=2.6)
        self.wait(2.0)

        nl = NumberLine(x_range=[0, 2, 0.5], length=8.0, color=FAINT,
                        stroke_width=1.6, tick_size=0.04)
        nl.move_to(DOWN * 1.75)
        tgt = nl.n2p(1.4142135)
        mk = DashedLine(tgt + UP * 0.4, tgt + DOWN * 0.1, color=GOLD,
                        stroke_width=1.2, dash_length=0.06)
        lb = mt(r"x", size=24, color=GOLD).next_to(mk, UP, buff=0.1)
        self.play(FadeIn(nl), run_time=1.2)
        self.play(Create(mk), FadeIn(lb), run_time=1.0)
        dots = VGroup(*[Dot(nl.n2p(q), radius=0.04, color=INK)
                        for q in (1.0, 1.5, 1.4, 1.42, 1.414, 1.4142)])
        self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in dots],
                              lag_ratio=0.2), run_time=2.4)
        self.wait(3.6)
        self.wipe()

        # ---------------- 金句
        l1 = quote("连续性不是结论。", 40, INK, key="结论", key_color=DIM)
        l2 = quote("它是前提。", 40, INK, key="前提", key_color=RED)
        g = VGroup(l1, l2).arrange(DOWN, buff=0.7)
        g.move_to(UP * 0.1)
        for ln in (l1, l2):
            self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.06) for c in ln],
                                  lag_ratio=0.06), run_time=2.4)
            self.wait(1.2)
        self.wait(4.2)
        self.wipe()


# ================================================================ 肆
class S4Hamel(Base):
    def body(self):
        self.chapter_card("第三章", "丛林", "THE WILDERNESS", 4)
        self.wipe()

        # ---------------- 向量空间
        t = serif("把实数看成有理数上的向量空间。", 30, INK)
        t.move_to(UP * 2.1)
        self.play(FadeIn(t, shift=UP * 0.1), run_time=1.8)
        self.wait(1.4)

        e = mt(r"x=q_1b_1+q_2b_2+\cdots+q_kb_k,\qquad q_i\in\mathbb{Q}", size=36)
        e.next_to(t, DOWN, buff=0.9)
        self.play(Write(e), run_time=2.4)
        self.wait(1.2)

        c = kai("B 叫 Hamel 基；存在性由佐恩引理保证", 18, DIM)
        c.next_to(e, DOWN, buff=0.8)
        self.play(FadeIn(c), run_time=1.4)
        self.wait(3.4)
        self.wipe()

        # ---------------- 构造
        e = mt(r"f\!\left(\sum_i q_ib_i\right):=\sum_i q_i\,\varphi(b_i)",
               size=44, color=INK)
        e.move_to(UP * 1.3)
        self.play(Write(e), run_time=2.6)
        self.wait(1.0)

        c = kai("φ 可以任意指定 —— 于是这样的 f，和实数一样多", 18, DIM)
        c.next_to(e, DOWN, buff=0.9)
        self.play(FadeIn(c), run_time=1.6)
        self.wait(1.0)

        c2 = serif("它满足方程。", 28, DIM)
        c2.next_to(c, DOWN, buff=0.85)
        self.play(FadeIn(c2), run_time=1.4)
        self.wait(3.6)
        self.wipe()

        # ---------------- 反例
        a = kai("取基里有一和根号二", 19, DIM).move_to(UP * 2.35)
        e = mt(r"\varphi(1)=0,\qquad \varphi(\sqrt{2})=1", size=42)
        e.next_to(a, DOWN, buff=0.6)
        self.play(FadeIn(a), run_time=1.2)
        self.play(Write(e), run_time=2.2)
        self.wait(1.6)

        e2 = mt(r"\Longrightarrow\quad f(m+n\sqrt{2})=n", size=42, color=DIM)
        e2.next_to(e, DOWN, buff=0.8)
        self.play(Write(e2), run_time=2.2)
        self.wait(1.6)

        e3 = mt(r"f(1)=0,\qquad f(\sqrt{2})=1", size=48, color=RED)
        e3.next_to(e2, DOWN, buff=0.9)
        self.play(Write(e3), run_time=2.2)
        self.wait(1.2)

        c = kai("若 f 是 c 乘 x，则 c 等于 f 一，等于零 —— 矛盾", 18, DIM)
        c.next_to(e3, DOWN, buff=0.8)
        self.play(FadeIn(c), run_time=1.6)
        self.wait(4.0)
        self.wipe()

        # ---------------- 图像
        axes = Axes(x_range=[-5.2, 5.2, 1], y_range=[-2.8, 2.8, 1],
                    x_length=7.2, y_length=4.2,
                    axis_config={"color": FAINT, "stroke_width": 1.4,
                                 "include_ticks": False,
                                 "tip_width": 0.1, "tip_height": 0.1})
        axes.move_to(LEFT * 3.1 + DOWN * 0.2)
        self.play(FadeIn(axes), run_time=1.2)

        pts = VGroup()
        for n in range(-2, 3):
            for m in range(-55, 56):
                x = m + n * np.sqrt(2)
                if abs(x) <= 5.0:
                    pts.add(Dot(axes.c2p(x, n), radius=0.02,
                                color=INK if n else GOLD))
        self.play(LaggedStart(*[FadeIn(p, scale=0.3) for p in pts],
                              lag_ratio=0.004), run_time=4.0)
        self.wait(1.0)

        side = VGroup(
            kai("在 1 与根号二张成的平面上", 17, DIM),
            serif("它落在一条条水平线上。", 22, INK),
            kai("补满整个 Hamel 基之后", 17, DIM),
            serif("图像在平面上稠密。", 22, INK),
        ).arrange(DOWN, buff=0.34, aligned_edge=LEFT)
        side.next_to(axes, RIGHT, buff=0.6)
        for s in side:
            self.play(FadeIn(s, shift=RIGHT * 0.08), run_time=1.0)
            self.wait(1.0)
        self.wait(3.4)
        self.wipe()

        # ---------------- 金句
        l1 = quote("处处不连续。处处无界。", 38, INK, key="无界", key_color=RED)
        l2 = quote("图像稠密到，画不出来。", 38, INK, key="画不出来", key_color=RED)
        g = VGroup(l1, l2).arrange(DOWN, buff=0.7)
        g.move_to(UP * 0.1)
        for ln in (l1, l2):
            self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.06) for c in ln],
                                  lag_ratio=0.05), run_time=2.4)
            self.wait(1.2)
        self.wait(4.2)
        self.wipe()

        # ---------------- 选择公理
        t = VGroup(
            serif("佐恩引理造出了 Hamel 基。", 28, INK),
            serif("Solovay 证明：不用选择公理，就造不出来。", 28, DIM),
        ).arrange(DOWN, buff=0.55)
        t.move_to(UP * 1.1)
        self.play(FadeIn(t[0], shift=UP * 0.1), run_time=1.8)
        self.wait(1.4)
        self.play(FadeIn(t[1], shift=UP * 0.1), run_time=1.8)
        self.wait(1.8)

        c = quote("它不是「还没找到」。", 30, INK, key="还没找到", key_color=DIM)
        c.next_to(t, DOWN, buff=1.2)
        self.play(LaggedStart(*[FadeIn(ch, shift=UP * 0.05) for ch in c],
                              lag_ratio=0.05), run_time=2.2)
        self.wait(1.0)

        c2 = quote("是「必须用公理」。", 30, RED, key="必须", key_color=RED)
        c2.next_to(c, DOWN, buff=0.55)
        self.play(LaggedStart(*[FadeIn(ch, shift=UP * 0.05) for ch in c2],
                              lag_ratio=0.05), run_time=2.0)
        self.wait(4.0)
        self.wipe()


# ================================================================ 伍
class S5Measurable(Base):
    def body(self):
        self.chapter_card("第四章", "可测", "MEASURABLE", 5)
        self.wipe()

        t = serif("把 f 积分一次。", 30, INK)
        t.move_to(UP * 2.2)
        t2 = kai("积分会把野性磨平", 18, DIM)
        t2.next_to(t, DOWN, buff=0.3)
        self.play(FadeIn(t, shift=UP * 0.1), run_time=1.6)
        self.play(FadeIn(t2), run_time=1.2)
        self.wait(1.6)

        e = mt(r"F(x):=\int_0^{x}f(t)\,dt", size=44, color=DIM)
        e.next_to(t2, DOWN, buff=0.9)
        self.play(Write(e), run_time=2.2)
        self.wait(1.4)

        e2 = mt(r"F(x+y)=F(x)+F(y)+y\,f(x)", size=44, color=INK)
        e2.next_to(e, DOWN, buff=0.9)
        self.play(Write(e2), run_time=2.4)
        self.wait(3.6)
        self.wipe()

        t = kai("x 与 y 地位对称，换一遍再相减", 19, DIM).move_to(UP * 2.3)
        self.play(FadeIn(t), run_time=1.2)
        self.wait(0.6)

        e = mt(r"y\,f(x)=x\,f(y)", size=64, color=GOLD)
        e.move_to(UP * 0.75)
        self.play(Write(e), run_time=2.6)
        self.wait(1.8)

        e2 = mt(r"\Longrightarrow\quad f(x)=c\,x", size=52, color=RED)
        e2.next_to(e, DOWN, buff=1.1)
        self.play(Write(e2), run_time=2.2)
        self.wait(1.4)

        c = serif("f 比 x，是一个常数。", 26, DIM)
        c.next_to(e2, DOWN, buff=1.0)
        self.play(FadeIn(c), run_time=1.4)
        self.wait(3.8)
        self.wipe()

        l1 = quote("可测。", 44, INK, key="可测", key_color=GOLD)
        l2 = quote("就已经足够好了。", 40, INK)
        g = VGroup(l1, l2).arrange(DOWN, buff=0.7)
        g.move_to(UP * 0.1)
        for ln in (l1, l2):
            self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.06) for c in ln],
                                  lag_ratio=0.07), run_time=2.4)
            self.wait(1.2)
        self.wait(4.0)
        self.wipe()


# ================================================================ 陆
class S6Variants(Base):
    def body(self):
        self.chapter_card("第五章", "外衣", "OTHER CLOTHES", 6)
        self.wipe()

        a = kai("同一条方程，换一件外衣", 19, DIM).move_to(UP * 2.5)
        self.play(FadeIn(a), run_time=1.4)
        self.wait(0.8)

        rows = [
            (r"f(x+y)=f(x)+f(y)", r"f(x)=c\,x", "线性"),
            (r"f(x+y)=f(x)\,f(y)", r"f(x)=a^{x}", "指数"),
            (r"f(xy)=f(x)+f(y)", r"f(x)=c\ln x", "对数"),
            (r"f(x+y)+f(x-y)=2f(x)", r"f(x)=ax+d", "仿射"),
        ]
        g = VGroup()
        for i, (eq_, sol, nm) in enumerate(rows):
            left = mt(eq_, size=28, color=INK)
            arrow = mt(r"\longrightarrow", size=24, color=FAINT)
            right = mt(sol, size=28, color=GOLD)
            tag = kai(nm, 15, DIM)
            r = VGroup(left, arrow, right, tag).arrange(RIGHT, buff=0.5)
            g.add(r)
        g.arrange(DOWN, buff=0.72, aligned_edge=LEFT)
        g.next_to(a, DOWN, buff=0.85).align_to(a, LEFT).shift(RIGHT * 0.1)

        for r in g:
            self.play(FadeIn(r, shift=RIGHT * 0.06), run_time=1.4)
            self.wait(1.2)
        self.wait(2.4)

        c = kai("以上都要求：足够好的正则性", 18, RED)
        c.next_to(g, DOWN, buff=0.85)
        self.play(FadeIn(c), run_time=1.4)
        self.wait(3.6)
        self.wipe()

        l1 = quote("没有正则性，", 38, INK)
        l2 = quote("它们都只是怪物换了衣服。", 38, INK, key="怪物", key_color=RED)
        gg = VGroup(l1, l2).arrange(DOWN, buff=0.7)
        gg.move_to(UP * 0.1)
        for ln in (l1, l2):
            self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.06) for c in ln],
                                  lag_ratio=0.05), run_time=2.4)
            self.wait(1.2)
        self.wait(4.0)
        self.wipe()


# ================================================================ 柒
class S7Outlook(Base):
    def body(self):
        self.chapter_card("第六章", "为什么值得认真对待", "WHY IT MATTERS", 7)
        self.wipe()

        rows = [
            ("线性代数", "加性，并不自动等于齐性"),
            ("泛函分析", "可加算子，与连续算子"),
            ("概率论", "特征函数，靠连续性锁定分布"),
            ("物理学", "叠加原理的唯一性"),
        ]
        g = VGroup()
        for tag, body in rows:
            t1 = kai(tag, 17, DIM)
            t2 = serif(body, 24, INK)
            g.add(VGroup(t1, t2).arrange(RIGHT, buff=0.7))
        g.arrange(DOWN, buff=0.72, aligned_edge=LEFT)
        g.move_to(UP * 1.0).shift(LEFT * 0.2)

        for r in g:
            self.play(FadeIn(r, shift=RIGHT * 0.06), run_time=1.4)
            self.wait(1.2)
        self.wait(3.2)
        self.wipe()

        # ---------------- 收束
        lines = [
            quote("它的全部解，是一个巨大、稠密、不可测的家族。", 26, INK),
            quote("而连续性一刀切下去，", 26, INK),
            quote("只剩一条过原点的直线。", 30, INK, key="一条过原点的直线", key_color=GOLD),
        ]
        g = VGroup(*lines).arrange(DOWN, buff=0.62)
        g.move_to(UP * 0.55)
        for ln in lines:
            self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.05) for c in ln],
                                  lag_ratio=0.04), run_time=2.6)
            self.wait(1.4)
        self.wait(3.0)

        r = rule(2.0, LINE, 1.0)
        r.next_to(g, DOWN, buff=0.9)
        end = kai("完", 18, DIM)
        end.next_to(r, DOWN, buff=0.45)
        self.play(Create(r), run_time=1.4)
        self.play(FadeIn(end), run_time=1.2)
        self.wait(4.0)
