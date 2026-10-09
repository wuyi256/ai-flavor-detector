"""核心分析逻辑：AI 信号加分 + 人味信号减分 -> 0~100 的「AI 味浓度分」。

AI 信号（加分项）：
1. 陈词滥调密度（最高 55 分）：命中词库词条的加权次数 / 文本长度。
   开场加权：template 类词条出现在开头 60 字/词内，权重 ×1.5。
   注意放大系数只有 4.5——单个命中不该主导总分（v0.3 之前是 14，
   100 词里一个 "crucial" 就 +42 分，既误伤人类、又让分数被词库绑架）。
2. 节奏均匀度（最高 25 分）：句长 CV 与分句（逗号/顿号分隔）长度 CV 取强。
   AI 不仅句子一样长，每个逗号之间的分句都一样长。
3. 八股连接词密度（最高 12 分）：moreover / furthermore / 首先其次 的滥用。
4. 套路结构（最高 10 分）：「首先…其次…最后」链条、连续列表符、句首重复。
5. 对仗平衡（最高 5 分）：「虽然…但是…」「不仅…而且…」成对出现 >=2 组——
   AI 写议论文特别喜欢端水。
6. 空泛度（最高 5 分）：全文没有一个数字、引用或专有名词——人写东西
   总有具体细节，AI 的顺滑文本往往通篇抽象。

人味信号（减分项，合计最多减 20 分）：见 human_signals.py。

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
# 分句：逗号、顿号、分号、冒号都算（句末标点先断开过了）
_CLAUSE_SPLIT_RE = re.compile(r"[,，、;；:：]")
_BULLET_RE = re.compile(r"^\s*(?:[-*•]|\d{1,2}[.、)）])\s", re.M)
_ZH_CHAIN_RE = re.compile(r"首先.{0,400}?其次.{0,400}?(最后|再次)", re.S)
_EN_CHAIN_RE = re.compile(r"first(ly)?\b.{0,400}?\bsecond(ly)?\b.{0,400}?\b(finally|third(ly)?)\b", re.I | re.S)

# 空泛度：全文找不到任何「具体信息」时加分
_DIGIT_RE = re.compile(r"\d")
_QUOTE_RE = re.compile(r"[「」《》\"']")
_MIDCAP_RE = re.compile(r"(?<=[a-z] )[A-Z][A-Za-z]+")  # 句中专有名词（句首大写不算）

# 对仗结构：左右两边都出现才算一组；>=2 组才加分（单组是正常用法）
_ZH_PAIRS = [
    (("不仅", "不但"), ("而且",)),
    (("虽然",), ("但是", "但")),
    (("既",), ("又",)),
    (("无论",), ("都",)),
    (("与其",), ("不如",)),
]
_EN_PAIRS = [
    (("not only",), ("but also",)),
    (("on the one hand",), ("on the other hand",)),
]

MIN_UNITS = 30        # 文本太短不评分
_OPEN_WINDOW = 60     # 开头 60 字/词内的 template 命中吃「开场白」加权
_OPEN_BONUS = 0.5     # 开场命中的额外权重系数（weight × 1.5）

MAX_CLICHE_PTS = 55.0
CLICHE_SCALE = 4.5    # 每「每百字 1 次加权命中」对应的分值
MAX_UNIFORM_PTS = 25.0
CV_SPAN = 0.72        # CV 到 0.72 视为「长短不一」，均匀度归零
MAX_CONNECTOR_PTS = 12.0
MAX_PATTERN_PTS = 10.0
MAX_PAIR_PTS = 5.0
MAX_GENERIC_PTS = 5.0


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


def _cv(lengths: List[int]) -> float:
    """变异系数；数据不足返回 -1。"""
    if len(lengths) < 4:
        return -1.0
    mean = statistics.fmean(lengths)
    if mean == 0:
        return -1.0
    return statistics.pstdev(lengths) / mean


def _uniformity_points(text: str) -> Tuple[float, float, float]:
    """节奏均匀度 = max(句长均匀, 0.8 × 分句长均匀)。返回 (得分, 句CV, 分句CV)。"""
    sent_lens = [count_units(s) for s in split_sentences(text) if count_units(s) >= 3]
    clauses = [
        c.strip()
        for s in split_sentences(text)
        for c in _CLAUSE_SPLIT_RE.split(s)
        if count_units(c) >= 2
    ]
    clause_lens = [count_units(c) for c in clauses]

    sent_cv = _cv(sent_lens)
    clause_cv = _cv(clause_lens)
    sent_pts = MAX_UNIFORM_PTS * max(0.0, 1.0 - sent_cv / CV_SPAN) if sent_cv >= 0 else 0.0
    clause_pts = MAX_UNIFORM_PTS * max(0.0, 1.0 - clause_cv / CV_SPAN) if clause_cv >= 0 else 0.0
    return max(sent_pts, 0.8 * clause_pts), sent_cv, clause_cv


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


def _pair_points(text: str) -> Tuple[float, int]:
    """对仗平衡：左右成对的关联词 >=2 组才加分（1 组是正常用法）。"""
    lower = text.lower()
    pairs = 0
    for lefts, rights in _ZH_PAIRS:
        if any(k in text for k in lefts) and any(k in text for k in rights):
            pairs += 1
    for lefts, rights in _EN_PAIRS:
        if any(k in lower for k in lefts) and any(k in lower for k in rights):
            pairs += 1
    if pairs >= 3:
        return MAX_PAIR_PTS, pairs
    if pairs == 2:
        return 3.0, pairs
    return 0.0, pairs


def _generic_points(text: str, units: int) -> float:
    """空泛度：全文没有一个数字、引用或句中专有名词。"""
    specificity = (
        len(_DIGIT_RE.findall(text))
        + len(_QUOTE_RE.findall(text))
        + len(_MIDCAP_RE.findall(text))
    )
    if specificity > 0:
        return 0.0
    if units >= 120:
        return MAX_GENERIC_PTS
    if units >= 60:
        return 3.0
    return 0.0


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

    # 平滑密度：分母加 40 防止短文本里单个命中被放大成高分
    cliche_density = cliche_weighted / (units + 40) * 100
    cliche_pts = min(MAX_CLICHE_PTS, cliche_density * CLICHE_SCALE)

    connector_density = connector_count / (units + 40) * 100
    connector_pts = min(MAX_CONNECTOR_PTS, connector_density * 6.0)

    uniform_pts, sent_cv, clause_cv = _uniformity_points(text)

    pattern_pts = 0.0
    bullets = len(_BULLET_RE.findall(text))
    if bullets >= 3:
        pattern_pts += 4.0
    if _ZH_CHAIN_RE.search(text) or _EN_CHAIN_RE.search(text):
        pattern_pts += 4.0
    starter_pts, starter, starter_n = _starter_repetition_points(text)
    pattern_pts = min(MAX_PATTERN_PTS, pattern_pts + starter_pts)

    pair_pts, pair_count = _pair_points(text)
    generic_pts = _generic_points(text, units)

    score_raw = cliche_pts + uniform_pts + connector_pts + pattern_pts + pair_pts + generic_pts
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
            "sentence_cv": round(sent_cv, 3),
            "clause_cv": round(clause_cv, 3),
            "connector_points": round(connector_pts, 1),
            "pattern_points": round(pattern_pts, 1),
            "starter_points": round(starter_pts, 1),
            "starter": starter if starter_pts > 0 else "",
            "opening_hits": opening_count,
            "pair_points": round(pair_pts, 1),
            "pair_count": pair_count,
            "generic_points": round(generic_pts, 1),
            "human_points": human_pts,
            "hit_count": sum(h.count for h in hits),
        },
        suggestions=suggestions,
        human_signals=human_signals,
    )
