"""
柯西函数方程 (The Cauchy Functional Equation)
==============================================
一段约 10 分钟、数学性较强的 Manim 讲解视频。

分镜:
    S1  问题的提出             (~55 s)
    S2  代数性质与 Q-线性       (~100 s)
    S3  正则性条件              (~135 s)
    S4  Hamel 基与病态解        (~130 s)
    S5  可测性                  (~95 s)
    S6  变体与推广              (~95 s)
    S7  应用与总结              (~85 s)

渲染:
    manim -qm cauchy.py S1Intro S2Algebra ...      # 720p30
"""
from manim import *
import numpy as np
import os
import json

# ---------------------------------------------------------------- 视觉常量
BG = "#0E131A"
INK = "#E9EFF6"
DIM = "#7E93A8"
ACC = "#4FC3B0"      # 青绿 —— 主线强调
GOLD = "#E8B84B"     # 金 —— 结论 / 方程
RED = "#E4685D"      # 红 —— 错误直觉 / 反例
BLUE = "#6BA6E0"     # 蓝 —— 定义
VIOL = "#A78BFA"     # 紫 —— 病态
BOXBG = "#16202B"
LINE = "#22303F"

CN = "Microsoft YaHei"

config.background_color = BG
config.no_latex_cleanup = True


# ---------------------------------------------------------------- 工具函数
def ctext(s, size=28, color=INK, weight=NORMAL, slant=NORMAL):
    """中文文本。"""
    return Text(s, font=CN, font_size=size, color=color, weight=weight, slant=slant)


def mt(s, size=40, color=INK):
    """数学公式。"""
    return MathTex(s, font_size=size, color=color)


def rich(s, size=28, color=INK):
    """中英混排：$...$ 内用 LaTeX，其余用中文字体。"""
    import re
    parts = re.split(r"(\$[^$]*\$)", s)
    objs = []
    for p in parts:
        if not p:
            continue
        if p.startswith("$") and p.endswith("$"):
            objs.append(MathTex(p[1:-1], font_size=size * 1.12, color=color))
        else:
            objs.append(Text(p, font=CN, font_size=size, color=color))
    g = VGroup(*objs).arrange(RIGHT, buff=size * 0.16 / 28 + 0.05)
    for o in g:
        if isinstance(o, MathTex):
            o.shift(DOWN * size / 28 * 0.035)
    return g


def rn(math_tex, note, msize=38, nsize=21, buff=0.42):
    """公式 + 右侧小注。"""
    n = ctext(note, size=nsize, color=DIM)
    return VGroup(math_tex, n).arrange(RIGHT, buff=buff)


def card(*objs, width=7.0, height=0.85, color=ACC, fill=BOXBG, radius=0.12):
    """圆角卡片。"""
    r = RoundedRectangle(
        corner_radius=radius, width=width, height=height,
        stroke_color=color, stroke_width=1.6,
        fill_color=fill, fill_opacity=0.85,
    )
    inner = VGroup(*objs)
    inner.move_to(r.get_center())
    return VGroup(r, inner)


PACE_DEFAULT = 1.0

# 页面级补时表：{"场景|页码": 额外等待秒数}，由 narration.py 依据配音时长生成
PAD = {}
_pad_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pad.json")
if os.path.exists(_pad_path):
    with open(_pad_path, encoding="utf-8") as _fh:
        PAD = json.load(_fh)

PAGELOG = []


class Base(Scene):
    """统一页眉 / 进度条 / 翻页 / 配音打点。"""

    PACE = PACE_DEFAULT

    def construct(self):
        """先演完本页，再按配音需要补足最后一页的停留时间。"""
        self.body()
        extra = float(PAD.get("%s|%d" % (type(self).__name__, self._pidx), 0.0)) * self.PACE
        if extra > 0:
            super().wait(extra)

    def setup(self):
        super().setup()
        self._pidx = 0
        self._pstart = 0.0
        self._wtotal = 0.0

    def wait(self, duration=DEFAULT_WAIT_TIME, stop_condition=None):
        self._wtotal = getattr(self, "_wtotal", 0.0) + duration * self.PACE
        return super().wait(duration * self.PACE, stop_condition)

    def wipe(self, keep=(), run_time=0.55):
        """翻页：记录本页起止，并按 PAD 补足时长，然后淡出。"""
        cls = type(self).__name__
        t = self.renderer.time
        extra = float(PAD.get("%s|%d" % (cls, self._pidx), 0.0)) * self.PACE
        if extra > 0:
            super().wait(extra)
        end = t + max(extra, 0.0)
        PAGELOG.append((cls, self._pidx, round(self._pstart, 3), round(end, 3)))
        if os.environ.get("MN_DUMP"):
            with open(os.environ["MN_DUMP"], "a", encoding="utf-8") as fh:
                fh.write("%s\t%d\t%.3f\t%.3f\n" % PAGELOG[-1])
        self._pidx += 1
        outs = [m for m in self.mobjects if m not in keep]
        if outs:
            self.play(*[FadeOut(m) for m in outs], run_time=run_time)
        self._pstart = self.renderer.time

    def tear_down(self):
        cls = type(self).__name__
        PAGELOG.append((cls, self._pidx, round(self._pstart, 3),
                        round(self.renderer.time, 3)))
        print("[[WAITS]] %s %.2f" % (cls, getattr(self, "_wtotal", 0.0)))
        if os.environ.get("MN_DUMP"):
            with open(os.environ["MN_DUMP"], "a", encoding="utf-8") as fh:
                fh.write("%s\t%d\t%.3f\t%.3f\n" % PAGELOG[-1])
        super().tear_down()

    def head(self, idx, title):
        a = ctext(f"{idx:02d}", size=19, color=ACC)
        b = ctext(title, size=19, color=DIM)
        g = VGroup(a, b).arrange(RIGHT, buff=0.18, aligned_edge=DOWN)
        g.to_corner(UL, buff=0.40)
        self.play(FadeIn(g, shift=DOWN * 0.08), run_time=0.5)
        return g

    def prog(self, idx, n=7):
        y = -3.68
        track = Line(np.array([-6.30, y, 0.0]), np.array([6.30, y, 0.0]),
                     stroke_width=2.0, color=LINE)
        w = 12.60 * idx / n
        fill = Line(np.array([-6.30, y, 0.0]), np.array([-6.30 + w, y, 0.0]),
                    stroke_width=2.0, color=ACC)
        self.add(track)
        self.play(Create(fill), run_time=0.8)


