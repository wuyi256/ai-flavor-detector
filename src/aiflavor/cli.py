"""命令行入口：aiflavor [文件] [--json] [--no-color]；不带文件时从标准输入读。"""
from __future__ import annotations

import argparse
import json
import sys

from .analyzer import analyze
from .report import render_terminal, to_json_dict


def _read_text(path: "str | None") -> str:
    if path is None:
        return sys.stdin.read()
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8", "gb18030"):  # Windows 上很多文本是 GBK
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(
        prog="aiflavor",
        description="AI 味检测器：给文字打个「AI 浓度分」，把 AI 陈词滥调统统标红。",
    )
    parser.add_argument("file", nargs="?", help="要检测的文本文件（不填则从标准输入读）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出完整结果")
    parser.add_argument("--no-color", action="store_true", help="不用 ANSI 颜色（用【】标记命中词）")
    args = parser.parse_args(argv)

    text = _read_text(args.file)
    analysis = analyze(text)

    if args.json:
        print(json.dumps(to_json_dict(analysis), ensure_ascii=False, indent=2))
    else:
        print(render_terminal(analysis, text, color=not args.no_color and sys.stdout.isatty()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
