# -*- coding: utf-8 -*-
import unittest

from aiflavor import analyze
from aiflavor.report import to_json_dict

AI_EN_TEXT = (
    "In today's world, it is crucial to leverage cutting-edge technology. "
    "Moreover, robust frameworks can foster innovation across the landscape. "
    "Furthermore, a holistic approach can unlock new realms of synergy. "
    "In addition, we must delve into this multifaceted paradigm shift. "
    "It is important to note that seamless integration plays a role. "
    "In conclusion, these pivotal tools underscore a bright future."
)

AI_ZH_TEXT = (
    "综上所述，随着时代的不断发展，人工智能正在全方位赋能各行各业。"
    "首先，它为组织提供了新的抓手，帮助企业打通业务链路。"
    "其次，通过多维度的系统性打法，可以形成完整的商业闭环。"
    "值得注意的是，这种变革的重要性不言而喻。"
    "与此同时，我们也应当看到其在一定程度上带来的深层次影响。"
)

HUMAN_ZH_TEXT = (
    "今天中午食堂的糖醋排骨又涨价了，气死。不过打饭阿姨手没抖，给了我四大块，行吧，原谅她了。"
    "下午实验课困得要命，昨晚熬夜赶报告，三点多才睡，还好同桌带了风油精，往太阳穴一抹，直接清醒。"
    "回宿舍路上下雨了，我没带伞，一路小跑，鞋全湿。晚上本来想看两集剧，结果躺床上五分钟就睡着了。"
    "明天早八，闹钟定了三个，希望能起得来。"
)


class TestAnalyze(unittest.TestCase):
    def test_ai_english_scores_high(self):
        a = analyze(AI_EN_TEXT)
        self.assertFalse(a.too_short)
        self.assertGreaterEqual(a.score, 55.0, f"AI 英文应得高分，实际 {a.score}")
        self.assertIn(a.verdict, ("AI 味明显", "AI 浓度超标", "铁 AI，建议回炉重写"))

    def test_ai_chinese_scores_high(self):
        a = analyze(AI_ZH_TEXT)
        self.assertGreaterEqual(a.score, 50.0, f"AI 中文应得高分，实际 {a.score}")

    def test_human_text_scores_low(self):
        a = analyze(HUMAN_ZH_TEXT)
        self.assertLessEqual(a.score, 30.0, f"人写的文字应得低分，实际 {a.score}")
        self.assertIn(a.verdict, ("人味十足", "略有 AI 嫌疑"))

    def test_empty_and_short_text(self):
        self.assertTrue(analyze("").too_short)
        self.assertTrue(analyze("太短了").too_short)
        self.assertEqual(analyze("").score, 0.0)

    def test_specific_hits_detected(self):
        a = analyze(AI_EN_TEXT)
        patterns = {h.cliche.pattern for h in a.hits}
        for expected in ("leverage", "delve", "furthermore", "in today's world"):
            self.assertIn(expected, patterns)

    def test_zh_hits_detected(self):
        a = analyze(AI_ZH_TEXT)
        patterns = {h.cliche.pattern for h in a.hits}
        for expected in ("赋能", "抓手", "闭环", "综上所述"):
            self.assertIn(expected, patterns)

    def test_case_insensitive_english(self):
        text = "We should DELVE into this. " * 8
        a = analyze(text)
        hits = {h.cliche.pattern: h.count for h in a.hits}
        self.assertEqual(hits.get("delve"), 8)

    def test_json_shape(self):
        d = to_json_dict(analyze(AI_ZH_TEXT))
        for key in ("score", "verdict", "stats", "hits", "suggestions"):
            self.assertIn(key, d)
        self.assertIsInstance(d["hits"], list)

    def test_suggestions_offered(self):
        a = analyze(AI_EN_TEXT)
        self.assertTrue(a.suggestions)
        self.assertTrue(all(len(s) == 2 for s in a.suggestions))


if __name__ == "__main__":
    unittest.main()