# ================================================================ S1 问题的提出
class S1Intro(Base):
    def body(self):
        self.camera.background_color = BG

        kicker = ctext("函数方程 · 第一讲", size=21, color=ACC)
        kicker.to_corner(UL, buff=0.6)
        title = ctext("柯西函数方程", size=76, color=INK, weight=BOLD)
        title.move_to(UP * 1.95)
        en = Text("The Cauchy Functional Equation", font="Georgia",
                  font_size=23, color=DIM, slant=ITALIC)
        en.next_to(title, DOWN, buff=0.34)

        self.play(FadeIn(kicker, shift=DOWN * 0.12), run_time=0.7)
        self.play(Write(title), run_time=1.5)
        self.play(FadeIn(en, shift=UP * 0.10), run_time=0.8)
        self.wait(1.0)

        eq = mt(r"f(x+y) = f(x) + f(y)", size=84, color=GOLD)
        eq.move_to(DOWN * 1.05)
        self.play(Write(eq), run_time=1.8)
        self.wait(1.3)
        self.play(Circumscribe(eq, color=ACC, buff=0.22), run_time=1.4)
        self.wait(1.0)

        self.wipe(run_time=0.6)

        # ---------------- 页 2：历史与时间线
        era = ctext("1821", size=52, color=GOLD, weight=BOLD)
        era.move_to(LEFT * 4.85 + UP * 2.45)
        hist = ctext("柯西《分析教程》", size=27, color=INK)
        hist.next_to(era, RIGHT, buff=0.6)
        hist2 = ctext("在建立函数概念的严格基础时，他断言解只能是", size=21, color=DIM)
        hist2.next_to(hist, DOWN, buff=0.24).align_to(hist, LEFT)
        hist3 = mt(r"f(x)=c\,x", size=30, color=GOLD)
        hist3.next_to(hist2, RIGHT, buff=0.16)

        self.play(FadeIn(era, shift=RIGHT * 0.2), run_time=0.8)
        self.play(FadeIn(hist, shift=RIGHT * 0.15), run_time=0.7)
        self.play(FadeIn(hist2), FadeIn(hist3), run_time=0.9)
        self.wait(3.0)

        tl = Line(np.array([-5.7, -0.45, 0.0]), np.array([5.7, -0.45, 0.0]),
                  color=LINE, stroke_width=2.4)
        self.play(Create(tl), run_time=1.0)

        marks = [(-4.2, "1821", "柯西：默认了连续性", GOLD),
                 (0.0, "1905", "Hamel：选择公理造出反例", VIOL),
                 (4.2, "1970", "Solovay：反例必须用 AC", ACC)]
        for x, yr, txt, col in marks:
            d = Dot(np.array([x, -0.45, 0.0]), radius=0.06, color=col)
            y1 = ctext(yr, size=22, color=col).next_to(d, UP, buff=0.16)
            t1 = ctext(txt, size=18, color=DIM).next_to(d, DOWN, buff=0.2)
            self.play(FadeIn(d, scale=0.5), FadeIn(y1), FadeIn(t1), run_time=0.7)
            self.wait(1.2)
        self.wait(2.8)

        self.wipe(run_time=0.6)

        # ---------------- 页 3：问题
        q1 = VGroup(ctext("问题：", size=30, color=ACC),
                    ctext("求所有满足该方程的", size=30, color=INK),
                    mt(r"f:\mathbb{R}\to\mathbb{R}", size=36)).arrange(RIGHT, buff=0.22)
        q1.move_to(UP * 1.85)

        q2 = VGroup(ctext("直觉答案：", size=30, color=DIM),
                    mt(r"f(x) = c\,x", size=40, color=GOLD)).arrange(RIGHT, buff=0.22)
        q2.next_to(q1, DOWN, buff=0.6)

        q3 = VGroup(ctext("但这是", size=30, color=INK),
                    ctext("全部", size=32, color=RED, weight=BOLD),
                    ctext("答案吗？", size=30, color=INK)).arrange(RIGHT, buff=0.10)
        q3.next_to(q2, DOWN, buff=0.6)

        self.play(FadeIn(q1, shift=UP * 0.15), run_time=0.9)
        self.wait(2.6)
        self.play(FadeIn(q2, shift=UP * 0.15), run_time=0.9)
        self.wait(2.4)
        self.play(FadeIn(q3, shift=UP * 0.15), run_time=0.9)
        self.play(Circumscribe(q3, color=RED, buff=0.14), run_time=1.2)
        self.wait(2.4)

        rule = Line(np.array([-5.4, -0.55, 0.0]), np.array([5.4, -0.55, 0.0]),
                    color=LINE, stroke_width=1.6)
        q4 = VGroup(ctext("注意：", size=22, color=ACC),
                    ctext("条件里没有任何关于连续、单调、可测的假设", size=22, color=INK),
                    ctext("—— 这是一个纯代数条件", size=22, color=ACC)).arrange(RIGHT, buff=0.06)
        q4.next_to(rule, DOWN, buff=0.3)
        self.play(Create(rule), FadeIn(q4), run_time=1.0)
        self.wait(3.4)

        self.wipe(run_time=0.6)

        # 路线图
        head = ctext("本讲路线", size=26, color=ACC)
        head.to_corner(UL, buff=0.55)
        head.align_to(np.array([-6.2, 0, 0]), LEFT)

        items = [
            ("01", "代数性质", "只靠方程推出 Q-线性"),
            ("02", "正则性", "连续 / 单调 / 有界 → 线性"),
            ("03", "病态解", "Hamel 基与选择公理"),
            ("04", "可测性 · 变体 · 应用", "为什么它如此重要"),
        ]
        rows = VGroup()
        for num, t1, t2 in items:
            a = ctext(num, size=20, color=GOLD)
            b = ctext(t1, size=28, color=INK)
            c = ctext(t2, size=21, color=DIM)
            r = VGroup(a, b).arrange(RIGHT, buff=0.35, aligned_edge=DOWN)
            r2 = VGroup(r, c).arrange(RIGHT, buff=0.5)
            rows.add(r2)
        rows.arrange(DOWN, buff=0.42, aligned_edge=LEFT)
        rows.move_to(DOWN * 0.35 + LEFT * 0.55)

        self.play(FadeIn(head), run_time=0.6)
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.18), run_time=0.6)
            self.wait(0.55)
        self.wait(3.4)


