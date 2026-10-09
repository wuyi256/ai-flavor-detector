"""核心分析逻辑：AI 信号加分 + 人味信号减分 -> 0~100 的「AI 味浓度分」。

AI 信号（加分项）：
1. 陈词滥调密度（最高 55 分）：命中词库词条的加权次数 / 文本长度。
   开场加权：template 类词条出现在开头 60 字/词内，权重 ×1.5——
   「综上所述」「In today's world」放在开头，是 AI 的招牌动作。
2. 句长均匀度（最高 25 分）：AI 句长往往整齐划一，人写的参差不齐（按 CV）。
3. 八股连接词密度（最高 12 分）：moreover / furthermore / 首先其次 的滥用。
4. 套路结构（最高 10 分）：「首先…其次…最后」链条、连续列表符、句首重复
   （AI 爱用同一个词开头每句话，人不会）。

人味信号（减分项，合计最多减 20 分）：
口语助词、网络用语、emoji、短句、省略号、感叹号、破折号、英文缩略形式等
AI 很少用的东西。见 human_signals.py。

注意：网页版 docs/index.html 里的 JS 实现与本文件逐条对应，
改动请两边同步，并用 tools/check_web_parity.py 验证分数一致。
"""
from __future__ import annotations

import re
import statistics
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .human_signals import HumanSignal, compute_human_points
from .lexicon import CLICHES, Cliche

_EN_WORD_RE = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*")
_CJK_RE = re.compile(r"[一-鿿]")
# 只在句末标点处断句；逗号、顿号、分号不断——AI 的长句内部也整齐，断了就看不出
_SENT_SPLIT_RE = re.compile(r"[.!?。！？]+")
_BULLET_RE = re.compile(r"^\s*(?:[-*•]|\d{1,2}[.、)）])\s", re.M)
_ZH_CHAIN_RE = re.compile(r"首先.{0,400}?其次.{0,400}?(最后|再次)", re.S)
_EN_CHAIN_RE = re.compile(r"first(ly)?\b.{0,400}?\bsecond(ly)?\b.{0,400}?\b(finally|third(ly)?)\b", re.I | re.S)

MIN_UNITS = 30        # 文本太短不评分
_OPEN_WINDOW = 60     # 开头 60 字/词内的 template 命中吃「开场白」加权
_OPEN_BONUS = 0.5     # 开场命中的额外权重系数（weight × 1.5）

MAX_CLICHE_PTS = 55.0
MAX_UNIFORM_PTS = 25.0
MAX_CONNECTOR_PTS = 12.0
MAX_PATTERN_PTS = 10.0


@dataclass
class Hit:
    cliche: Cliche
    count: int
    opening_count: int = 0  # 其中出现在开头区域的次数（用于开场加权）


@dataclass
class Analysis:
    score: float
    verdict: str
    hits: List[Hit] = field(default_factory=list)
    stats: Dict[str, float] = field(default_factory=dict)
    suggestions: List[Tuple[str, str]] = field(default_factory=list)
    human_signals: List[HumanSignal] = field(default_factory=list)
    too_short: bool = False


def count_units(text: str) -> int:
    """中英文混排的「字数」：英文按词、中文按字。"""
    return len(_EN_WORD_RE.findall(text)) + len(_CJK_RE.findall(text))


def split_sentences(text: str) -> List[str]:
    """按句末标点断句，返回非空句子列表。"""
    return [s.strip() for s in _SENT_SPLIT_RE.split(text) if count_units(s) >= 1]


def _find_hits(text: str) -> List[Hit]:
    lower = text.lower()
    hits: List[Hit] = []
    for c in CLICHES:
        if c.lang == "en":
            matches = list(re.finditer(r"\b" + re.escape(c.pattern) + r"\b", lower))
        else:
            matches = list(re.finditer(re.escape(c.pattern), text))
        if not matches:
            continue
        opening = 0
        if c.category == "template":
            for m in matches:
                if count_units(text[: m.start()]) < _OPEN_WINDOW:
                    opening += 1
        hits.append(Hit(c, len(matches), opening))
    hits.sort(key=lambda h: h.cliche.weight * h.count, reverse=True)
    return hits


