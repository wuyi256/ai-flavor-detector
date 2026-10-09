# ai-flavor-detector · AI 味检测器

把一段文字贴进来，给它打个 **「AI 浓度分」（0–100）**，把 delve、leverage、「赋能」「抓手」这类 AI 高频陈词滥调统统标红，并给出「去味」建议。

中英文都支持。纯 Python 标准库实现，零依赖。

## 为什么做这个

AI 写的文字有一套很明显的"口癖"：开场必是 "In today's fast-paced world"，动词必是 leverage / delve / foster，中文必是「赋能、抓手、闭环、综上所述」，而且句长整齐得像阅兵。这个项目把这些特征量化成一个分数：

| 分数区间 | 判定 |
|---|---|
| 0–20 | 人味十足 |
| 20–40 | 略有 AI 嫌疑 |
| 40–60 | AI 味明显 |
| 60–80 | AI 浓度超标 |
| 80–100 | 铁 AI，建议回炉重写 |

## 评分模型

总分由四部分加权（封顶 100）：

1. **陈词滥调密度（≤55 分）**：内置 80+ 条中英 AI 高频词库（每条带权重），按文本长度归一化
2. **句长均匀度（≤25 分）**：AI 句长的变异系数（CV）显著低于人类，CV 越低分越高
3. **八股连接词密度（≤12 分）**：moreover / furthermore / 「首先其次最后」的滥用程度
4. **套路结构（≤8 分）**：「首先…其次…最后」链式结构、连续 3 条以上的列表符

## 安装与使用

```bash
pip install -e .

# 检测文件
aiflavor essay.txt

# 管道输入
cat essay.txt | aiflavor

# JSON 输出（方便接入其他工具）
aiflavor essay.txt --json
```

也可以不安装，直接跑：

```bash
PYTHONPATH=src python -m aiflavor essay.txt
```

## 网页版

`docs/index.html` 是一个零依赖的单文件网页版（同一套词库和评分算法的 JavaScript 移植），
全部计算在浏览器本地完成，文字不出本机。开启 GitHub Pages（Settings → Pages → 选 `docs/` 目录）即可在线使用。

## 作为库调用

```python
from aiflavor import analyze

result = analyze("综上所述，人工智能正在全方位赋能各行各业……")
print(result.score, result.verdict)   # 78.5  AI 浓度超标
for hit in result.hits:
    print(hit.cliche.pattern, hit.count)
```

## 测试

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

测试覆盖：AI 英文/中文文本得高分、人类口语化文本得低分、大小写不敏感、空文本处理、JSON 输出结构等。

## 词库怎么来的

词库（`src/aiflavor/lexicon.py`）来自日常改稿时手工整理的 AI 高频表达，每条都带一条「说人话」的替换建议。欢迎 PR 补充你遇到的 AI 口癖。

## License

MIT