# ================================================================ S2 代数性质
class S2Algebra(Base):
    def body(self):
        self.head(2, "代数性质：方程 = Q-线性")
        self.prog(2)

        # ------------------------------------------------ 页 1：f(0)=0
        t = ctext("先不假设 f 有任何正则性，只反复使用方程本身", size=26, color=DIM)
        t.to_edge(UP, buff=0.85)
        self.play(FadeIn(t), run_time=0.7)

        e0 = mt(r"f(x+y)=f(x)+f(y)", size=42, color=GOLD)
        e0.next_to(t, DOWN, buff=0.42)
        self.play(Write(e0), run_time=1.1)
        self.wait(1.4)

        s1 = VGroup(mt(r"f(0) = f(0+0) = f(0)+f(0)", size=38),
                    ctext("令 x = y = 0", size=20, color=DIM)).arrange(DOWN, buff=0.18)
        s1.next_to(e0, DOWN, buff=0.75)
        self.play(Write(s1[0]), FadeIn(s1[1]), run_time=1.3)
        self.wait(2.2)

        s2 = VGroup(mt(r"f(0) = 0", size=46, color=ACC),
                    ctext("两边减去 f(0)", size=20, color=DIM)).arrange(DOWN, buff=0.18)
        s2.move_to(s1)
        self.play(TransformMatchingTex(s1[0], s2[0]), FadeOut(s1[1]), run_time=1.1)
        self.play(FadeIn(s2[1]), run_time=0.6)
        self.wait(2.6)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 页 2：奇性
        t = ctext("把 x 换成 -x 的搭档：", size=26, color=DIM)
        t.move_to(UP * 2.15)
        self.play(FadeIn(t), run_time=0.6)

        e1 = mt(r"f(x) + f(-x) = f\big(x+(-x)\big) = f(0) = 0", size=36)
        e1.next_to(t, DOWN, buff=0.55)
        self.play(Write(e1), run_time=1.6)
        self.wait(1.4)

        e2 = mt(r"\Longrightarrow\qquad f(-x) = -\,f(x)", size=44, color=ACC)
        e2.next_to(e1, DOWN, buff=0.65)
        self.play(Write(e2), run_time=1.2)
        self.wait(1.2)

        n2 = ctext("所以 f 必是奇函数 —— 这一步只用到了 f(0)=0", size=23, color=DIM)
        n2.next_to(e2, DOWN, buff=0.6)
        self.play(FadeIn(n2), run_time=0.8)
        self.wait(3.0)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 页 3：整数齐性
        t = ctext("第一层：整数倍", size=26, color=GOLD)
        t.to_edge(UP, buff=0.85)
        self.play(FadeIn(t), run_time=0.6)

        a = mt(r"f(nx) = n\,f(x), \qquad n\in\mathbb{N}", size=40)
        a.next_to(t, DOWN, buff=0.5)
        self.play(Write(a), run_time=1.2)
        self.wait(1.0)

        pf = VGroup(
            mt(r"n=1:\quad f(x)=1\cdot f(x)", size=30, color=DIM),
            mt(r"f\big((n+1)x\big) = f(nx) + f(x) = n\,f(x)+f(x) = (n+1)f(x)",
               size=30, color=DIM),
        ).arrange(DOWN, buff=0.32, aligned_edge=LEFT)
        pf.next_to(a, DOWN, buff=0.55).align_to(a, LEFT)
        self.play(FadeIn(pf[0], shift=RIGHT * 0.1), run_time=0.8)
        self.wait(1.0)
        self.play(FadeIn(pf[1], shift=RIGHT * 0.1), run_time=1.0)
        self.wait(2.4)

        b = mt(r"n<0:\quad f(nx) = -f(-nx) = -(-n)f(x) = n\,f(x)", size=32, color=ACC)
        b.next_to(pf, DOWN, buff=0.65).align_to(pf, LEFT)
        self.play(Write(b), run_time=1.3)
        self.wait(1.4)

        c = mt(r"\Longrightarrow\quad f(nx)=n\,f(x), \qquad n\in\mathbb{Z}", size=42, color=GOLD)
        c.next_to(b, DOWN, buff=0.55)
        self.play(Write(c), run_time=1.2)
        self.wait(3.0)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 页 4：有理齐性
        t = ctext("第二层：有理倍 —— 关键是把 x 切成 n 份", size=26, color=GOLD)
        t.to_edge(UP, buff=0.85)
        self.play(FadeIn(t), run_time=0.6)

        d = mt(r"f(x) = f\!\left(n\cdot\frac{x}{n}\right) = n\,f\!\left(\frac{x}{n}\right)",
               size=40)
        d.next_to(t, DOWN, buff=0.5)
        self.play(Write(d), run_time=1.4)
        self.wait(1.2)

        d2 = mt(r"\Longrightarrow\qquad f\!\left(\frac{x}{n}\right) = \frac{1}{n}\,f(x)",
                size=42, color=ACC)
        d2.next_to(d, DOWN, buff=0.55)
        self.play(Write(d2), run_time=1.2)
        self.wait(1.8)

        e = mt(r"f\!\left(\frac{m}{n}\,x\right) = m\,f\!\left(\frac{x}{n}\right) = \frac{m}{n}\,f(x)",
               size=38)
        e.next_to(d2, DOWN, buff=0.65)
        nd = ctext("m ∈ ℤ，n ∈ ℕ：先切份，再复制", size=21, color=DIM)
        nd.next_to(e, DOWN, buff=0.3)
        self.play(Write(e), run_time=1.4)
        self.play(FadeIn(nd), run_time=0.7)
        self.wait(2.4)

        f4 = mt(r"f(q) = c\,q, \qquad q\in\mathbb{Q},\quad c:=f(1)", size=46, color=GOLD)
        f4.next_to(nd, DOWN, buff=0.55)
        self.play(Write(f4), run_time=1.3)
        self.play(Circumscribe(f4, color=GOLD, buff=0.18), run_time=1.4)
        self.wait(3.2)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 页 5：Q-线性
        key1 = VGroup(ctext("于是：满足柯西方程", size=29, color=INK),
                      ctext("当且仅当", size=29, color=ACC),
                      ctext("f 是", size=29, color=INK),
                      mt(r"\mathbb{Q}", size=35, color=ACC),
                      ctext("上的线性映射", size=29, color=INK)).arrange(RIGHT, buff=0.14)
        key1.to_edge(UP, buff=0.85)
        self.play(FadeIn(key1, shift=UP * 0.15), run_time=1.0)

        defn = mt(r"f(q_1x_1 + q_2x_2) = q_1f(x_1) + q_2f(x_2), \qquad q_i\in\mathbb{Q}",
                  size=36, color=ACC)
        defn.next_to(key1, DOWN, buff=0.45)
        self.play(Write(defn), run_time=1.3)
        note = rich(r"把 $\mathbb{R}$ 看成 $\mathbb{Q}$ 上的向量空间：数乘只允许有理数",
                    size=22, color=DIM)
        note.next_to(defn, DOWN, buff=0.28)
        self.play(FadeIn(note), run_time=0.7)
        self.wait(3.0)

        # 图形：有理点被锁死在直线上
        axes = Axes(x_range=[-4.6, 4.6, 1], y_range=[-2.4, 2.4, 1],
                    x_length=7.6, y_length=3.2,
                    axis_config={"color": DIM, "stroke_width": 2,
                                 "include_ticks": False, "tip_width": 0.13,
                                 "tip_height": 0.13})
        axes.move_to(DOWN * 1.95 + LEFT * 2.0)
        lab = VGroup(mt(r"x", size=24, color=DIM), mt(r"f(x)", size=24, color=DIM))
        lab[0].next_to(axes.x_axis.get_right(), RIGHT, buff=0.1)
        lab[1].next_to(axes.y_axis.get_top(), UP, buff=0.1)

        self.play(FadeIn(axes), FadeIn(lab), run_time=1.0)

        cc = 0.45
        glide = DashedLine(axes.c2p(-4.3, cc * -4.3), axes.c2p(4.3, cc * 4.3),
                           color=DIM, stroke_width=1.6, dash_length=0.08)
        dots = VGroup(*[Dot(axes.c2p(k / 2, cc * k / 2), radius=0.042, color=ACC)
                        for k in range(-8, 9)])
        self.play(Create(glide), run_time=0.9)
        self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in dots],
                              lag_ratio=0.06), run_time=2.0)
        self.wait(0.8)

        cap = VGroup(ctext("有理点上的值", size=21, color=DIM),
                     ctext("全部锁死：", size=21, color=DIM),
                     mt(r"f(q)=cq", size=25, color=ACC))
        cap.arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        cap.next_to(axes, RIGHT, buff=0.6)
        self.play(FadeIn(cap), run_time=0.8)
        self.wait(2.0)

        # 无理点：完全自由
        irr = [0.7071, -1.4142, 2.2361, -2.8284, 3.3166, -0.3162]
        rng = np.random.RandomState(7)
        free = VGroup()
        for x0 in irr:
            p = axes.c2p(x0, cc * x0)
            q = axes.c2p(x0, float(np.clip(rng.uniform(-1.7, 1.7), -2.1, 2.1)))
            free.add(Dot(p, radius=0.042, color=DIM),
                     DashedLine(p, q, color=VIOL, stroke_width=1.2, dash_length=0.05),
                     Dot(q, radius=0.048, color=VIOL),
                     mt(r"?", size=22, color=VIOL).next_to(q, RIGHT, buff=0.06))
        self.play(LaggedStart(*[FadeIn(o, scale=0.6) for o in free], lag_ratio=0.1),
                  run_time=2.4)
        cap2 = ctext("无理点上的取值：方程管不着", size=21, color=VIOL)
        cap2.next_to(cap, DOWN, buff=0.35).align_to(cap, LEFT)
        self.play(FadeIn(cap2), run_time=0.8)
        self.wait(3.4)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 页 6：自由度
        l1 = VGroup(rich(r"$\mathbb{R}$ 作为", size=29, color=INK),
                    mt(r"\mathbb{Q}", size=33, color=ACC),
                    ctext("上的向量空间：", size=29, color=INK),
                    ctext("维数无穷", size=31, color=GOLD, weight=BOLD)).arrange(RIGHT, buff=0.10)
        l1.move_to(UP * 1.45)
        self.play(FadeIn(l1, shift=UP * 0.12), run_time=1.0)
        self.wait(2.2)

        l2 = VGroup(ctext("一个解在", size=29, color=INK),
                    mt(r"\mathbb{Q}", size=33, color=ACC),
                    ctext("上定下的信息，", size=29, color=INK),
                    ctext("对无理点毫无约束力", size=29, color=RED)).arrange(RIGHT, buff=0.10)
        l2.next_to(l1, DOWN, buff=0.7)
        self.play(FadeIn(l2, shift=UP * 0.12), run_time=1.0)
        self.wait(2.8)

        q = VGroup(ctext("那么：", size=29, color=DIM),
                   ctext("会不会存在", size=29, color=INK),
                   ctext("不是 c·x", size=29, color=VIOL, weight=BOLD),
                   ctext("的解？", size=29, color=INK)).arrange(RIGHT, buff=0.10)
        q.next_to(l2, DOWN, buff=1.0)
        self.play(FadeIn(q, shift=UP * 0.12), run_time=0.9)
        self.play(Circumscribe(q, color=VIOL, buff=0.16), run_time=1.4)
        self.wait(3.6)