def _uniformity_points(text: str) -> Tuple[float, float]:
    """返回 (得分, 变异系数 CV)。句子少于 4 句时证据不足，给 0 分。"""
    lengths = [count_units(s) for s in split_sentences(text) if count_units(s) >= 3]
    if len(lengths) < 4:
        return 0.0, -1.0
    mean = statistics.fmean(lengths)
    if mean == 0:
        return 0.0, -1.0
    cv = statistics.pstdev(lengths) / mean
    # CV 0（句句一样长）-> 满分；CV >= 0.65（长短不一）-> 0 分
    return MAX_UNIFORM_PTS * max(0.0, 1.0 - cv / 0.65), cv


def _starter_repetition_points(text: str) -> Tuple[float, str, int]:
    """句首重复：每句话开头用同一个词，是 AI 的惯性。

    返回 (得分, 重复的开头, 次数)。>=4 句且最高频开头出现 >=3 次才计分。
    """
    sentences = [s for s in split_sentences(text) if count_units(s) >= 3]
    if len(sentences) < 4:
        return 0.0, "", 0
    starters: List[str] = []
    for s in sentences:
        m = _EN_WORD_RE.match(s)
        if m:
            starters.append(m.group(0).lower())
        else:
            zh = _CJK_RE.findall(s)
            if len(zh) >= 2:
                starters.append("".join(zh[:2]))
    if not starters:
        return 0.0, "", 0
    top, n = Counter(starters).most_common(1)[0]
    if n >= 3:
        return min(6.0, (n - 2) * 2.0), top, n
    return 0.0, top, n


def _verdict(score: float) -> str:
    if score < 20:
        return "人味十足"
    if score < 40:
        return "略有 AI 嫌疑"
    if score < 60:
        return "AI 味明显"
    if score < 80:
        return "AI 浓度超标"
    return "铁 AI，建议回炉重写"


def analyze(text: str) -> Analysis:
    text = (text or "").strip()
    units = count_units(text)
    if units < MIN_UNITS:
        return Analysis(
            score=0.0,
            verdict="文本太短，测不出来（至少来三五十个字）",
            stats={"units": units},
            too_short=True,
        )

    hits = _find_hits(text)

    cliche_weighted = 0.0
    connector_count = 0
    opening_count = 0
    for h in hits:
        if h.cliche.category == "connector":
            connector_count += h.count
        else:
            cliche_weighted += h.cliche.weight * h.count
            # 开场加权：开头区域的 template 命中，权重 ×(1 + 0.5)
            cliche_weighted += h.cliche.weight * h.opening_count * _OPEN_BONUS
            opening_count += h.opening_count

    cliche_density = cliche_weighted / units * 100
    cliche_pts = min(MAX_CLICHE_PTS, cliche_density * 14.0)

    connector_density = connector_count / units * 100
    connector_pts = min(MAX_CONNECTOR_PTS, connector_density * 6.0)

    uniform_pts, cv = _uniformity_points(text)

    pattern_pts = 0.0
    bullets = len(_BULLET_RE.findall(text))
    if bullets >= 3:
        pattern_pts += 4.0
    if _ZH_CHAIN_RE.search(text) or _EN_CHAIN_RE.search(text):
        pattern_pts += 4.0
    starter_pts, starter, starter_n = _starter_repetition_points(text)
    pattern_pts = min(MAX_PATTERN_PTS, pattern_pts + starter_pts)

    score_raw = cliche_pts + uniform_pts + connector_pts + pattern_pts
    human_pts, human_signals = compute_human_points(text)
    score = round(min(100.0, max(0.0, score_raw - human_pts)), 1)

    suggestions = [(h.cliche.pattern, h.cliche.suggestion) for h in hits[:5]]

    return Analysis(
        score=score,
        verdict=_verdict(score),
        hits=hits,
        stats={
            "units": units,
            "cliche_points": round(cliche_pts, 1),
            "uniformity_points": round(uniform_pts, 1),
            "sentence_cv": round(cv, 3),
            "connector_points": round(connector_pts, 1),
            "pattern_points": round(pattern_pts, 1),
            "starter_points": round(starter_pts, 1),
            "starter": starter if starter_pts > 0 else "",
            "opening_hits": opening_count,
            "human_points": human_pts,
            "hit_count": sum(h.count for h in hits),
        },
        suggestions=suggestions,
        human_signals=human_signals,
    )
