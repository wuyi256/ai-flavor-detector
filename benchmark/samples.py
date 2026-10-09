# -*- coding: utf-8 -*-
"""基准测试集：6 段 AI 文本 + 6 段人类文本，用于验证评分模型的区分度。

AI_SAMPLES：用大模型生成后未加修改的典型输出（公文腔 / 学术八股 / 产品文案）。
HUMAN_SAMPLES：日记、聊天记录、论坛回帖、商品评价等真实口语化写作。
"""

AI_SAMPLES = [
    # 1 中文公文腔
    "综上所述，随着时代的不断发展，人工智能正在全方位赋能各行各业。"
    "首先，它为组织提供了新的抓手，帮助企业打通业务链路。"
    "其次，通过多维度的系统性打法，可以形成完整的商业闭环。"
    "值得注意的是，这种变革的重要性不言而喻。"
    "与此同时，我们也应当看到其在一定程度上带来的深层次影响。"
    "总而言之，只有积极拥抱变化，才能在新征程上立于不败之地。",
    # 2 英文学术八股
    "In today's world, it is crucial to leverage cutting-edge technology. "
    "Moreover, robust frameworks can foster innovation across the landscape. "
    "Furthermore, a holistic approach can unlock new realms of synergy. "
    "In addition, we must delve into this multifaceted paradigm shift. "
    "It is important to note that seamless integration plays a crucial role. "
    "In conclusion, these pivotal tools underscore a bright future.",
    # 3 中文 AI 说明文
    "人工智能在医疗领域的应用正引发广泛关注。首先，它能够助力医生进行影像诊断，"
    "显著提高效率。其次，通过深耕大数据赛道，AI 可以为患者打造个性化治疗方案。"
    "然而，值得注意的是，数据隐私问题不容忽视。总而言之，AI 医疗前景广阔，"
    "正在深刻改变人们的生活，带来了前所未有的机遇。",
    # 4 英文 AI 产品文案
    "Discover our innovative platform that leverages state-of-the-art algorithms. "
    "This comprehensive solution is designed to elevate your workflow and unlock productivity. "
    "Moreover, it seamlessly integrates with your existing tools. "
    "Furthermore, the robust architecture ensures reliability at scale. "
    "In conclusion, it is a game-changer for modern teams.",
    # 5 中文 AI 鸡汤
    "在这个充满变化的大背景下，每个人都在寻找自己的方向。首先，我们要学会与自己和解。"
    "其次，要不断深耕自己的领域，提升核心竞争力。与此同时，保持开放的心态也至关重要。"
    "总而言之，人生的每一步都算数。让我们携手共进，谱写属于自己的新篇章，"
    "绘就美好未来的蓝图。",
    # 6 英文 AI 议论文
    "In recent years, remote work has become increasingly popular. "
    "Notably, it offers flexibility that was previously unimaginable. "
    "Moreover, companies can harness a global talent pool. "
    "However, it is essential to consider the challenges. "
    "For instance, communication can be less effective. "
    "Ultimately, a balanced approach is pivotal for success.",
]

HUMAN_SAMPLES = [
    # 1 日记
    "今天中午食堂的糖醋排骨又涨价了，气死。不过打饭阿姨手没抖，给了我四大块，行吧，原谅她了。"
    "下午实验课困得要命，昨晚熬夜赶报告，三点多才睡，还好同桌带了风油精，往太阳穴一抹，直接清醒。"
    "回宿舍路上下雨了，我没带伞，一路小跑，鞋全湿。晚上本来想看两集剧，结果躺床上五分钟就睡着了。",
    # 2 聊天记录
    "在吗在吗！明天抢课帮我留意下呗，我怕我起不来……闹钟定了仨了还是慌。"
    "对了上次说的那个香锅，就西门那家，周末去不去？我室友说巨好吃。"
    "哈哈哈哈行，那就周六中午，谁迟到谁请客啊！",
    # 3 论坛回帖
    "楼主这个解法我看了，思路是对的，但第三步有个坑：边界条件没处理，n=1 的时候会直接炸。"
    "我上周刚在这儿栽过，调了一下午……你把循环下标往前挪一位试试。"
    "另外建议换个变量名，tmp1、tmp2 真的谁看谁迷糊。",
    # 4 商品评价
    "先说结论：值这个价。鞋码偏大半码，脚瘦的记得拍小。"
    "底挺软的，走一天不累，就是新鞋有点味儿，阳台吹两天就好了。"
    "快递是真的慢，等了五天才到……看在质量的份上原谅它了。",
    # 5 英文论坛回帖
    "Yeah I ran into this exact bug last week lol. Took me forever to figure out "
    "it's just a caching issue. Clear your browser cache and it should work. "
    "Also don't use the beta version right now, it's broken on Windows. "
    "The devs said they're gonna fix it in the next release, so fingers crossed.",
    # 6 课程感想
    "这门课怎么说呢，开头两周我真想退。作业量大不说，讲的东西感觉根本用不上。"
    "结果第三周做项目的时候突然发现，诶，前面那些好像串起来了？"
    "现在看还行吧，就是老师语速太快了，我得回去看回放，0.75 倍速刚刚好。",
    # 7 认真写的实验报告反思（人类正式写作，不应被误伤）
    "这次实验我做了三次才成功。前两次都卡在数据读取那一步，后来才发现是编码格式的问题，"
    "文件是 GBK 的，我一直按 UTF-8 读。改完之后程序跑通了，但结果和助教给的参考答案对不上，"
    "又调了一个晚上，最后发现是我把两个变量的顺序写反了。说实话这个过程挺折磨人的，"
    "但调通那一刻确实开心。我最大的收获是：报错信息要认真看，它基本都告诉你问题在哪了。",
]