# ================================================================ S3 正则性
class S3Regularity(Base):
    def body(self):
        self.head(3, "正则性：把怪物赶出去")
        self.prog(3)

        # ------------------------------------------------ 页 1：五个等价条件
        tt = ctext("定理（柯西，1821）", size=25, color=GOLD)
        tt.to_corner(UL, buff=0.55).shift(DOWN * 0.38)
        self.play(FadeIn(tt, shift=DOWN * 0.1), run_time=0.7)

        premise = VGroup(ctext("设", size=26, color=INK),
                         mt(r"f:\mathbb{R}\to\mathbb{R}", size=31),
                         ctext("满足", size=26, color=INK),
                         mt(r"f(x+y)=f(x)+f(y)", size=31, color=GOLD),
                         ctext("，则下列条件等价：", size=26, color=INK)).arrange(RIGHT, buff=0.12)
        premise.next_to(tt, DOWN, buff=0.42).align_to(tt, LEFT)
        self.play(FadeIn(premise), run_time=0.9)
        self.wait(1.8)

        items = [
            ("(a)", r"f 在 $\mathbb{R}$ 上连续"),
            ("(b)", "f 在某一点连续"),
            ("(c)", "f 在某个区间上单调"),
            ("(d)", "f 在某个区间上有界"),
        ]
        col_l = VGroup()
        for tag, s in items:
            inner = VGroup(ctext(tag, size=23, color=ACC), rich(s, size=26))
            inner.arrange(RIGHT, buff=0.26)
            col_l.add(inner)
        col_l.arrange(DOWN, buff=0.46, aligned_edge=LEFT)
        col_l.next_to(premise, DOWN, buff=0.5).align_to(premise, LEFT).shift(RIGHT * 0.15)

        for it in col_l:
            self.play(FadeIn(it, shift=RIGHT * 0.15), run_time=0.7)
            self.wait(1.1)

        e_row = VGroup(ctext("(e)", size=23, color=GOLD),
                       mt(r"f(x)=c\,x\quad\text{for all }x", size=31, color=GOLD))
        e_row.arrange(RIGHT, buff=0.26)
        e_row.next_to(col_l, DOWN, buff=0.5).align_to(col_l, LEFT)
        self.play(FadeIn(e_row, shift=RIGHT * 0.15), run_time=0.8)
        self.wait(2.6)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 页 2：(d) ⇒ (b)
        step = VGroup(ctext("关键一步：", size=27, color=ACC),
                      ctext("在一个区间上有界", size=27, color=INK),
                      ctext("→", size=27, color=ACC),
                      ctext("在原点连续", size=27, color=INK)).arrange(RIGHT, buff=0.12)
        step.to_edge(UP, buff=0.85)
        self.play(FadeIn(step), run_time=0.8)

        h1 = mt(r"\exists\, M>0,\ \delta>0:\quad |f(t)|\le M \quad \text{whenever } |t|<\delta",
                size=33)
        h1.next_to(step, DOWN, buff=0.42)
        self.play(Write(h1), run_time=1.3)
        self.wait(2.0)

        lines = [
            (r"\varepsilon>0\ \Longrightarrow\ \exists\,n\in\mathbb{N}:\ \ \frac{M}{n}<\varepsilon",
             None),
            (r"|x|<\frac{\delta}{n}\ \Longrightarrow\ |t|:=|nx|<\delta", None),
            (r"f(t)=f(nx)=n\,f(x)\ \Longrightarrow\ |f(x)| \le \frac{M}{n} < \varepsilon",
             "ACC"),
        ]
        group = VGroup()
        for tex, col in lines:
            group.add(mt(tex, size=32, color=ACC if col else INK))
        group.arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        group.next_to(h1, DOWN, buff=0.55).align_to(h1, LEFT)

        for o in group:
            self.play(Write(o), run_time=1.3)
            self.wait(1.4)

        concl = VGroup(ctext("任给 ε，取 n 把 x 缩进 δ/n；", size=24, color=DIM),
                       ctext("这正是", size=24, color=DIM),
                       mt(r"f(x)\to f(0)=0", size=29, color=ACC),
                       ctext("，即 f 在 0 点连续", size=24, color=INK)).arrange(RIGHT, buff=0.1)
        concl.next_to(group, DOWN, buff=0.6)
        self.play(FadeIn(concl, shift=UP * 0.1), run_time=0.9)
        self.wait(3.0)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 页 3：一点连续 → 处处连续
        s2 = VGroup(ctext("① 一点连续", size=27, color=ACC),
                    ctext("→", size=27, color=DIM),
                    ctext("处处连续", size=27, color=INK)).arrange(RIGHT, buff=0.12)
        s2.to_edge(UP, buff=0.85)
        self.play(FadeIn(s2), run_time=0.7)
        e2 = mt(r"f(x+h)-f(x) = f(h) \longrightarrow 0 \qquad (h\to 0)", size=34)
        e2.next_to(s2, DOWN, buff=0.42)
        self.play(Write(e2), run_time=1.3)
        self.wait(2.4)

        s3 = VGroup(ctext("② 连续", size=27, color=ACC),
                    ctext("→", size=27, color=DIM),
                    ctext("用有理数逼近", size=27, color=INK)).arrange(RIGHT, buff=0.12)
        s3.next_to(e2, DOWN, buff=0.85)
        self.play(FadeIn(s3), run_time=0.7)

        e3 = mt(r"q_n\in\mathbb{Q},\qquad q_n\to x", size=32)
        e3.next_to(s3, DOWN, buff=0.35)
        self.play(Write(e3), run_time=0.9)
        e3b = mt(r"\Longrightarrow\quad f(x)=\lim_{n\to\infty}f(q_n)"
                 r"=\lim_{n\to\infty}c\,q_n=c\,x", size=32, color=ACC)
        e3b.next_to(e3, DOWN, buff=0.3)
        self.play(Write(e3b), run_time=1.4)
        self.wait(2.0)

        # 数轴演示
        nl = NumberLine(x_range=[0, 2, 0.5], length=7.6, color=DIM,
                        include_numbers=True, font_size=20,
                        tick_size=0.05, stroke_width=2.2)
        nl.move_to(DOWN * 2.55)
        tgt = nl.n2p(1.4142135)
        mark = DashedLine(tgt + UP * 0.45, tgt + DOWN * 0.12, color=GOLD,
                          stroke_width=1.6, dash_length=0.06)
        mlabel = mt(r"x", size=26, color=GOLD).next_to(mark, UP, buff=0.08)
        self.play(FadeIn(nl), run_time=0.8)
        self.play(Create(mark), FadeIn(mlabel), run_time=0.7)

        approx = [1.0, 1.5, 1.4, 1.42, 1.414, 1.4142]
        dots = VGroup()
        for qv in approx:
            dots.add(Dot(nl.n2p(qv), radius=0.05, color=ACC))
        self.play(LaggedStart(*[FadeIn(d, scale=0.6) for d in dots], lag_ratio=0.22),
                  run_time=2.2)
        qlab = VGroup(mt(r"q_1", size=20, color=DIM), mt(r"q_2", size=20, color=DIM),
                      mt(r"q_3", size=20, color=DIM))
        self.wait(2.6)

        final = mt(r"f(x) = c\,x \qquad \text{for all } x\in\mathbb{R}", size=44, color=GOLD)
        final.next_to(e3b, DOWN, buff=0.75)
        self.play(Write(final), run_time=1.4)
        self.play(Circumscribe(final, color=GOLD, buff=0.18), run_time=1.3)
        self.wait(3.0)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 页 4：等价链条
        hd = ctext("五个条件，其实是同一个条件的五种说法", size=27, color=INK)
        hd.to_edge(UP, buff=0.9)
        self.play(FadeIn(hd), run_time=0.8)
        self.wait(1.0)

        labels = [ctext("区间上单调", size=20), ctext("区间上有界", size=20),
                  ctext("一点连续", size=20), ctext("处处连续", size=20),
                  mt(r"f(x)=c\,x", size=26, color=GOLD)]
        cols = [ACC, ACC, ACC, ACC, GOLD]
        boxes = VGroup()
        for lb, col in zip(labels, cols):
            w = max(1.95, lb.width + 0.42)
            b = card(lb, width=w, height=0.78, color=col, fill=BOXBG)
            boxes.add(b)
        boxes.arrange(RIGHT, buff=0.75)
        boxes.move_to(UP * 1.0)
        if boxes.width > 13.0:
            boxes.scale_to_fit_width(13.0)

        for b in boxes:
            self.play(FadeIn(b, scale=0.92), run_time=0.45)
        self.wait(1.2)

        for i in range(4):
            s = boxes[i].get_right() + RIGHT * 0.04
            e = boxes[i + 1].get_left() + LEFT * 0.04
            ar = Arrow(s, e, buff=0.0, stroke_width=2.2, color=DIM,
                       max_tip_length_to_length_ratio=0.3)
            self.play(Create(ar), run_time=0.5)
            self.wait(0.25)
        self.wait(1.2)

        legs = VGroup(
            ctext("① 单调 → 端点界住", size=21, color=DIM),
            ctext("② 有界 → ε-δ 缩放", size=21, color=DIM),
            ctext("③ 连续 → 平移", size=21, color=DIM),
            ctext("④ 连续 → 有理逼近", size=21, color=DIM),
        )
        legs.arrange(RIGHT, buff=0.7)
        legs.move_to(DOWN * 0.15)
        if legs.width > 13.2:
            legs.scale_to_fit_width(13.2)
        for lg in legs:
            self.play(FadeIn(lg, shift=UP * 0.08), run_time=0.55)
            self.wait(0.35)
        self.wait(1.4)

        note = VGroup(ctext("反向全部显然：", size=19, color=DIM),
                      mt(r"(e)\Rightarrow(a)\Rightarrow(b)\Rightarrow(d)\Rightarrow(c)",
                         size=24, color=DIM))
        note.arrange(RIGHT, buff=0.24)
        note.move_to(DOWN * 1.35)
        self.play(FadeIn(note), run_time=0.8)
        self.wait(2.2)

        gap = ctext("注意：这五条是「加在柯西方程上的额外假设」，不是方程本身能推出的",
                    size=22, color=RED)
        gap.next_to(note, DOWN, buff=0.75)
        self.play(FadeIn(gap, shift=UP * 0.08), run_time=0.9)
        self.wait(3.6)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 页 5：更弱的正则性
        t = ctext("正则性还能再弱一点吗？", size=28, color=GOLD)
        t.to_edge(UP, buff=0.9)
        self.play(FadeIn(t), run_time=0.8)
        self.wait(1.2)

        rows = [
            ("Lebesgue 可测", "即可（第 5 节给出证明）", ACC),
            ("在一个正测度集上有界", "Sierpiński, 1920", ACC),
            ("f 是某个可测函数的导数", "自动线性", BLUE),
            ("f 在每点附近不取极大值", "仍然线性", BLUE),
        ]
        g = VGroup()
        for a_, b_, col in rows:
            left = ctext(a_, size=23, color=INK)
            right = ctext(b_, size=20, color=col)
            g.add(VGroup(left, right).arrange(RIGHT, buff=0.45))
        g.arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        g.next_to(t, DOWN, buff=0.6).align_to(t, LEFT).shift(LEFT * 0.55)

        for r in g:
            self.play(FadeIn(r, shift=RIGHT * 0.15), run_time=0.7)
            self.wait(1.5)

        self.wait(2.5)


