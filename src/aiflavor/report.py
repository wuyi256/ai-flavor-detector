"""终端输出：高亮命中词、打印分数条和修改建议。"""
from __future__ import annotations

import re
from typing import List

from .analyzer import Analysis

_RED = "\033[91m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RESET = "\033[0m"


def _combined_pattern(analysis: Analysis) -> "re.Pattern[str] | None":
    if not analysis.hits:
        return None
    parts: List[str] = []
    # 长的排前面，避免短模式先吃掉长模式的一部分
    for h in sorted(analysis.hits, key=lambda h: len(h.cliche.pattern), reverse=True):
        esc = re.escape(h.cliche.pattern)
        parts.append(r"\b" + esc + r"\b" if h.cliche.lang == "en" else esc)
    return re.compile("|".join(parts), re.I)


def highlight_text(text: str, analysis: Analysis, color: bool = True) -> str:
    pattern = _combined_pattern(analysis)
    if pattern is None:
        return text
    if not color:
        return pattern.sub(lambda m: "【" + m.group(0) + "】", text)
    return pattern.sub(lambda m: _RED + _BOLD + m.group(0) + _RESET, text)


def _bar(score: float, width: int = 30) -> str:
    filled = int(round(score / 100 * width))
    return "█" * filled + "░" * (width - filled)


def _score_color(score: float) -> str:
    if score < 40:
        return _GREEN
    if score < 70:
        return _YELLOW
    return _RED


def render_terminal(analysis: Analysis, text: str, color: bool = True) -> str:
    c = lambda code: code if color else ""
    lines: List[str] = []
    if analysis.too_short:
        return analysis.verdict

    s = analysis.stats
    lines.append("")
    lines.append(c(_BOLD) + "AI 味浓度分："
                 + c(_score_color(analysis.score)) + f"{analysis.score} / 100" + c(_RESET))
    lines.append(c(_score_color(analysis.score)) + _bar(analysis.score) + c(_RESET)
                 + "  " + c(_BOLD) + analysis.verdict + c(_RESET))
    lines.append("")
    lines.append(c(_DIM) + f"字数 {s['units']} | 命中 {s['hit_count']} 处 | "
                 f"大词 {s['cliche_points']} 分 | 句长均匀 {s['uniformity_points']} 分"
                 f" | 八股连接词 {s['connector_points']} 分 | 套路结构 {s['pattern_points']} 分"
                 + c(_RESET))
    lines.append("")
    lines.append(c(_BOLD) + "---- 原文（标红 = AI 高频词）----" + c(_RESET))
    lines.append(highlight_text(text, analysis, color=color))
    if analysis.suggestions:
        lines.append("")
        lines.append(c(_BOLD) + "---- 去味建议 ----" + c(_RESET))
        for pattern, tip in analysis.suggestions:
            lines.append(f"  • 「{pattern}」→ {tip}")
    lines.append("")
    return "\n".join(lines)


def to_json_dict(analysis: Analysis) -> dict:
    return {
        "score": analysis.score,
        "verdict": analysis.verdict,
        "too_short": analysis.too_short,
        "stats": analysis.stats,
        "hits": [
            {
                "pattern": h.cliche.pattern,
                "lang": h.cliche.lang,
                "category": h.cliche.category,
                "weight": h.cliche.weight,
                "count": h.count,
                "suggestion": h.cliche.suggestion,
            }
            for h in analysis.hits
        ],
        "suggestions": [
            {"pattern": p, "suggestion": s} for p, s in analysis.suggestions
        ],
    }
