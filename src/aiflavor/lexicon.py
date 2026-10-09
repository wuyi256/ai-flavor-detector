"""内置 AI 陈词滥调词库（中英双语）。

每条包含：
- pattern:    匹配模式（英文按词边界、不区分大小写；中文按子串）
- lang:       "en" | "zh"
- category:   "buzzword"（大词/黑话）| "connector"（八股连接词）| "template"（套话模板）
- weight:     1.0（轻微）~ 3.0（重灾）
- suggestion: 更有人味的替换思路
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Cliche:
    pattern: str
    lang: str
    category: str
    weight: float
    suggestion: str


def _en(pattern, category, weight, suggestion):
    return Cliche(pattern, "en", category, weight, suggestion)


def _zh(pattern, category, weight, suggestion):
    return Cliche(pattern, "zh", category, weight, suggestion)


CLICHES = [
    # ---------------- English buzzwords (weight 3) ----------------
    _en("delve", "buzzword", 3.0, "换成 dig into / look at，或者直接说「看看」"),
    _en("leverage", "buzzword", 3.0, "换成 use"),
    _en("utilize", "buzzword", 3.0, "换成 use"),
    _en("facilitate", "buzzword", 3.0, "换成 help"),
    _en("robust", "buzzword", 3.0, "具体说哪里好，别用万能形容词"),
    _en("seamless", "buzzword", 3.0, "具体说怎么个顺法"),
    _en("cutting-edge", "buzzword", 3.0, "说具体技术或数字"),
    _en("state-of-the-art", "buzzword", 3.0, "说具体指标"),
    _en("game-changer", "buzzword", 3.0, "说改变了什么"),
    _en("realm", "buzzword", 3.0, "换成 field / area"),
    _en("navigate", "buzzword", 3.0, "除非真的在导航，换成 deal with"),
    _en("foster", "buzzword", 3.0, "换成 encourage / help"),
    _en("holistic", "buzzword", 3.0, "说清是哪几个方面的整体"),
    _en("paradigm", "buzzword", 3.0, "换成 model / way"),
    _en("tapestry", "buzzword", 3.0, "别织锦了，说人话"),
    _en("multifaceted", "buzzword", 3.0, "列举是哪几面"),
    _en("underscore", "buzzword", 3.0, "换成 show"),
    _en("pivotal", "buzzword", 3.0, "换成 key / important"),
    _en("crucial", "buzzword", 3.0, "换成 important，或说清为什么重要"),
    _en("elevate", "buzzword", 3.0, "换成 improve"),
    _en("unlock", "buzzword", 3.0, "换成 enable / open"),
    _en("unleash", "buzzword", 3.0, "收一收戏剧性"),
    _en("harness", "buzzword", 3.0, "换成 use"),
    _en("embark", "buzzword", 3.0, "换成 start"),
    _en("spearhead", "buzzword", 3.0, "换成 lead"),
    _en("bolster", "buzzword", 3.0, "换成 support / strengthen"),
    _en("synergy", "buzzword", 3.0, "说清谁和谁怎么配合"),
    _en("shed light on", "buzzword", 3.0, "换成 explain"),
    _en("testament", "buzzword", 3.0, "「a testament to」是重灾区，换成 shows"),
    # ---------------- English mild (weight 2) ----------------
    _en("comprehensive", "buzzword", 2.0, "说清覆盖了什么"),
    _en("innovative", "buzzword", 2.0, "说清新在哪"),
    _en("significantly", "buzzword", 2.0, "给数字"),
    _en("effectively", "buzzword", 2.0, "给效果"),
    _en("numerous", "buzzword", 2.0, "给数字"),
    _en("various", "buzzword", 2.0, "列举几个"),
    _en("journey", "buzzword", 2.0, "除非真的在旅行"),
    _en("landscape", "buzzword", 2.0, "比喻用法是 AI 重灾区，换成 field"),
    _en("ever-evolving", "buzzword", 2.0, "删掉通常不影响意思"),
    _en("fast-paced", "buzzword", 2.0, "AI 开头标配，删掉"),
    _en("play a role", "template", 2.0, "换成具体动词"),
    _en("wide range of", "template", 2.0, "列举几个"),
    _en("in today's world", "template", 3.0, "AI 开场白第一名，整句删"),
    # ---------------- English connectors / templates ----------------
    _en("moreover", "connector", 1.5, "换成 also，或者直接另起一句"),
    _en("furthermore", "connector", 1.5, "换成 also"),
    _en("in addition", "connector", 1.5, "换成 also / plus"),
    _en("consequently", "connector", 1.5, "换成 so"),
    _en("in conclusion", "connector", 1.5, "结论直接说结论"),
    _en("firstly", "connector", 1.5, "first 就够"),
    _en("it is important to note", "template", 2.5, "重要就直接讲，别预告"),
    _en("it is worth noting", "template", 2.5, "值得注意就直接讲"),
    _en("it goes without saying", "template", 2.5, "既然不用说，那就别说"),
    # ---------------- Chinese 黑话/大词 (weight 3) ----------------
    _zh("赋能", "buzzword", 3.0, "说清谁帮谁做了什么"),
    _zh("抓手", "buzzword", 3.0, "换成「切入点」或直接说做法"),
    _zh("闭环", "buzzword", 3.0, "说清流程怎么走"),
    _zh("链路", "buzzword", 3.0, "换成「流程/环节」"),
    _zh("颗粒度", "buzzword", 3.0, "换成「细致程度」"),
    _zh("对齐", "buzzword", 3.0, "换成「确认/统一」"),
    _zh("拉通", "buzzword", 3.0, "换成「一起沟通」"),
    _zh("组合拳", "buzzword", 3.0, "列举是哪几招"),
    _zh("心智", "buzzword", 3.0, "换成「印象/认知」"),
    _zh("生态化反", "buzzword", 3.0, "这个……祝好运"),
    _zh("全方位", "buzzword", 2.5, "列举是哪几个方面"),
    _zh("多维度", "buzzword", 2.5, "列举是哪几个维度"),
    _zh("深层次", "buzzword", 2.5, "说清深在哪"),
    _zh("系统性", "buzzword", 2.0, "说清包括哪些部分"),
    _zh("沉淀", "buzzword", 2.0, "换成「积累/总结」"),
    _zh("打法", "buzzword", 2.0, "换成「做法」"),
    # ---------------- Chinese 套话模板 ----------------
    _zh("综上所述", "template", 2.5, "直接说结论"),
    _zh("总而言之", "template", 2.5, "直接说结论"),
    _zh("总的来说", "template", 2.0, "直接说结论"),
    _zh("由此可见", "template", 2.0, "换成「所以」"),
    _zh("毋庸置疑", "template", 2.5, "真的无疑就不用强调"),
    _zh("显而易见", "template", 2.5, "明显就不用说"),
    _zh("不难发现", "template", 2.0, "换成「可以看到」或删掉"),
    _zh("值得注意的是", "template", 2.5, "值得注意就直接讲"),
    _zh("众所周知", "template", 2.5, "都知道就别说了"),
    _zh("在某种程度上", "template", 2.0, "哪种程度？说具体"),
    _zh("在一定程度上", "template", 2.0, "哪种程度？说具体"),
    _zh("随着时代的", "template", 2.5, "AI 开场白，整句删"),
    _zh("不断发展", "template", 1.5, "「随着…的不断发展」是重灾区"),
    _zh("重要性不言而喻", "template", 3.0, "不言自明就别言"),
    # ---------------- Chinese 八股连接词 ----------------
    _zh("首先", "connector", 1.0, "一二三列太多像提纲"),
    _zh("其次", "connector", 1.5, "「首先其次」连用是 AI 八股"),
    _zh("与此同时", "connector", 1.5, "换成「同时」"),
    _zh("此外", "connector", 1.0, "偶尔用没问题，连用就有味"),
    _zh("然而", "connector", 1.0, "换成「但是/不过」更口语"),
    _zh("不仅", "connector", 1.0, "「不仅…而且…」连用注意"),
    _zh("一方面", "connector", 1.5, "「一方面…另一方面…」是八股"),
    _zh("另一方面", "connector", 1.5, "说人话：「再说」"),
]