# ================================================================ S4 Hamel 基
class S4Hamel(Base):
    def body(self):
        self.head(4, "病态解：Hamel 基")
        self.prog(4)

        # ------------------------------------------------ 页 1：问题重述
        t = VGroup(ctext("去掉连续性，", size=30, color=INK),
                   ctext("方程还有别的解吗？", size=30, color=VIOL, weight=BOLD)).arrange(RIGHT, buff=0.1)
        t.move_to(UP * 2.6)
        self.play(FadeIn(t), run_time=0.9)
        self.wait(1.8)

        new = VGroup(ctext("关键转译：", size=27, color=ACC),
                     rich(r"把 $\mathbb{R}$ 看成", size=27, color=INK),
                     mt(r"\mathbb{Q}", size=32, color=ACC),
                     ctext("上的向量空间", size=27, color=INK)).arrange(RIGHT, buff=0.10)
        new.next_to(t, DOWN, buff=0.75)
        self.play(FadeIn(new), run_time=0.8)
        self.wait(2.2)

        d1 = ctext("允许的「数乘」只有有理数，允许的「加法」还是实数加法", size=22, color=DIM)
        d1.next_to(new, DOWN, buff=0.32)
        self.play(FadeIn(d1), run_time=0.7)
        self.wait(2.4)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 页 2：基的存在与构造
        s1 = VGroup(ctext("Zorn 引理", size=26, color=GOLD),
                    ctext("保证存在一组", size=26, color=INK),
                    ctext("Hamel 基", size=28, color=ACC, weight=BOLD)).arrange(RIGHT, buff=0.15)
        s1.move_to(UP * 3.0)
        self.play(FadeIn(s1), run_time=0.8)
        self.wait(1.2)

        s2 = mt(r"x = q_1b_1 + q_2b_2 + \cdots + q_kb_k, \qquad q_i\in\mathbb{Q},\ b_i\in B",
                size=36)
        s2.next_to(s1, DOWN, buff=0.45)
        self.play(Write(s2), run_time=1.4)
        n2 = rich(r"表示唯一（B 是 $\mathbb{Q}$-线性无关的极大族）", size=21, color=DIM)
        n2.next_to(s2, DOWN, buff=0.25)
        self.play(FadeIn(n2), run_time=0.7)
        self.wait(2.4)

        # 构造
        box = VGroup()
        st = ctext("构造", size=22, color=GOLD)
        phi = mt(r"\varphi:B\to\mathbb{R}", size=33)
        any_ = ctext("任意指定每个基元素的像", size=21, color=DIM)
        then = VGroup(ctext("令", size=24, color=INK),
                      mt(r"f\!\left(\sum_i q_ib_i\right) := \sum_i q_i\,\varphi(b_i)", size=34))
        then.arrange(RIGHT, buff=0.18)
        chk = VGroup(ctext("则", size=24, color=DIM),
                     mt(r"f(x+y)=f(x)+f(y)", size=30, color=ACC),
                     ctext("自动成立", size=22, color=DIM)).arrange(RIGHT, buff=0.15)
        inner = VGroup(st, VGroup(phi, any_).arrange(RIGHT, buff=0.45), then, chk)
        inner.arrange(DOWN, buff=0.38)
        frame = RoundedRectangle(corner_radius=0.16, width=9.6, height=inner.height + 0.7,
                                 stroke_color=ACC, stroke_width=1.6,
                                 fill_color=BOXBG, fill_opacity=0.85)
        frame.move_to(inner)
        box.add(frame, inner)
        box.move_to(DOWN * 0.95)
        self.play(FadeIn(box, scale=0.95), run_time=1.1)
        self.wait(3.0)

        # 一一对应
        bij = VGroup(ctext("反过来，f 在基上的值决定了整个 f：", size=23, color=DIM),
                     rich(r"解空间 $\cong$", size=23, color=INK),
                     mt(r"\mathbb{R}^{B}", size=30, color=GOLD)).arrange(RIGHT, buff=0.15)
        bij.next_to(box, DOWN, buff=0.45)
        self.play(FadeIn(bij), run_time=0.8)
        self.wait(3.0)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 页 3：显式反例
        tt = ctext("取一个具体的基元组合", size=28, color=INK)
        tt.move_to(UP * 3.1)
        self.play(FadeIn(tt), run_time=0.7)

        e1 = VGroup(ctext("基中含", size=26, color=INK),
                    mt(r"1", size=34, color=ACC),
                    ctext("与", size=26, color=INK),
                    mt(r"\sqrt{2}", size=34, color=ACC)).arrange(RIGHT, buff=0.16)
        e2 = VGroup(ctext("令", size=26, color=INK),
                    mt(r"\varphi(1)=0,\quad \varphi(\sqrt2)=1", size=34),
                    ctext("，其余基元取 0", size=24, color=DIM)).arrange(RIGHT, buff=0.16)
        e3 = mt(r"\Longrightarrow\quad f(m+n\sqrt2) = n, \qquad m,n\in\mathbb{Z}", size=36)
        grp = VGroup(e1, e2, e3).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        grp.next_to(tt, DOWN, buff=0.5).align_to(tt, LEFT).shift(RIGHT * 0.2)
        for o in grp:
            self.play(FadeIn(o, shift=RIGHT * 0.12), run_time=0.8)
            self.wait(1.2)

        e4 = VGroup(ctext("于是", size=26, color=DIM),
                    mt(r"f(1)=0", size=34, color=RED),
                    ctext("但", size=26, color=DIM),
                    mt(r"f(\sqrt2)=1", size=34, color=RED)).arrange(RIGHT, buff=0.16)
        e4.next_to(grp, DOWN, buff=0.55)
        self.play(FadeIn(e4), run_time=0.9)
        self.wait(1.6)

        e5 = VGroup(ctext("若", size=24, color=DIM),
                    mt(r"f(x)=cx", size=30, color=DIM),
                    ctext("则", size=24, color=DIM),
                    mt(r"c=f(1)=0", size=30, color=DIM),
                    ctext("，与", size=24, color=DIM),
                    mt(r"f(\sqrt2)=1", size=30, color=DIM),
                    ctext("矛盾", size=24, color=RED, weight=BOLD)).arrange(RIGHT, buff=0.12)
        e5.next_to(e4, DOWN, buff=0.5)
        self.play(FadeIn(e5), run_time=0.9)
        self.play(Circumscribe(e5, color=RED, buff=0.14), run_time=1.4)
        self.wait(3.4)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 页 4：图像
        axes = Axes(x_range=[-5.2, 5.2, 1], y_range=[-2.8, 2.8, 1],
                    x_length=8.6, y_length=4.6,
                    axis_config={"color": DIM, "stroke_width": 2,
                                 "include_ticks": False, "tip_width": 0.14,
                                 "tip_height": 0.14})
        axes.move_to(LEFT * 2.6 + DOWN * 0.35)
        self.play(FadeIn(axes), run_time=0.9)

        pts = VGroup()
        for n in range(-2, 3):
            for m in range(-55, 56):
                x = m + n * np.sqrt(2)
                if abs(x) <= 5.0:
                    pts.add(Dot(axes.c2p(x, n), radius=0.028, color=ACC if n else GOLD))
        self.play(LaggedStart(*[FadeIn(p, scale=0.4) for p in pts], lag_ratio=0.004),
                  run_time=2.6)
        self.wait(1.4)

        side = VGroup(
            ctext("在 span{1, √2} 上：", size=22, color=ACC),
            ctext("图像落在无穷多条水平线上", size=22, color=INK),
            ctext("补满整个 Hamel 基之后，", size=22, color=VIOL),
            ctext("图像在平面上稠密", size=22, color=VIOL, weight=BOLD),
        ).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        side.next_to(axes, RIGHT, buff=0.55)
        for s in side:
            self.play(FadeIn(s, shift=RIGHT * 0.1), run_time=0.6)
            self.wait(0.6)
        self.wait(2.6)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 页 5：病态性质
        hd = ctext("病态解的性质", size=30, color=VIOL, weight=BOLD)
        hd.move_to(UP * 3.0)
        self.play(FadeIn(hd), run_time=0.7)

        props = [
            ("无处连续", "不连续于任何一点"),
            ("每区间无界", "在任何非空开区间上无界"),
            ("图像稠密", r"在 $\mathbb{R}^2$ 中稠密，无法作图"),
            ("不可测", "不是 Lebesgue 可测函数"),
        ]
        g = VGroup()
        for a_, b_ in props:
            d = Dot(radius=0.05, color=VIOL)
            t1 = ctext(a_, size=25, color=INK)
            t2 = rich(b_, size=21, color=DIM)
            row = VGroup(d, t1, t2).arrange(RIGHT, buff=0.35, aligned_edge=DOWN)
            g.add(row)
        g.arrange(DOWN, buff=0.55, aligned_edge=LEFT)
        g.next_to(hd, DOWN, buff=0.55).align_to(hd, LEFT).shift(RIGHT * 0.1)

        for row in g:
            self.play(FadeIn(row, shift=RIGHT * 0.15), run_time=0.7)
            self.wait(1.4)

        self.wait(2.0)

        # 稠密性证明要点
        self.wipe(run_time=0.6)
        pr = ctext("为什么图像稠密？", size=27, color=GOLD)
        pr.move_to(UP * 2.95)
        self.play(FadeIn(pr), run_time=0.7)

        pf = VGroup(
            VGroup(ctext("若 f 不连续，则它在每个", size=22, color=INK),
                   mt(r"(-\delta,\delta)", size=28),
                   ctext("上无界", size=22, color=INK)).arrange(RIGHT, buff=0.12),
            VGroup(ctext("取 u 使", size=22, color=INK),
                   mt(r"|u|<\varepsilon", size=28, color=ACC),
                   ctext("而", size=22, color=INK),
                   mt(r"|f(u)|", size=28, color=ACC),
                   ctext("足够大", size=22, color=INK)).arrange(RIGHT, buff=0.12),
            VGroup(ctext("则", size=22, color=INK),
                   mt(r"f(x_0+qu) = f(x_0) + q\,f(u),\qquad q\in\mathbb{Q}",
                      size=30)).arrange(RIGHT, buff=0.2),
            VGroup(ctext("x 几乎不动，而纵坐标可以扫过任意高度", size=22, color=VIOL)).arrange(RIGHT),
        )
        pf.arrange(DOWN, buff=0.42, aligned_edge=LEFT)
        pf.next_to(pr, DOWN, buff=0.55).align_to(pr, LEFT).shift(LEFT * 1.0)
        for o in pf:
            self.play(FadeIn(o, shift=RIGHT * 0.12), run_time=0.8)
            self.wait(1.5)
        self.wait(3.0)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 页 6：选择公理
        ac = VGroup(ctext("Hamel 基的存在性本质上用到", size=28, color=INK),
                    ctext("选择公理", size=30, color=GOLD, weight=BOLD)).arrange(RIGHT, buff=0.12)
        ac.move_to(UP * 2.1)
        self.play(FadeIn(ac), run_time=0.9)
        self.wait(1.8)

        sl = VGroup(
            ctext("Solovay (1970)：在 ZF + DC +「所有集合可测」的模型中，", size=23, color=DIM),
            VGroup(ctext("每个解都必须是", size=23, color=DIM),
                   mt(r"f(x)=cx", size=30, color=ACC)).arrange(RIGHT, buff=0.14),
        ).arrange(DOWN, buff=0.28)
        sl.next_to(ac, DOWN, buff=0.6)
        self.play(FadeIn(sl), run_time=0.9)
        self.wait(2.6)

        cc = ctext("病态解不是「我们还没找到」，而是「必须有选择公理才存在」", size=26, color=VIOL)
        cc.next_to(sl, DOWN, buff=0.75)
        self.play(FadeIn(cc, shift=UP * 0.1), run_time=0.9)
        self.play(Circumscribe(cc, color=VIOL, buff=0.16), run_time=1.4)
        self.wait(3.8)


