"""人味信号：AI 很少这么写的东西——口语助词、短句、emoji、破折号、省略号……

这些信号用来【减分】，压低对人类口语化文本的误判。
总分最多减 20 分。

注意：网页版 docs/index.html 里的 JS 实现与本文件逐条对应，改动请两边同步。
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

# 中文口头禅/填充词：AI 写作几乎不用
_ZH_FILLERS = ["然后", "就是", "那个", "反正", "话说"]

# 私人指称：AI 说明文很少提到「我妈」「我室友」
_PERSONAL_RE = re.compile(
    r"我妈|我爸|我室友|舍友|我同学|我老师|我同事|我老板|我上次|我当时|"
    r"我小时候|我高中|我大学|我奶|我爷"
    r"|my (?:mom|dad|roommate|boss|teacher|grandma|grandpa|friend)",
    re.I,
)

_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF☀-➿⬀-⯿]"
)
_ELLIPSIS_RE = re.compile(r"……|\.\.\.")
_EXCLAIM_RE = re.compile(r"[！!]")
_QUESTION_RE = re.compile(r"[？?]")
# 破折号（—— 算一次）、波浪号：人类随笔的标配，AI 几乎不用
_DASH_RE = re.compile(r"——|[—~～]")
_SENT_SPLIT_RE = re.compile(r"[.!?。！？]+")
_EN_WORD_RE = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*")
_CJK_RE = re.compile(r"[一-鿿]")

MAX_HUMAN_POINTS = 20.0


@dataclass
class HumanSignal:
    kind: str       # 类别（中文）
    detail: str     # 命中示例
    count: int
    points: float


def _count_units(text: str) -> int:
    return len(_EN_WORD_RE.findall(text)) + len(_CJK_RE.findall(text))


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

    filler_count = sum(text.count(w) for w in _ZH_FILLERS)
    add("口头禅/填充词", "、".join(w for w in _ZH_FILLERS if w in text)[:12],
        filler_count, 0.5, 3)

    personal = _PERSONAL_RE.findall(text)
    add("私人指称", "、".join(personal[:3]) if personal else "",
        len(personal), 1.0, 3)

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

    questions = _QUESTION_RE.findall(text)
    add("问句", "？", len(questions), 0.5, 3)

    dashes = _DASH_RE.findall(text)
    add("破折号/波浪号", "——", len(dashes), 1.0, 3)

    # 短句：「气死。」「行吧。」——AI 写不出这么碎的句子
    short_sents = [
        s for s in _SENT_SPLIT_RE.split(text)
        if 1 <= _count_units(s) <= 6
    ]
    add("短句", "「" + short_sents[0].strip()[:6] + "」" if short_sents else "",
        len(short_sents), 1.0, 4)

    total = min(MAX_HUMAN_POINTS, sum(s.points for s in signals))
    return round(total, 1), signals
