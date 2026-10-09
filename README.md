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

**AI 信号（加分）**：

1. **陈词滥调密度（≤55 分）**：内置 100+ 条中英 AI 高频词库（每条带权重），按文本长度归一化；**开场加权**——template 类套话出现在开头 60 字内权重 ×1.5（「综上所述」「In today's world」放开头是 AI 的招牌动作）
2. **句长均匀度（≤25 分）**：AI 句长的变异系数（CV）显著低于人类，CV 越低分越高
3. **八股连接词密度（≤12 分）**：moreover / furthermore / 「首先其次最后」的滥用程度
4. **套路结构（≤10 分）**：「首先…其次…最后」链式结构、连续 3 条以上的列表符、**句首重复**（每句话用同一个词开头，是 AI 的惯性）

**人味信号（减分，最多 -20 分）**：

只找"AI 的证据"会误伤口语化的人类文本，所以同时检测 AI 几乎不会用的东西：
中文语气词（吧/呢/呗）、网络用语、emoji、**短句**（「气死。」「行吧。」这种碎句 AI 写不出来）、省略号、感叹号、**破折号/波浪号**、**问句**、英文缩略形式（don't / it's）、英文口语（lol / gonna）等。

最终得分 = clamp(AI 信号 − 人味信号, 0, 100)

## 基准验证

`benchmark/` 内置 6 段 AI 文本 + 7 段人类文本的基准集（含一段认真写的人类正式写作，专门验证不误伤），跑一下就知道模型水平：

```bash
PYTHONPATH=src python benchmark/run_benchmark.py
```

当前结果（阈值 40 分）：

| 指标 | 数值 |
|---|---|
| AI 样本平均分 | 86.0 |
| 人类样本平均分 | 4.4 |
| 最小间隔（AI 最低 − 人类最高） | 71.0 |
| 基准集准确率 | 13/13 = 100% |

## 诚实的局限

- 这是**启发式规则模型**，不是神经网络。它擅长抓"典型的 AI 腔"，但对认真润色过的 AI 文本、或本身写得就很正式的人类文本（比如公文），区分能力有限。
- 它更适合**自查**（"我这段是不是 AI 味太重了"），不适合当"判官"去锤别人。
- 基准集目前只有 13 个样本，验证的是区分度而非泛化能力，欢迎 PR 补充样本。

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

`docs/index.html` 是零依赖的单文件网页版，「检测报告单」风格：

- **边贴边测**：输入即分析（防抖 300ms），不用点按钮
- **红色印章判定**：人味十足 → 铁 AI，像体检报告一样盖章
- **悬停看建议**：命中的 AI 高频词带红色波浪下划线，鼠标放上去直接看替换建议
- 全部计算在浏览器本地完成，文字不出本机

开启 GitHub Pages（Settings → Pages → 选 `docs/` 目录）即可在线使用。

网页版是同一套算法的 JavaScript 移植，与 Python 版逐条对应。改动算法后跑一致性校验：

```bash
python tools/check_web_parity.py -v   # 用 Node.js 对比两边在基准集上的分数
```

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

测试覆盖：AI 英文/中文文本得高分、人类口语化文本得低分、开场套路加权、句首重复检测、短句/破折号/问句等人味信号、基准集 13 样本分离度、JSON 输出结构等。

## 词库怎么来的

词库（`src/aiflavor/lexicon.py`）来自日常改稿时手工整理的 AI 高频表达，每条都带一条「说人话」的替换建议。欢迎 PR 补充你遇到的 AI 口癖。

## License

MIT
