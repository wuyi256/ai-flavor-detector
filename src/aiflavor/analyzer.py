"""核心分析逻辑：AI 信号加分 + 人味信号减分 -> 0~100 的「AI 味浓度分」。

AI 信号（加分项，合计封顶 100）：
1. 陈词滥调密度（最高 55 分）：命中词库词条的加权次数 / 文本长度
2. 句长均匀度（最高 25 分）：AI 句长往往整齐划一，人写的参差不齐
3. 八股连接词密度（最高 12 分）：moreover / furthermore / 首先其次 的滥用
4. 套路结构（最高 8 分）：「首先…其次…最后」链条、连续列表符

人味信号（减分项，合计最多减 20 分）：
口语助词、网络用语、emoji、省略号、感叹号、英文缩略形式等 AI 很少用的东西。
见 human_signals.py。
"""
from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .human_signals import HumanSignal, compute_human_points
from .lexicon import CLICHES, Cliche

_EN_WORD_RE = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*")
_CJK_RE = re.compile(r"[一-鿿]")
_SENT_SPLIT_RE = re.compile(r"[.!?。！？；;]+")
_BULLET_RE = re.compile(r"^\s*(?:[-*•]|\d{1,2}[.、)）])\s", re.M)
_ZH_CHAIN_RE = re.compile(r"首先.{0,400}?其次.{0,400}?(最后|再次)", re.S)
_EN_CHAIN_RE = re.compile(r"first(ly)?\b.{0,400}?\bsecond(ly)?\b.{0,400}?\b(finally|third(ly)?)\b", re.I | re.S)

MIN_UNITS = 30  # 文本太短不评分


@dataclass
class Hit:
    cliche: Cliche
    count: int


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


def _find_hits(text: str) -> List[Hit]:
    lower = text.lower()
    hits: List[Hit] = []
    for c in CLICHES:
        if c.lang == "en":
            count = len(re.findall(r"\b" + re.escape(c.pattern) + r"\b", lower))
        else:
            count = text.count(c.pattern)
        if count:
            hits.append(Hit(c, count))
    hits.sort(key=lambda h: h.cliche.weight * h.count, reverse=True)
    return hits


def _sentence_unit_lengths(text: str) -> List[int]:
    sentences = [s for s in _SENT_SPLIT_RE.split(text) if count_units(s) >= 3]
    return [count_units(s) for s in sentences]


def _uniformity_points(text: str) -> Tuple[float, float]:
    """返回 (得分, 变异系数 CV)。句子少于 4 句时证据不足，给 0 分。"""
    lengths = _sentence_unit_lengths(text)
    if len(lengths) < 4:
        return 0.0, -1.0
    mean = statistics.fmean(lengths)
    if mean == 0:
        return 0.0, -1.0
    cv = statistics.pstdev(lengths) / mean
    # CV 0（句句一样长）-> 25 分；CV >= 0.65（长短不一）-> 0 分
    return 25.0 * max(0.0, 1.0 - cv / 0.65), cv


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

    cliche_weighted = sum(h.cliche.weight * h.count for h in hits if h.cliche.category != "connector")
    connector_count = sum(h.count for h in hits if h.cliche.category == "connector")

    cliche_density = cliche_weighted / units * 100
    cliche_pts = min(55.0, cliche_density * 14.0)

    connector_density = connector_count / units * 100
    connector_pts = min(12.0, connector_density * 6.0)

    uniform_pts, cv = _uniformity_points(text)

    pattern_pts = 0.0
    bullets = len(_BULLET_RE.findall(text))
    if bullets >= 3:
        pattern_pts += 4.0
    if _ZH_CHAIN_RE.search(text) or _EN_CHAIN_RE.search(text):
        pattern_pts += 4.0

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
            "human_points": human_pts,
            "hit_count": sum(h.count for h in hits),
        },
        suggestions=suggestions,
        human_signals=human_signals,
    )
