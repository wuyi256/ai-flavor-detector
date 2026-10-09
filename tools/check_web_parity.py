# -*- coding: utf-8 -*-
"""校验网页版（docs/index.html 内嵌 JS）与 Python 版的评分一致性。

原理：
1. 从 docs/index.html 抽出 ==ALGORITHM-BEGIN/END== 之间的 JS（纯算法，无 DOM）
2. 用 Node.js 跑这段 JS，对基准集每条样本算分
3. 与 Python 版 analyze() 的分数逐条比对

用法（仓库根目录）：
    python tools/check_web_parity.py           # 比对，有差异时退出码 1
    python tools/check_web_parity.py -v        # 打印每条样本的两边分数
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "benchmark"))

from aiflavor import analyze  # noqa: E402
from samples import AI_SAMPLES, HUMAN_SAMPLES, SUBTLE_AI_SAMPLES  # noqa: E402

TOLERANCE = 0.2  # Python round() 银行家舍入 vs JS Math.round 的边界差

NODE_CANDIDATES = [
    shutil.which("node"),
    r"C:\Users\wuyi\.workbuddy\binaries\node\versions\22.22.2-2\node.exe",
]


def find_node() -> str:
    for n in NODE_CANDIDATES:
        if n and os.path.exists(n) if os.path.isabs(n or "") else n:
            return n
    sys.exit("找不到 Node.js，无法校验网页版算法")


def extract_js() -> str:
    html = open(os.path.join(ROOT, "docs", "index.html"), encoding="utf-8").read()
    begin = html.index("// ==ALGORITHM-BEGIN==")
    end = html.index("// ==ALGORITHM-END==")
    return html[begin:end]


def main() -> int:
    verbose = "-v" in sys.argv
    samples = (
        [("AI-%d" % (i + 1), t) for i, t in enumerate(AI_SAMPLES)]
        + [("隐蔽AI-%d" % (i + 1), t) for i, t in enumerate(SUBTLE_AI_SAMPLES)]
        + [("人-%d" % (i + 1), t) for i, t in enumerate(HUMAN_SAMPLES)]
    )
    py_scores = {label: analyze(text).score for label, text in samples}

    with tempfile.TemporaryDirectory() as tmp:
        algo = os.path.join(tmp, "algo.js")
        runner = os.path.join(tmp, "runner.js")
        data = os.path.join(tmp, "samples.json")
        with open(algo, "w", encoding="utf-8") as f:
            f.write(extract_js())
        with open(data, "w", encoding="utf-8") as f:
            json.dump([{"label": l, "text": t} for l, t in samples], f, ensure_ascii=False)
        with open(runner, "w", encoding="utf-8") as f:
            f.write(
                "const {analyze}=require(process.argv[2]);\n"
                "const samples=require(process.argv[3]);\n"
                "const out={};\n"
                "for(const s of samples){const r=analyze(s.text);out[s.label]=r.tooShort?0:r.score;}\n"
                "console.log(JSON.stringify(out));\n"
            )
        node = find_node()
        res = subprocess.run(
            [node, runner, algo, data], capture_output=True, text=True, encoding="utf-8"
        )
        if res.returncode != 0:
            sys.exit("Node 执行失败：\n" + res.stderr)
        js_scores = json.loads(res.stdout)

    bad = 0
    for label, _ in samples:
        py, js = py_scores[label], js_scores[label]
        diff = abs(py - js)
        flag = "" if diff <= TOLERANCE else "  <-- 不一致"
        if diff > TOLERANCE:
            bad += 1
        if verbose or flag:
            print(f"{label:6s} Python {py:5.1f} | Web {js:5.1f} | 差 {diff:.1f}{flag}")
    if bad:
        print(f"\n{bad} 条样本两边分数不一致（容差 {TOLERANCE}），请同步两边的算法实现。")
        return 1
    print(f"网页版与 Python 版评分一致（{len(samples)} 条样本，容差 {TOLERANCE}）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