# ================================================================ S5 可测性
class S5Measurable(Base):
    def body(self):
        self.head(5, "可测性：积分给出的强制线性")
        self.prog(5)

        thm = VGroup(ctext("定理", size=26, color=GOLD),
                     ctext("若 f 满足柯西方程且 Lebesgue 可测，则", size=26, color=INK),
                     mt(r"f(x)=c\,x", size=32, color=GOLD)).arrange(RIGHT, buff=0.2)
        thm.move_to(UP * 3.0)
        self.play(FadeIn(thm), run_time=0.9)
        self.wait(2.0)

        s1 = VGroup(ctext("思路：", size=24, color=ACC),
                    ctext("把 f 积分一次，", size=24, color=INK),
                    ctext("用积分的光滑性换掉 f 的野性", size=24, color=INK)).arrange(RIGHT, buff=0.1)
        s1.next_to(thm, DOWN, buff=0.55)
        self.play(FadeIn(s1), run_time=0.8)
        self.wait(2.0)

        F = mt(r"F(x) := \int_0^x f(t)\,dt", size=42, color=ACC)
        F.next_to(s1, DOWN, buff=0.6)
        self.play(Write(F), run_time=1.3)
        nF = ctext("f 可测有界地局部可积，F 连续；且 F 几乎处处可微", size=21, color=DIM)
        nF.next_to(F, DOWN, buff=0.3)
        self.play(FadeIn(nF), run_time=0.7)
        self.wait(2.8)

        self.wipe(run_time=0.6)

        # 计算
        calc = VGroup(
            mt(r"F(x+y) = F(x) + \int_0^{y}\!f(t+x)\,dt", size=33),
            mt(r"= F(x) + \int_0^{y}\!\big[f(t)+f(x)\big]dt = F(x)+F(y)+y\,f(x)",
               size=31, color=GOLD),
        ).arrange(DOWN, buff=0.42, aligned_edge=LEFT)
        calc.move_to(UP * 2.55)

        hd = ctext("第一步：把区间拆开，再平移积分变量", size=24, color=ACC)
        hd.next_to(calc, UP, buff=0.45).align_to(calc, LEFT)
        self.play(FadeIn(hd), run_time=0.7)
        self.play(Write(calc[0]), run_time=1.5)
        self.wait(0.8)
        self.play(Write(calc[1]), run_time=1.6)
        self.wait(2.4)

        sym = VGroup(ctext("第二步：", size=24, color=ACC),
                     ctext("x 与 y 的地位对称，再算一遍", size=24, color=INK)).arrange(RIGHT, buff=0.1)
        sym.next_to(calc, DOWN, buff=0.6).align_to(calc, LEFT)
        self.play(FadeIn(sym), run_time=0.8)

        e2 = mt(r"F(x+y) = F(y)+F(x)+x\,f(y)", size=33)
        e2.next_to(sym, DOWN, buff=0.35).align_to(sym, LEFT).shift(RIGHT * 0.4)
        self.play(Write(e2), run_time=1.2)
        self.wait(1.4)

        e3 = mt(r"\Longrightarrow\quad y\,f(x) = x\,f(y) \qquad \text{for all } x,y",
                size=38, color=GOLD)
        e3.next_to(e2, DOWN, buff=0.55)
        self.play(Write(e3), run_time=1.4)
        self.wait(1.6)

        e4 = mt(r"\Longrightarrow\quad \frac{f(x)}{x} = \frac{f(y)}{y} = c \ \ (x,y\neq 0)"
                r"\quad\Longrightarrow\quad f(x)=c\,x", size=34, color=GOLD)
        e4.next_to(e3, DOWN, buff=0.5)
        self.play(Write(e4), run_time=1.6)
        self.wait(1.4)

        rm = ctext("（再用 f 连续于 0 补上 x = 0 一点）", size=20, color=DIM)
        rm.next_to(e4, DOWN, buff=0.3)
        self.play(FadeIn(rm), run_time=0.6)
        self.wait(3.0)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 另一条路 + 推论
        hd = ctext("另一条证明路线：把「可测」翻译成「有界」", size=27, color=INK)
        hd.move_to(UP * 3.0)
        self.play(FadeIn(hd), run_time=0.8)

        route = VGroup(
            VGroup(ctext("f 可测", size=24, color=BLUE),
                   ctext("→", size=26, color=DIM),
                   ctext("存在正测度集 E 使 f 在 E 上有界", size=23, color=INK)).arrange(RIGHT, buff=0.2),
            VGroup(ctext("Steinhaus：", size=23, color=DIM),
                   mt(r"E-E", size=26, color=ACC),
                   ctext("包含一个区间", size=23, color=INK)).arrange(RIGHT, buff=0.2),
            VGroup(ctext("→ f 在某个区间上有界 → 由 S3 得", size=23, color=INK),
                   mt(r"f(x)=c\,x", size=28, color=GOLD)).arrange(RIGHT, buff=0.2),
        )
        route.arrange(DOWN, buff=0.55, aligned_edge=LEFT)
        route.next_to(hd, DOWN, buff=0.6).align_to(hd, LEFT).shift(LEFT * 0.6)
        for o in route:
            self.play(FadeIn(o, shift=RIGHT * 0.12), run_time=0.9)
            self.wait(1.5)

        self.wait(2.0)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 页：为什么可测就够
        hd = ctext("为什么「可测」这么强？", size=28, color=GOLD)
        hd.move_to(UP * 3.0)
        self.play(FadeIn(hd), run_time=0.8)
        self.wait(1.2)

        p1 = rich(r"测度是平移不变的：$\mu(E+t)=\mu(E)$", size=24, color=INK)
        p1.next_to(hd, DOWN, buff=0.45)
        self.play(FadeIn(p1), run_time=0.8)
        self.wait(2.0)

        nl = NumberLine(x_range=[-3.4, 3.4, 1], length=9.2, color=DIM,
                        include_numbers=False, stroke_width=2.2)
        nl.move_to(DOWN * 0.55)
        self.play(FadeIn(nl), run_time=0.7)

        E = Rectangle(width=1.8, height=0.15, stroke_width=0,
                      fill_color=BLUE, fill_opacity=0.8)
        E.move_to(np.array([nl.n2p(-1.1)[0], nl.n2p(0)[1], 0.0]))
        elb = ctext("E", size=22, color=BLUE).next_to(E, UP, buff=0.16)
        self.play(FadeIn(E), FadeIn(elb), run_time=0.8)
        self.wait(1.0)

        E2 = E.copy().set_fill(VIOL, 0.8)
        e2lb = ctext("E + t", size=22, color=VIOL).next_to(E2, UP, buff=0.16).shift(DOWN * 1.6)
        e2lb.next_to(E2, DOWN, buff=0.16)
        self.play(FadeIn(E2), FadeIn(e2lb), run_time=0.6)
        self.play(E2.animate.shift(RIGHT * 1.1), e2lb.animate.shift(RIGHT * 1.1),
                  run_time=1.8)

        x1 = max(E.get_left()[0], E2.get_left()[0])
        x2 = min(E.get_right()[0], E2.get_right()[0])
        ov = Rectangle(width=max(0.02, x2 - x1), height=0.15, stroke_width=0,
                       fill_color=GOLD, fill_opacity=1.0)
        ov.move_to(np.array([(x1 + x2) / 2, E.get_center()[1], 0.0]))
        self.play(FadeIn(ov), run_time=0.6)
        self.wait(1.0)

        p2 = ctext("相交，就有 t ∈ E - E；Steinhaus 引理：E - E 含一个以 0 为中心的区间",
                   size=23, color=ACC)
        p2.next_to(nl, DOWN, buff=0.85)
        self.play(FadeIn(p2), run_time=0.9)
        self.wait(2.4)

        p3 = VGroup(ctext("于是", size=23, color=DIM),
                    mt(r"f", size=26, color=ACC),
                    ctext("在这个区间上有界，由 S3 的定理即得", size=23, color=DIM),
                    mt(r"f(x)=c\,x", size=28, color=GOLD)).arrange(RIGHT, buff=0.12)
        p3.next_to(p2, DOWN, buff=0.4)
        self.play(FadeIn(p3), run_time=0.9)
        self.wait(3.4)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 页：结论
        cor = ctext("推论：病态解不可测，因此既画不出来，也构造不出来", size=27, color=VIOL)
        cor.move_to(UP * 0.75)
        self.play(FadeIn(cor, shift=UP * 0.1), run_time=0.9)
        self.play(Circumscribe(cor, color=VIOL, buff=0.14), run_time=1.3)
        self.wait(1.8)

        cor2 = ctext("连续性、单调性、有界性、可测性 —— 四种「足够好」，同一个结论", size=23,
                     color=DIM)
        cor2.next_to(cor, DOWN, buff=0.6)
        self.play(FadeIn(cor2), run_time=0.9)
        self.wait(3.4)


