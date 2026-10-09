# -*- coding: utf-8 -*-
"""基准验证：AI 文本与人类文本的分数分离度。

用法：PYTHONPATH=src python benchmark/run_benchmark.py
打印每组分数、判定结果，以及阈值 40 下的准确率。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aiflavor import analyze  # noqa: E402
from samples import AI_SAMPLES, HUMAN_SAMPLES  # noqa: E402

THRESHOLD = 40.0  # 分数 >= 40 判为 AI


def main() -> int:
    ai_scores = [analyze(t).score for t in AI_SAMPLES]
    human_scores = [analyze(t).score for t in HUMAN_SAMPLES]

    print(f"{'样本':<6}{'分数':>8}  {'判定'}")
    for i, s in enumerate(ai_scores, 1):
        ok = "✓" if s >= THRESHOLD else "✗ 误判"
        print(f"AI-{i:<4}{s:>8}  {ok}")
    for i, s in enumerate(human_scores, 1):
        ok = "✓" if s < THRESHOLD else "✗ 误判"
        print(f"人-{i:<4}{s:>8}  {ok}")

    correct = sum(s >= THRESHOLD for s in ai_scores) + sum(
        s < THRESHOLD for s in human_scores
    )
    total = len(ai_scores) + len(human_scores)
    margin = min(ai_scores) - max(human_scores)

    print("-" * 30)
    print(f"AI 平均 {sum(ai_scores)/len(ai_scores):.1f} | "
          f"人类平均 {sum(human_scores)/len(human_scores):.1f} | "
          f"间隔 {margin:.1f}")
    print(f"阈值 {THRESHOLD} 下准确率：{correct}/{total} = {correct/total:.0%}")
    return 0 if correct == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
