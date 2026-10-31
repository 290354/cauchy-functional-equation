# 柯西函数方程 · 讲解视频（两版）

| 文件 | 说明 |
|---|---|
| **`柯西函数方程_漫士版.mp4`** | **主交付**：漫士沉思录风格，9:00，32 页，AI 配音 |
| `柯西函数方程_讲课版.mp4` | 早期"课件"风格，10:50，35 页，AI 配音 |
| `柯西函数方程_无配音.mp4` | 讲课版画面，无音轨 |
| `cauchy_ms.py` | 漫士版 Manim 源码（7 章 32 页） |
| `narration_ms.py` | 漫士版逐页配音稿（更书面、更短、留白更多） |
| `mux_ms.py` | 漫士版合成：按实测场景时长 + 页内时间精确铺轨 |
| `cauchy.py` / `narration.py` / `audio_track.py` | 讲课版源码 |
| `assemble.py` / `check_av.py` / `frames.py` | 拼接 / 音画同步自检 / 抽帧 |

## 漫士风是怎么做出来的

四个决定，都跟"课件感"反着来：

1. **字体全换衬线**。标题 `STZhongsong`（华文中宋），正文 `SimSun`，批注 `KaiTi`，西文小字 Georgia 加宽字距。数字与公式保留 Computer Modern。
2. **配色压到四种**。墨黑 `#0B0B0C` / 纸白 `#EDE6DA` / 灰褐 `#8A8175` / 朱砂 `#B4483C`，金色 `#C8A05A` 只给结论。去掉所有圆角卡片、阴影、进度条。
3. **一页只说一件事**。35 页压到 32 页，公式居中、四周大片留白；金句单独成页，逐字浮现（`lag_ratio` 0.05，一个字一个字亮起来）。
4. **节奏放慢**。`PACE=1.55`，转场改 0.9 s 黑场淡出；页脚用 7 个微小圆点代替进度条。

旁白同步换成"沉思"腔：短句、设问、书面语，删掉"我们来看""接下来"这类过场话；
语速 `-4%`（讲课版是 `+10%`），全片旁白只占 61%，剩下的时间是留白。

## 时长与章节

| 章节 | 起止 | 内容 |
|---|---|---|
| 壹 一条方程 | 0:00–1:03 | 封面 · 方程 · "他没有说清为什么" · 1821/1905/1970 |
| 贰 方程在说什么 | 1:03–2:29 | f(0)=0 · 奇性 · 整数倍与有理倍 · f(q)=cq · "无理点上，方程沉默" |
| 叁 一道裂缝 | 2:29–4:04 | 四个条件 · ε-δ · 有理逼近 · "连续性不是结论，是前提" |
| 肆 丛林 | 4:04–6:07 | ℚ-向量空间 · 构造 · 反例 · 点阵 · 病态三连 · 选择公理 |
| 伍 可测 | 6:07–7:11 | 积分法 · 对称性 · "就已经足够好了" |
| 陆 外衣 | 7:11–8:02 | 四行对照 · "怪物换了衣服" |
| 柒 为什么值得认真对待 | 8:02–9:00 | 四个领域 · 收束 · 完 |

## 配音

`edge-tts` + `zh-CN-YunxiNeural`（男声），语速 `-4%`——比讲课版的 `+10%` 慢一档，贴合沉思节奏。
换音色改 `narration_ms.py` 里 `VOICE` 一行；`zh-CN-YunyangNeural`（播音）、`zh-CN-XiaoxiaoNeural`（女声）都可直接替换。

## 音画对齐

1. `cauchy_ms.py` 的 `Base.wipe()` 记录每页起止（`MN_DUMP` 导出），**补时不含在 PACE 缩放里**（早期踩过坑：补时被 PACE 二次放大，导致整轨漂移）。
2. 每页一段旁白 → 合成后读时长 → `pad = max(0, 时长 + 0.45 + 0.55 - 窗口)` → `pad_ms.json`。
3. 重渲后 `pages_ms.txt` 里的时间**已包含补时**，是场景内绝对时间。
4. `mux_ms.py` 用 mp4 的**实测时长**做场景偏移，不用累计推算——避免帧取整误差。
5. `check_av.py` 逐页验：32/32 有人声，峰值 0.889，无叠话。

## 重跑

```bash
python narration_ms.py synth     # 增量合成
python narration_ms.py pad       # 生成 pad_ms.json
manim -qm cauchy_ms.py S1Intro S2Algebra ...        # 重渲
python assemble.py "$TEMP/manim_ms/videos/cauchy_ms/720p30" _work/ms_silent.mp4
python mux_ms.py _work/pages_ms.txt "$TEMP/manim_ms/videos/cauchy_ms/720p30" _work/ms_narrated.mp4
NARR_MOD=narration_ms python check_av.py _work/ms_narrated.mp4 _work/pages_ms.txt "$TEMP/manim_ms/videos/cauchy_ms/720p30"
```

依赖：`manim==0.22.0`、`edge-tts`（联网）、`av`、`imageio-ffmpeg`、MiKTeX（`latex`/`dvisvgm` 在 PATH）。