# ================================================================ S6 变体
class S6Variants(Base):
    def body(self):
        self.head(6, "变体：同一个方程的五张面孔")
        self.prog(6)

        tt = ctext("柯西方程是「同态方程」的原型", size=27, color=INK)
        tt.move_to(UP * 3.0)
        self.play(FadeIn(tt), run_time=0.8)
        self.wait(1.4)

        # ---- 卡片 1：指数型
        eq = mt(r"f(x+y) = f(x)\,f(y)", size=40, color=GOLD)
        eq.move_to(UP * 2.05 + LEFT * 3.3)
        lb = ctext("指数型", size=23, color=ACC)
        lb.next_to(eq, UP, buff=0.25)

        step1 = mt(r"f(x) = f\!\left(\tfrac{x}{2}\right)^2 > 0", size=30)
        step1.next_to(eq, RIGHT, buff=0.65)
        lab1 = ctext("非零解必为正", size=19, color=DIM).next_to(step1, RIGHT, buff=0.3)

        self.play(FadeIn(lb), Write(eq), run_time=1.3)
        self.wait(1.2)
        self.play(Write(step1), FadeIn(lab1), run_time=1.2)
        self.wait(1.6)

        step2 = mt(r"g:=\ln f\ \Longrightarrow\ g(x+y)=g(x)+g(y)", size=30, color=ACC)
        step2.next_to(step1, DOWN, buff=0.45).align_to(step1, LEFT)
        self.play(Write(step2), run_time=1.3)
        step3 = VGroup(ctext("f 连续（或单调）→", size=22, color=DIM),
                       mt(r"f(x)=a^{x}", size=34, color=GOLD)).arrange(RIGHT, buff=0.2)
        step3.next_to(step2, DOWN, buff=0.45).align_to(step2, LEFT)
        self.play(FadeIn(step3), run_time=0.9)
        self.wait(3.2)

        self.wipe(run_time=0.6)

        # ---- 卡片 2：对数型
        eq = mt(r"f(xy) = f(x) + f(y), \qquad x,y>0", size=40, color=GOLD)
        eq.move_to(UP * 2.05 + LEFT * 2.9)
        lb = ctext("对数型", size=23, color=ACC)
        lb.next_to(eq, UP, buff=0.25)
        self.play(FadeIn(lb), Write(eq), run_time=1.3)
        self.wait(1.2)

        t2 = mt(r"h(u) := f(e^{u})\ \Longrightarrow\ h(u+v)=h(u)+h(v)", size=30, color=ACC)
        t2.next_to(eq, DOWN, buff=0.5).align_to(eq, LEFT)
        self.play(Write(t2), run_time=1.3)
        t3 = VGroup(ctext("f 连续 →", size=22, color=DIM),
                    mt(r"f(x)=c\,\ln x", size=34, color=GOLD)).arrange(RIGHT, buff=0.2)
        t3.next_to(t2, DOWN, buff=0.45).align_to(t2, LEFT)
        self.play(FadeIn(t3), run_time=0.9)
        self.wait(2.0)
        t4 = ctext("没有正则性时：f = c·L，L 可以是任意「野」的加法函数复合对数", size=21, color=DIM)
        t4.next_to(t3, DOWN, buff=0.4).align_to(t3, LEFT)
        self.play(FadeIn(t4), run_time=0.8)
        self.wait(3.0)

        self.wipe(run_time=0.6)

        # ---- 卡片 3：中点型
        eq = mt(r"f(x+y)+f(x-y)=2f(x)", size=40, color=GOLD)
        eq.move_to(UP * 2.35)
        lb = ctext("中点型 / Jensen", size=23, color=ACC)
        lb.next_to(eq, UP, buff=0.25)
        self.play(FadeIn(lb), Write(eq), run_time=1.3)
        self.wait(1.2)

        d1 = VGroup(ctext("令", size=22, color=DIM),
                    mt(r"g=f-f(0)", size=30),
                    ctext("，取", size=22, color=DIM),
                    mt(r"y=x", size=30),
                    ctext("得", size=22, color=DIM),
                    mt(r"g(2x)=2g(x)", size=30, color=ACC)).arrange(RIGHT, buff=0.14)
        d1.next_to(eq, DOWN, buff=0.5)
        self.play(FadeIn(d1), run_time=1.0)
        d2 = mt(r"g(x)+g(y) = 2g\!\left(\frac{x+y}{2}\right) = g(x+y)", size=31, color=ACC)
        d2.next_to(d1, DOWN, buff=0.4)
        self.play(Write(d2), run_time=1.3)
        d3 = VGroup(ctext("所以它和柯西方程", size=22, color=INK),
                    ctext("完全等价", size=24, color=GOLD, weight=BOLD),
                    ctext("：解为", size=22, color=INK),
                    mt(r"f(x)=A(x)+f(0)", size=30, color=GOLD)).arrange(RIGHT, buff=0.12)
        d3.next_to(d2, DOWN, buff=0.45)
        self.play(FadeIn(d3), run_time=1.0)
        self.wait(2.6)
        d4 = ctext("连续时退化为一次函数 f(x) = ax + d", size=23, color=DIM)
        d4.next_to(d3, DOWN, buff=0.4)
        self.play(FadeIn(d4), run_time=0.8)
        self.wait(3.2)

        self.wipe(run_time=0.6)

        # ---- 卡片 4：幂函数型
        eq = mt(r"f(xy) = f(x)\,f(y), \qquad x,y>0", size=40, color=GOLD)
        eq.move_to(UP * 2.35)
        lb = ctext("幂函数型", size=23, color=ACC)
        lb.next_to(eq, UP, buff=0.25)
        self.play(FadeIn(lb), Write(eq), run_time=1.3)
        self.wait(1.2)

        q1 = mt(r"f(x) = f\big(e^{\ln x}\big)\ \Longrightarrow\ h(u):=f(e^{u}),\ \ h(u+v)=h(u)\,h(v)",
                size=30, color=ACC)
        q1.next_to(eq, DOWN, buff=0.55)
        self.play(Write(q1), run_time=1.4)
        self.wait(1.4)

        q2 = VGroup(ctext("连续 →", size=22, color=DIM),
                    mt(r"h(u)=a^{u}", size=30, color=GOLD),
                    ctext("→", size=24, color=DIM),
                    mt(r"f(x)=a^{\ln x}=x^{\ln a}", size=30, color=GOLD)).arrange(RIGHT, buff=0.22)
        q2.next_to(q1, DOWN, buff=0.5)
        self.play(FadeIn(q2), run_time=1.0)
        self.wait(2.4)

        q3 = ctext("于是 a^x、log、x^α 三族函数，都只是同一个方程的三种连续解", size=22, color=DIM)
        q3.next_to(q2, DOWN, buff=0.55)
        self.play(FadeIn(q3), run_time=0.9)
        self.wait(1.6)

        q4 = VGroup(ctext("凸性版本：", size=22, color=ACC),
                    ctext("f 满足柯西方程且在区间上凸", size=22, color=INK),
                    ctext("→", size=22, color=DIM),
                    ctext("f 线性", size=22, color=GOLD)).arrange(RIGHT, buff=0.12)
        q4.next_to(q3, DOWN, buff=0.5)
        self.play(FadeIn(q4), run_time=0.9)
        self.wait(3.0)

        self.wipe(run_time=0.6)

        # ---- 总结表
        hd = ctext("一张表收尾", size=28, color=INK)
        hd.move_to(UP * 3.05)
        self.play(FadeIn(hd), run_time=0.7)

        rows = [
            (r"f(x+y)=f(x)+f(y)", r"f(x)=cx", "线性"),
            (r"f(x+y)=f(x)f(y)", r"f(x)=a^x", "指数"),
            (r"f(xy)=f(x)+f(y)", r"f(x)=c\ln x", "对数"),
            (r"f(x+y)+f(x-y)=2f(x)", r"f(x)=ax+d", "仿射"),
        ]
        header = VGroup(ctext("方程", size=20, color=DIM),
                        ctext("连续解", size=20, color=DIM),
                        ctext("名称", size=20, color=DIM))
        header[0].move_to(LEFT * 4.0 + UP * 2.3)
        header[1].move_to(LEFT * 0.9 + UP * 2.3)
        header[2].move_to(RIGHT * 3.3 + UP * 2.3)
        self.play(FadeIn(header), run_time=0.7)

        y0 = 1.55
        for i, (e, s, nm) in enumerate(rows):
            y = y0 - i * 1.0
            o1 = mt(e, size=30)
            o1.move_to(LEFT * 4.0 + UP * y)
            o2 = mt(s, size=30, color=GOLD)
            o2.move_to(LEFT * 0.9 + UP * y)
            o3 = ctext(nm, size=23, color=ACC)
            o3.move_to(RIGHT * 3.3 + UP * y)
            self.play(FadeIn(o1), FadeIn(o2), FadeIn(o3), run_time=0.7)
            self.wait(0.8)

        foot = ctext("每一行都隐藏着同一个前提：足够好的正则性", size=24, color=RED)
        foot.move_to(DOWN * 2.75)
        self.play(FadeIn(foot), run_time=0.9)
        self.wait(3.4)


