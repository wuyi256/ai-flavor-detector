// 网页版 DOM 冒烟测试：用最小 DOM 桩加载 docs/index.html 里的真实脚本，
// 然后「点击」每个按钮、「输入」文字，断言页面行为正确。
// 用法: node tools/smoke_web.js   （退出码非 0 即失败）
// 背景: v0.3 曾因严格模式下块内函数声明不进全局、inline onclick 全部失灵，
//       而算法一致性工具只校验算法段、覆盖不到 UI 绑定，故加此测试。
"use strict";
const fs = require("fs");
const path = require("path");

const html = fs.readFileSync(path.join(__dirname, "..", "docs", "index.html"), "utf8");
const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) { console.error("FAIL: 没找到 <script>"); process.exit(1); }
const code = m[1];

// ---- 最小 DOM 桩 ----
const elems = {};
function makeEl(id) {
  return {
    id: id, value: "", textContent: "", innerHTML: "", style: {}, listeners: {},
    addEventListener(t, f) { (this.listeners[t] = this.listeners[t] || []).push(f); },
    click() { (this.listeners.click || []).forEach(f => f({})); },
    dispatchEvent(e) { (this.listeners[e.type] || []).forEach(f => f(e)); },
    focus() {},
  };
}
global.document = { getElementById(id) { return elems[id] || (elems[id] = makeEl(id)); } };
global.Event = function (t) { this.type = t; };

function assert(c, msg) { if (!c) { console.error("FAIL: " + msg); process.exit(1); } }

// ---- 静态检查：不允许再用 inline 事件属性（ strict 模式下会失灵）----
assert(!/on(?:click|input|change|load)\s*=/.test(html), "HTML 里仍有 inline 事件属性（onclick 等）");

// ---- 加载真实脚本 ----
eval(code);

// ---- 四个按钮都必须绑定了点击事件 ----
["btnAi", "btnHuman", "btnClear", "btnRun"].forEach(id => {
  assert(elems[id] && elems[id].listeners.click && elems[id].listeners.click.length === 1,
    id + " 没有绑定点击事件");
});

// ---- 点「装一段 AI 范文」→ 出报告、分高 ----
elems.btnAi.click();
assert(elems.result.style.display === "block", "点「装一段 AI 范文」后报告没显示");
const aiScore = parseFloat(elems.score.textContent);
assert(aiScore >= 60, "AI 范文分数异常: " + aiScore);
assert(elems.stamp.textContent.length > 0, "印章没盖章");
assert(elems.breakdown.innerHTML.includes("陈词滥调密度"), "分项表没渲染");

// ---- 点「装一段人话」→ 分低 ----
elems.btnHuman.click();
const huScore = parseFloat(elems.score.textContent);
assert(huScore < 40, "人话样本分数异常: " + huScore);

// ---- 点「清空」→ 输入框清空、报告隐藏 ----
elems.btnClear.click();
assert(elems.input.value === "", "清空后输入框没清空");
assert(elems.result.style.display === "none", "清空后报告没隐藏");

// ---- 手动输入 → input 事件 300ms 防抖后自动出报告 ----
elems.input.value = "综上所述，随着时代的不断发展，人工智能正在全方位赋能各行各业。首先它提供抓手，其次形成闭环。值得注意的是，这种变革的重要性不言而喻，值得我们深入思考。";
elems.input.dispatchEvent(new global.Event("input"));
setTimeout(() => {
  assert(elems.result.style.display === "block", "输入事件没有触发自动检测");
  assert(elems.count.textContent.includes("已输入"), "字数统计没更新");
  // ---- 点「出具报告」主按钮 ----
  elems.btnRun.click();
  assert(elems.result.style.display === "block", "点「出具报告」没反应");
  console.log("SMOKE OK  AI样本=" + aiScore + "  人话样本=" + huScore + "  按钮×4 + 自动检测 全部通过");
}, 400);
