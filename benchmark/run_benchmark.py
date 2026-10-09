# -*- coding: utf-8 -*-
"""基准验证：AI 文本与人类文本的分数分离度（分层考核）。

用法：PYTHONPATH=src python benchmark/run_benchmark.py

分三层：
- 典型 AI：阈值 40，必须判为 AI
- 隐蔽型 AI（顺滑、不堆大词）：阈值 25，至少进入「略有 AI 嫌疑」灰区
- 人类文本：阈值 40，不得误判
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aiflavor import analyze  # noqa: E402
from samples import AI_SAMPLES, HUMAN_SAMPLES, SUBTLE_AI_SAMPLES  # noqa: E402

THRESHOLD = 40.0      # 分数 >= 40 判为 AI
GRAY = 25.0           # 隐蔽型 AI 至少要到灰区


def main() -> int:
    ai_scores = [analyze(t).score for t in AI_SAMPLES]
    subtle_scores = [analyze(t).score for t in SUBTLE_AI_SAMPLES]
    human_scores = [analyze(t).score for t in HUMAN_SAMPLES]

    print(f"{'样本':<8}{'分数':>8}  {'判定'}")
    for i, s in enumerate(ai_scores, 1):
        ok = "✓" if s >= THRESHOLD else "✗ 误判"
        print(f"AI-{i:<6}{s:>8}  {ok}")
    for i, s in enumerate(subtle_scores, 1):
        ok = "✓ 灰区" if s >= GRAY else "✗ 漏网"
        print(f"隐蔽AI-{i:<2}{s:>8}  {ok}")
    for i, s in enumerate(human_scores, 1):
        ok = "✓" if s < THRESHOLD else "✗ 误判"
        print(f"人-{i:<6}{s:>8}  {ok}")

    correct = (
        sum(s >= THRESHOLD for s in ai_scores)
        + sum(s >= GRAY for s in subtle_scores)
        + sum(s < THRESHOLD for s in human_scores)
    )
    total = len(ai_scores) + len(subtle_scores) + len(human_scores)
    margin = min(ai_scores) - max(human_scores)

    print("-" * 30)
    print(f"典型AI 平均 {sum(ai_scores)/len(ai_scores):.1f} | "
          f"隐蔽AI 平均 {sum(subtle_scores)/len(subtle_scores):.1f} | "
          f"人类平均 {sum(human_scores)/len(human_scores):.1f} | "
          f"间隔(典型AI最低-人类最高) {margin:.1f}")
    print(f"分层准确率：{correct}/{total} = {correct/total:.0%}"
          f"（典型AI≥{THRESHOLD:g}，隐蔽AI≥{GRAY:g}，人类<{THRESHOLD:g}）")
    return 0 if correct == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