# ================================================================ S7 应用与总结
class S7Outlook(Base):
    def body(self):
        self.head(7, "应用与总结")
        self.prog(7)

        hd = ctext("为什么值得认真对待", size=28, color=INK)
        hd.move_to(UP * 3.05)
        self.play(FadeIn(hd), run_time=0.7)
        self.wait(0.8)

        items = [
            ("线性代数", "线性映射 = 加性 + 齐性；加性并不自动给出齐性", BLUE),
            ("泛函分析", "可加算子的连续性与有界性；无穷维会出现不连续可加算子", ACC),
            ("概率论", "特征函数满足 φ(x+y)=φ(x)φ(y)，靠连续性锁定分布", ACC),
            ("物理学", "叠加原理、指数衰减：e^{x+y}=e^x·e^y 的唯一性", GOLD),
            ("数学方法", "函数方程 + 正则性 = 唯一性，这是分析学的常规套路", VIOL),
        ]
        g = VGroup()
        for tag, body, col in items:
            a = ctext(tag, size=22, color=col)
            a.set(width=2.0)
            b = ctext(body, size=23, color=INK)
            row = VGroup(a, b).arrange(RIGHT, buff=0.45, aligned_edge=DOWN)
            g.add(row)
        g.arrange(DOWN, buff=0.55, aligned_edge=LEFT)
        g.next_to(hd, DOWN, buff=0.5).align_to(hd, LEFT).shift(LEFT * 0.4)

        for row in g:
            self.play(FadeIn(row, shift=RIGHT * 0.12), run_time=0.75)
            self.wait(1.5)
        self.wait(2.6)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 思考题
        hd = ctext("三个练习", size=28, color=GOLD)
        hd.move_to(UP * 3.0)
        self.play(FadeIn(hd), run_time=0.8)
        self.wait(1.0)

        ex = [
            ("1.", r"求 $f:\mathbb{R}\to\mathbb{R}$ 使 $f(x+y)=f(x)+f(y)+xy$",
             r"提示：令 $g(x)=f(x)-\frac{x^{2}}{2}$，则 $g$ 满足柯西方程"),
            ("2.", r"证明：$f$ 在 $(0,1)$ 上有上界 $\Rightarrow f(x)=cx$",
             r"提示：仿照 S3 的 $\varepsilon$-$\delta$ 论证"),
            ("3.", r"证明：$f$ 在某区间上不单调 $\Rightarrow \Gamma_f$ 稠密于 $\mathbb{R}^{2}$",
             r"提示：不单调 $\Rightarrow$ 不连续 $\Rightarrow$ 图像稠密"),
        ]
        rows = VGroup()
        for num, body, hint in ex:
            b = rich(body, size=21, color=INK)
            num_t = ctext(num, size=22, color=GOLD)
            head_ = VGroup(num_t, b).arrange(RIGHT, buff=0.2)
            h = rich(hint, size=17, color=DIM)
            rows.add(VGroup(head_, h).arrange(DOWN, buff=0.14, aligned_edge=LEFT))
        rows.arrange(DOWN, buff=0.62, aligned_edge=LEFT)
        rows.next_to(hd, DOWN, buff=0.55).align_to(hd, LEFT).shift(LEFT * 0.35)

        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.12), run_time=0.9)
            self.wait(2.2)

        self.wait(2.0)
        self.play(Create(Line(np.array([-5.6, -2.6, 0.0]), np.array([5.6, -2.6, 0.0]),
                             color=LINE, stroke_width=1.6)), run_time=0.8)
        tip = ctext("第三题说明：病态解不是「例外」，而是「稠密的一整片」", size=22, color=VIOL)
        tip.move_to(DOWN * 3.0)
        self.play(FadeIn(tip), run_time=0.9)
        self.wait(3.2)

        self.wipe(run_time=0.6)

        # ------------------------------------------------ 总结
        hd = ctext("总结", size=30, color=GOLD, weight=BOLD)
        hd.move_to(UP * 3.05)
        self.play(FadeIn(hd), run_time=0.7)

        pts = [
            ("①", r"方程本身只给出 $\mathbb{Q}$-线性：$f(q)=cq$"),
            ("②", r"连续 / 单调 / 有界 / 可测 —— 任一条即可得 $f(x)=cx$"),
            ("③", "去掉正则性：Hamel 基造出稠密、无界、不可测的病态解"),
            ("④", "病态解的存在性必须动用选择公理"),
        ]
        rows = VGroup()
        for num, body in pts:
            b = rich(body, size=23, color=INK)
            rows.add(VGroup(ctext(num, size=20, color=GOLD), b).arrange(RIGHT, buff=0.3))
        rows.arrange(DOWN, buff=0.42, aligned_edge=LEFT)
        rows.move_to(np.array([0.0, 0.95, 0.0]))

        for row in rows:
            self.play(FadeIn(row, shift=RIGHT * 0.12), run_time=0.8)
            self.wait(1.8)

        final = VGroup(
            ctext("柯西方程的全部解，是一个巨大、稠密、不可测的家族；", size=21, color=INK),
            VGroup(ctext("而", size=21, color=INK),
                   ctext("连续性", size=23, color=ACC, weight=BOLD),
                   ctext("一刀切下去，只剩一条过原点的直线。", size=21, color=INK)).arrange(
                       RIGHT, buff=0.05),
        ).arrange(DOWN, buff=0.24)
        final.move_to(np.array([0.0, -1.25, 0.0]))
        self.play(FadeIn(final[0]), run_time=0.9)
        self.wait(0.8)
        self.play(FadeIn(final[1][0]), FadeIn(final[1][1]), run_time=0.7)
        self.wait(0.5)
        self.play(FadeIn(final[1][2]), run_time=0.9)
        self.wait(3.0)

        self.play(Circumscribe(final, color=GOLD, buff=0.18), run_time=1.5)
        self.wait(1.6)

        refs = ctext("延伸阅读：Aczél《Lectures on Functional Equations》· Hamel (1905) · Solovay (1970)",
                     size=16, color=DIM)
        refs.next_to(final, DOWN, buff=0.45)
        self.play(FadeIn(refs), run_time=0.9)
        self.wait(2.0)

        end = ctext("感谢观看", size=20, color=DIM)
        end.next_to(refs, DOWN, buff=0.3)
        self.play(FadeIn(end), run_time=0.8)
        self.wait(2.4)
