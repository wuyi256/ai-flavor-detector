"""人味信号：AI 很少这么写的东西——口语助词、emoji、省略号、感叹号、英文缩略形式……

这些信号用来【减分】，压低对人类口语化文本的误判。
总分最多减 20 分。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple

# 中文句末/口语助词：AI 几乎不用「吧呢呗嘛啦」结尾
_ZH_PARTICLE_RE = re.compile(r"[吧呢呗嘛啦哦嗯][，。！？!?,.\s]")

# 中文口语词 / 网络用语：AI 写作里极少出现
_ZH_COLLOQUIAL = [
    "真的", "感觉", "好家伙", "笑死", "绷不住", "破防", "无语", "绝了",
    "yyds", "绝绝子", "牛逼", "贼", "巨", "超", "寄", "摆烂", "摸鱼",
    "干饭", "早八", "抢课", "食堂", "宿舍", "室友", "阿姨",
]

# 英文缩略形式：don't / it's / I'm —— AI 正式输出里很少用
_EN_CONTRACTION_RE = re.compile(r"\b\w+(?:n't|'m|'re|'ve|'ll|'d)\b", re.I)

# 英文口语
_EN_INFORMAL = [
    "gonna", "wanna", "kinda", "sorta", "lol", "lmao", "tbh", "imo",
    "ngl", "btw", "stuff", "yeah", "nah", "ok", "okay",
]

_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF☀-➿⬀-⯿]"
)
_ELLIPSIS_RE = re.compile(r"……|\.\.\.")
_EXCLAIM_RE = re.compile(r"[！!]")

MAX_HUMAN_POINTS = 20.0


@dataclass
class HumanSignal:
    kind: str       # 类别（中文）
    detail: str     # 命中示例
    count: int
    points: float


def compute_human_points(text: str) -> Tuple[float, List[HumanSignal]]:
    """返回 (减分, 信号列表)。每类有计数上限，避免长文本刷分。"""
    signals: List[HumanSignal] = []

    def add(kind: str, detail: str, count: int, weight: float, cap: int) -> None:
        if count <= 0:
            return
        capped = min(count, cap)
        signals.append(HumanSignal(kind, detail, count, round(capped * weight, 1)))

    particles = _ZH_PARTICLE_RE.findall(text)
    add("中文语气词", "……".join(particles[:3]).strip() or "吧/呢/呗", len(particles), 1.5, 6)

    zh_hits = [w for w in _ZH_COLLOQUIAL if w in text]
    add("中文口语/网络用语", "、".join(zh_hits[:3]), len(zh_hits), 2.0, 5)

    contractions = _EN_CONTRACTION_RE.findall(text)
    add("英文缩略形式", ", ".join(contractions[:3]), len(contractions), 1.0, 6)

    lower = text.lower()
    en_hits = [w for w in _EN_INFORMAL if re.search(r"\b" + re.escape(w) + r"\b", lower)]
    add("英文口语", ", ".join(en_hits[:3]), len(en_hits), 2.0, 4)

    emojis = _EMOJI_RE.findall(text)
    add("emoji", "".join(emojis[:5]), len(emojis), 1.5, 5)

    ellipsis = _ELLIPSIS_RE.findall(text)
    add("省略号", "……", len(ellipsis), 1.5, 3)

    exclaims = _EXCLAIM_RE.findall(text)
    add("感叹号", "！", len(exclaims), 0.5, 6)

    total = min(MAX_HUMAN_POINTS, sum(s.points for s in signals))
    return round(total, 1), signals
