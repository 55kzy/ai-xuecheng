# -*- coding: utf-8 -*-
"""AI学程 Web 摸底服务 — Flask 版"""
import sys, os, json, uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '03_程序'))
from engine import Session, QuestionBank
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.urandom(24)

qb = QuestionBank()
qb.load()

sessions = {}

# ============================================================
# 课程数据库（方向×维度矩阵）
# ============================================================
COURSE_MAP = {
    # (方向, 维度) → {id, title, desc, emoji, file, status}
    # ---- 方向A：日常生活 ----
    ('A','K'): {'id':'a-k','title':'让AI帮你搞定日常琐事','emoji':'🏠',
                'desc':'写消息、做计划、查信息，一句话的事',
                'file':'A_日常_T1_琐事.html','status':'ready'},
    ('A','P'): {'id':'a-p','title':'生活场景下让AI秒懂你','emoji':'💬',
                'desc':'用对prompt，让AI真正听懂你要什么',
                'file':'A_日常_T1_生活prompt.html','status':'ready'},
    ('A','L'): {'id':'a-l','title':'AI说的能信吗？日常信息核实术','emoji':'🔍',
                'desc':'别让AI把你带沟里去',
                'file':'A_日常_T1_核实.html','status':'ready'},
    ('A','T'): {'id':'a-t','title':'零门槛上手AI：注册到日常使用','emoji':'🚀',
                'desc':'从0到1，真正用起来',
                'file':'A_日常_T1_工具上手.html','status':'ready'},
    ('A','C'): {'id':'a-c','title':'AI能帮我干啥？一张日常能力地图','emoji':'🗺️',
                'desc':'搞清楚AI的边界，才知道怎么用',
                'file':'A_日常_T1_概念.html','status':'ready'},

    # ---- 方向B：职场应用 ----
    ('B','K'): {'id':'b-tools','title':'三步锁定你要的AI工具','emoji':'🧰',
                'desc':'一张地图搞定AI工具选择',
                'file':'B_职场_T1_工具箱.html','status':'ready'},
    ('B','P'): {'id':'b-prompt','title':'10分钟搞定周报','emoji':'📝',
                'desc':'让AI写出能用可用的职场汇报',
                'file':'B_职场_T1_周报.html','status':'ready'},
    ('B','L'): {'id':'b-verify','title':'别被AI骗了','emoji':'🔍',
                'desc':'三招判断AI说的是真是假',
                'file':'B_职场_T1_核实.html','status':'ready'},
    ('B','T'): {'id':'b-t','title':'职场人零代码自动化','emoji':'⚡',
                'desc':'不用写代码，把重复工作交给AI',
                'file':'B_职场_T1_自动化.html','status':'ready'},
    ('B','C'): {'id':'b-c','title':'AI职场能力地图','emoji':'🧭',
                'desc':'定位你的AI能力，找到提升方向',
                'file':'B_职场_T1_概念.html','status':'ready'},

    # ---- 方向C：自媒体 ----
    ('C','K'): {'id':'c-k','title':'自媒体AI工具链：从选题到发布','emoji':'🛠️',
                'desc':'找到适合你的创作工具组合',
                'file':'C_自媒体_T1_工具链.html','status':'ready'},
    ('C','P'): {'id':'c-style','title':'让AI写出你的风格','emoji':'✍️',
                'desc':'自媒体人怎么写prompt，文案才有个人味道',
                'file':'C_自媒体_T1_风格prompt.html','status':'ready'},
    ('C','L'): {'id':'c-l','title':'自媒体避坑：AI内容审核与事实核查','emoji':'🔍',
                'desc':'用AI但别被AI坑',
                'file':'C_自媒体_T1_核实.html','status':'ready'},
    ('C','T'): {'id':'c-script','title':'一条提示词顶一小时脚本','emoji':'🎬',
                'desc':'从卡壳到3分钟出一版能用脚本',
                'file':'C_自媒体_T1_脚本.html','status':'ready'},
    ('C','C'): {'id':'c-c','title':'自媒体AI能力全景图','emoji':'🧠',
                'desc':'系统了解AI在创作全链路中的应用',
                'file':'C_自媒体_T1_概念.html','status':'ready'},

    # ---- 方向D：搞钱变现 ----
    ('D','K'): {'id':'d-tools','title':'搞钱先搞工具：AI副业工具箱','emoji':'💰',
                'desc':'不同类型的副业，用不同的AI工具',
                'file':'D_搞钱_T1_工具箱.html','status':'ready'},
    ('D','P'): {'id':'d-first','title':'发条朋友圈，接第一单AI副业','emoji':'📱',
                'desc':'从知道到做到，就差这一单的距离',
                'file':'D_搞钱_T1_第一单.html','status':'ready'},
    ('D','L'): {'id':'d-l','title':'搞钱避坑：别让AI假信息坑了你','emoji':'⚠️',
                'desc':'搞钱路上，信息真假决定成败',
                'file':'D_搞钱_T1_核实.html','status':'ready'},
    ('D','T'): {'id':'d-t','title':'搞钱技术实操','emoji':'⚙️',
                'desc':'从工具到交付，搞定技术环节',
                'file':'D_搞钱_T1_技术.html','status':'ready'},
    ('D','C'): {'id':'d-c','title':'AI副业全景地图','emoji':'🧭',
                'desc':'搞钱方向那么多，哪个适合你？',
                'file':'D_搞钱_T1_概念.html','status':'ready'},

    # ---- 方向E：技术开发 ----
    ('E','K'): {'id':'e-tools','title':'程序员的AI工具箱','emoji':'⚙️',
                'desc':'哪些AI工具真的能帮你写代码',
                'file':'E_技术_T1_工具选型.html','status':'ready'},
    ('E','P'): {'id':'e-prompt','title':'技术人写prompt的实战秘籍','emoji':'⌨️',
                'desc':'不只是"帮我写个函数"——技术场景的prompt要这样写',
                'file':'E_技术_T1_prompt.html','status':'ready'},
    ('E','L'): {'id':'e-l','title':'AI代码能信吗？程序员防坑实战','emoji':'🔍',
                'desc':'审查、验证、调试AI生成的代码',
                'file':'E_技术_T1_代码核实.html','status':'ready'},
    ('E','T'): {'id':'e-t','title':'开发者AI进阶：用API搭开发流水线','emoji':'🚀',
                'desc':'从调用API到搭自己的AI工具',
                'file':'E_技术_T1_技术.html','status':'ready'},
    ('E','C'): {'id':'e-c','title':'AI技术全景进阶地图','emoji':'🧠',
                'desc':'技术人需要了解的AI底层原理',
                'file':'E_技术_T1_概念.html','status':'ready'},

    # ---- 方向F：学术研究 ----
    ('F','K'): {'id':'f-k','title':'学术研究AI工具箱','emoji':'📚',
                'desc':'找到最适合学术场景的AI工具',
                'file':'F_学术_T1_工具.html','status':'ready'},
    ('F','P'): {'id':'f-literature','title':'50篇文献，10分钟筛完','emoji':'📑',
                'desc':'让AI帮你筛、读、总结文献',
                'file':'F_学术_T1_文献.html','status':'ready'},
    ('F','L'): {'id':'f-verify','title':'学术研究别被AI带沟里','emoji':'🔍',
                'desc':'AI能帮你查文献，但小心它给你编论文',
                'file':'F_学术_T1_核实.html','status':'ready'},
    ('F','T'): {'id':'f-t','title':'学术AI技术实操：数据分析与图表','emoji':'📊',
                'desc':'用AI加速数据分析，把精力给思考',
                'file':'F_学术_T1_技术.html','status':'ready'},
    ('F','C'): {'id':'f-c','title':'学术研究AI能力全景','emoji':'🧠',
                'desc':'系统了解AI在科研全流程中能做什么',
                'file':'F_学术_T1_概念.html','status':'ready'},

    # ---- 方向G：全面了解 ----
    ('G','K'): {'id':'g-k','title':'AI工具全家桶：10个实用工具','emoji':'🛠️',
                'desc':'从ChatGPT到Midjourney，一张表看清楚',
                'file':'G_全面了解_T1_工具.html','status':'ready'},
    ('G','P'): {'id':'g-p','title':'跟AI说话的正确姿势','emoji':'💬',
                'desc':'零基础学会写prompt',
                'file':'G_全面了解_T1_prompt.html','status':'ready'},
    ('G','L'): {'id':'g-l','title':'别被AI骗了：AI信息核实术','emoji':'🔍',
                'desc':'AI也会编故事——你学会了分辨',
                'file':'G_全面了解_T1_核实.html','status':'ready'},
    ('G','T'): {'id':'g-t','title':'AI实操入门：注册到上手','emoji':'🚀',
                'desc':'从注册账号到第一次写出好东西',
                'file':'G_全面了解_T1_技术.html','status':'ready'},
    ('G','C'): {'id':'g-concept','title':'一张图看懂AI能做什么','emoji':'🗺️',
                'desc':'AI没你想的那么神，也没那么没用',
                'file':'G_全面了解_T1_概念.html','status':'ready'},
}

# 通用课（方向无关，只按维度）
COURSE_FALLBACK = {
    'P': {'id':'p-basic','title':'让AI听懂你的话','emoji':'💬',
          'desc':'学会写有效的prompt，告别AI答非所问',
          'file': None, 'status':'coming'},
    'L': {'id':'l-basic','title':'别被AI骗了','emoji':'🔍',
          'desc':'学会验证AI输出，识别幻觉和编造',
          'file': None, 'status':'coming'},
    'K': {'id':'k-basic','title':'AI到底能做什么','emoji':'🔧',
          'desc':'从头了解AI工具的能力和局限',
          'file': None, 'status':'coming'},
    'C': {'id':'c-basic','title':'跟AI打交道的正确姿势','emoji':'🧠',
          'desc':'掌握AI的核心概念，不再用错工具',
          'file': None, 'status':'coming'},
    'T': {'id':'t-basic','title':'技术门槛没那么可怕','emoji':'📈',
          'desc':'快速扫盲AI技术基础，零基础也能懂',
          'file': None, 'status':'coming'},
}

# 课程ID → (方向, 维度) 反向查找
COURSE_BY_ID = {}
for (dir_, dim), info in list(COURSE_MAP.items()):
    COURSE_BY_ID[info['id']] = {'dir': dir_, 'dim': dim, 'info': info}

# T2/T3 制作中课程
COMING_SOON = {}
for (dir_, dim), info in COURSE_MAP.items():
    for level, emoji in [('T2','💰'), ('T3','💎')]:
        cid = f"{info['id']}_{level.lower()}"
        COMING_SOON[cid] = {
            'id': cid,
            'title': info['title'],
            'dir': dir_,
            'dim': dim,
            'level': level,
            'emoji': emoji,
            'base_id': info['id']
        }


HOME_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI学程 — 摸底</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{
    font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;
    background:linear-gradient(135deg,#f5f7fa 0%,#e8ecf4 100%);
    color:#1d1d1f;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:16px
  }
  .card{
    background:rgba(255,255,255,0.88);backdrop-filter:blur(20px);border-radius:24px;
    padding:28px 24px;max-width:480px;width:100%;
    box-shadow:0 8px 40px rgba(0,0,0,.08),0 1px 3px rgba(0,0,0,.04);
    border:1px solid rgba(255,255,255,0.6)
  }
  h1{font-size:22px;font-weight:700;margin-bottom:4px;letter-spacing:-.3px}
  .sub{color:#8e8e93;font-size:13px;margin-bottom:20px}

  /* 方向选择卡片 */
  .dir-grid{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px}
  .dir-tag{
    width:calc(50% - 4px);min-width:140px;flex:1 1 auto;
    padding:10px 12px;border-radius:14px;border:1.5px solid #e5e5ea;
    cursor:pointer;transition:all .15s;user-select:none;
    background:rgba(255,255,255,0.6);display:flex;flex-direction:column;gap:2px;
    position:relative;overflow:hidden
  }
  .dir-tag:hover{border-color:#007aff;background:#f0f7ff;transform:scale(1.02);z-index:1}
  .dir-tag.selected{
    border-color:#007aff;background:#007aff;color:#fff;
    box-shadow:0 4px 12px rgba(0,122,255,.3)
  }
  .dir-tag .dir-emoji{font-size:18px;line-height:1.2}
  .dir-tag .dir-name{font-size:14px;font-weight:600;line-height:1.4}
  .dir-tag .dir-desc{font-size:11px;opacity:.65;line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .dir-tag.selected .dir-desc{opacity:.75}

  .btn{
    width:100%;padding:13px;border:none;border-radius:14px;
    font-size:16px;font-weight:600;cursor:pointer;transition:all .2s
  }
  .btn-primary{
    background:#007aff;color:#fff;
    box-shadow:0 4px 14px rgba(0,122,255,.25)
  }
  .btn-primary:hover{background:#0066d6;transform:translateY(-1px)}
  .btn-primary:disabled{opacity:.35;transform:none;cursor:not-allowed}

  /* 选项按钮 */
  .opt-btn{
    display:block;width:100%;padding:13px 15px;margin-bottom:9px;
    border:1.5px solid #e5e5ea;border-radius:16px;background:rgba(255,255,255,0.6);
    font-size:14px;text-align:left;cursor:pointer;transition:all .15s;line-height:1.5
  }
  .opt-btn:hover{border-color:#007aff;background:#f0f7ff;transform:translateX(2px)}
  .opt-btn.selected{border-color:#007aff;background:#e8f2ff;box-shadow:0 2px 8px rgba(0,122,255,.15)}
  .opt-btn.multi-selected{border-color:#ff9500;background:#fff8ec;box-shadow:0 2px 8px rgba(255,149,0,.2)}

  /* 进度条 */
  .progress{display:flex;gap:5px;margin-bottom:16px}
  .dot{flex:1;height:4px;border-radius:2px;background:#e5e5ea;transition:all .3s}
  .dot.done{background:#007aff}
  .dot.active{background:#007aff;opacity:.5}

  .badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;margin-bottom:10px}
  .badge-dim{background:rgba(0,122,255,.12);color:#007aff}
  .badge-type{background:rgba(142,142,147,.12);color:#8e8e93}

  /* ===== 结果页 ===== */
  .sec-title{font-size:14px;font-weight:600;display:flex;align-items:center;gap:5px;margin-bottom:10px;letter-spacing:-.2px}

  .result-hero{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}
  .result-hero .left h2{font-size:18px;font-weight:700;margin:0}
  .result-hero .left .sub{font-size:12px;margin:2px 0 0;color:#8e8e93}

  .profile-badge{
    padding:6px 14px;border-radius:100px;font-size:13px;font-weight:600;white-space:nowrap
  }
  .pb-探索者{background:linear-gradient(135deg,#fff3e0,#ffe0b2);color:#e65100}
  .pb-实践者{background:linear-gradient(135deg,#e8f5e9,#c8e6c9);color:#2e7d32}
  .pb-领跑者{background:linear-gradient(135deg,#e3f2fd,#bbdefb);color:#1565c0}

  /* 画像概览行：雷达 + 维度缩写 */
  .profile-row{display:flex;gap:12px;align-items:center;margin-bottom:18px}
  .profile-row canvas{width:120px;height:120px;flex-shrink:0}
  .dim-mini{flex:1;display:flex;flex-direction:column;gap:4px}
  .dim-mini-item{display:flex;align-items:center;gap:6px;font-size:12px}
  .dim-mini-item .dm-label{width:52px;color:#636366;font-weight:500;flex-shrink:0}
  .dim-mini-item .dm-bar{flex:1;height:5px;background:rgba(0,0,0,.06);border-radius:3px;overflow:hidden}
  .dim-mini-item .dm-fill{height:100%;border-radius:3px;transition:width .5s}
  .dim-mini-item .dm-level{font-size:11px;min-width:36px;text-align:right;font-weight:500}

  /* 短板区 */
  .gap-section{background:rgba(255,255,255,.4);border-radius:14px;padding:12px 14px;margin-bottom:18px;border:1px solid rgba(255,255,255,.3)}
  .gap-section .gap-title{font-size:13px;font-weight:600;margin-bottom:6px;color:#636366}
  .gap-section .gap-item{display:flex;align-items:center;gap:6px;font-size:13px;padding:3px 0;color:#c0392b}
  .gap-section .gap-none{font-size:13px;color:#636366}

  /* 课程推荐三级卡片 */
  .tier-card{border-radius:14px;padding:12px 14px;margin-bottom:10px;border:1px solid rgba(255,255,255,.4);overflow:hidden}
  .tier-card .tier-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:4px}
  .tier-card .tier-name{font-weight:700;font-size:15px}
  .tier-card .tier-badge{font-size:11px;font-weight:600;padding:2px 10px;border-radius:20px}
  .tier-card .tier-desc{font-size:12px;color:#636366;line-height:1.5;margin-bottom:4px}
  .tier-card .tier-result{font-size:12px;color:#007aff;font-weight:500}
  .tier-card .tier-result::before{content:'→ '}
  .tier-rec{font-size:12px;padding:2px 8px;border-radius:10px;display:inline-block;margin-top:3px;font-weight:500}
  .tier-rec.tag-hl{background:rgba(255,149,0,.12);color:#e65100}
  .tier-rec.tag-fit{background:rgba(52,199,89,.12);color:#2e7d32}
  .tier-rec.tag-adv{background:rgba(0,122,255,.1);color:#007aff}

  .tier-1 .tier-name{color:#e65100}
  .tier-1 .tier-badge{background:rgba(230,81,0,.1);color:#e65100}
  .tier-2 .tier-name{color:#2e7d32}
  .tier-2 .tier-badge{background:rgba(46,125,50,.1);color:#2e7d32}
  .tier-3 .tier-name{color:#1565c0}
  .tier-3 .tier-badge{background:rgba(21,101,192,.1);color:#1565c0}

  /* 方向建议 */
  .chip{display:inline-block;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:500;background:rgba(0,122,255,.08);color:#007aff;margin:0 4px 6px 0}

  .course-card{text-decoration:none;color:inherit;display:block}
  .course-card:hover div>div:first-child{box-shadow:0 2px 8px rgba(0,122,255,.12);border-color:rgba(0,122,255,.2)!important}

  .btn-row{display:flex;gap:10px;margin-top:16px}
  .btn-row .btn{flex:1}
  .btn-sec{background:rgba(142,142,147,.12);color:#1d1d1f}
  .btn-sec:hover{background:rgba(142,142,147,.2)}

  .page{animation:fadeUp .3s ease}
  @keyframes fadeUp{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
</style>
</head>
<body>
<div class="card" id="app">
  <h1 id="title">🧠 AI学程</h1>
  <div class="sub" id="subtitle">先聊聊你的需求，再推荐最适合的课</div>

  <!-- 选方向 -->
  <!-- 欢迎页：告诉用户这是干啥的 -->
  <div id="page-welcome" class="page">
    <div style="text-align:center;margin-bottom:14px">
      <div style="font-size:52px;margin-bottom:8px">🧠</div>
      <div style="font-size:26px;font-weight:700;letter-spacing:-.5px;margin-bottom:6px">AI学程</div>
      <div style="font-size:15px;color:#8e8e93;line-height:1.6">一套帮你找到最适合自己AI课程的系统</div>
    </div>

    <div style="margin:18px 0;display:flex;flex-direction:column;gap:13px">
      <div style="display:flex;gap:12px;align-items:flex-start">
        <span style="font-size:24px;flex-shrink:0;line-height:1">🔍</span>
        <div style="flex:1">
          <div style="font-size:16px;font-weight:600;margin-bottom:2px">摸底测试</div>
          <div style="font-size:14px;color:#636366;line-height:1.5">6道题快速了解你的AI基础水平，不费时不费力</div>
        </div>
      </div>
      <div style="display:flex;gap:12px;align-items:flex-start">
        <span style="font-size:24px;flex-shrink:0;line-height:1">🎯</span>
        <div style="flex:1">
          <div style="font-size:16px;font-weight:600;margin-bottom:2px">精准画像</div>
          <div style="font-size:14px;color:#636366;line-height:1.5">从工具认知、提示词、信息素养、技术感、概念理解五个维度画出你的AI能力图谱</div>
        </div>
      </div>
      <div style="display:flex;gap:12px;align-items:flex-start">
        <span style="font-size:24px;flex-shrink:0;line-height:1">📚</span>
        <div style="flex:1">
          <div style="font-size:16px;font-weight:600;margin-bottom:2px">定制课程</div>
          <div style="font-size:14px;color:#636366;line-height:1.5">根据你的画像和兴趣方向，推荐最该先学的课——免费又实用</div>
        </div>
      </div>
      <div style="display:flex;gap:12px;align-items:flex-start">
        <span style="font-size:24px;flex-shrink:0;line-height:1">🌟</span>
        <div style="flex:1">
          <div style="font-size:16px;font-weight:600;margin-bottom:2px">学得明白</div>
          <div style="font-size:14px;color:#636366;line-height:1.5">每节课20-30分钟，图文+实操，学完就能用上</div>
        </div>
      </div>
    </div>

    <div style="background:rgba(0,122,255,.06);border-radius:12px;padding:12px 14px;margin-bottom:12px">
      <div style="font-size:14px;color:#007aff;font-weight:600;margin-bottom:3px">⏱ 只需要3分钟</div>
      <div style="font-size:13px;color:#636366;line-height:1.5">选你感兴趣的AI方向 → 做6道简单的题 → 得到你的能力画像和课程推荐</div>
    </div>

    <button class="btn btn-primary" onclick="showSelectPage()" style="margin-top:6px;font-size:18px;padding:15px">好的，开始摸底 →</button>
  </div>

  <!-- 选方向 -->
  <div id="page-select" class="page" style="display:none">
    <div style="font-size:12px;color:#8e8e93;margin-bottom:10px">💡 可以多选 · 选你最感兴趣的就好</div>
    <div class="dir-grid" id="dirs"></div>
    <button class="btn btn-primary" id="btn-start" onclick="start()" disabled>开始摸底</button>
  </div>

  <!-- 做题 -->
  <div id="page-quiz" class="page" style="display:none">
    <div class="progress" id="progress"></div>
    <div><span class="badge badge-dim" id="q-dim"></span> <span class="badge badge-type" id="q-type"></span> <span class="badge" id="q-multi" style="display:none;background:rgba(255,149,0,.12);color:#e65100">可多选</span></div>
    <div style="font-size:16px;font-weight:600;margin:10px 0 16px;line-height:1.6" id="q-text"></div>
    <div id="q-options"></div>
    <div style="display:flex;gap:10px;margin-top:14px">
      <button class="btn" id="btn-back" onclick="onBack()" style="flex:1;background:rgba(142,142,147,.1);color:#1d1d1f;border:1.5px solid #e5e5ea" disabled>← 上一步</button>
      <button class="btn btn-primary" id="btn-confirm" onclick="confirmAnswer()" style="flex:2" disabled>确认答案</button>
    </div>
  </div>

  <!-- ===== 结果页 ===== -->
  <div id="page-result" class="page" style="display:none">
    <div class="result-hero">
      <div class="left">
        <h2>你的学习画像</h2>
        <div class="sub">共 <span id="r-count">0</span> 题 · 看看该从哪开始</div>
      </div>
      <span class="profile-badge" id="r-badge"></span>
    </div>

    <!-- 画像概览（小雷达 + 维度条） -->
    <div class="profile-row">
      <canvas id="miniRadar" width="240" height="240"></canvas>
      <div class="dim-mini" id="r-mini-dims"></div>
    </div>

    <!-- 短板区 -->
    <div class="gap-section" id="r-gap">
      <div class="gap-title">📌 需要提升</div>
      <div id="r-gap-list"></div>
    </div>

    <!-- 课程推荐 -->
    <div class="sec-title">📚 推荐课程</div>
    <div id="r-tiers"></div>

    <!-- 方向 -->
    <div style="margin-top:6px">
      <div class="sec-title">🎯 你关注的方向</div>
      <div id="r-dir"></div>
    </div>

    <div class="btn-row">
      <button class="btn btn-sec" onclick="clearAndRestart()">重新摸底</button>
    </div>
  </div>
</div>

<script>
const DIR_META={
  A:{e:'🏠',l:'日常生活',d:'写消息、做规划、查信息'},
  B:{e:'💼',l:'职场应用',d:'写周报、做PPT、整理数据'},
  C:{e:'📱',l:'自媒体',d:'文案、脚本、选题、排版'},
  D:{e:'💰',l:'搞钱变现',d:'副业、接单、赚钱技巧'},
  E:{e:'⚙️',l:'技术开发',d:'写代码、搭工具、调API'},
  F:{e:'📚',l:'学术研究',d:'文献、论文、数据分析'},
  G:{e:'🧠',l:'全面了解',d:'零基础入门AI全貌'},
};
const DIM_META={K:{e:'🔧',l:'工具认知'},P:{e:'✍️',l:'提示词'},T:{e:'⚡',l:'技术感'},L:{e:'🔍',l:'信息素养'},C:{e:'🧠',l:'概念理解'}};
const DIM_COLORS={K:'#007aff',P:'#ff9500',T:'#ff3b30',L:'#34c759',C:'#5856d6'};

let selectedDirs=[], sessionId='', isMultiSelect=false, selectedOptions=[];

// 方向选择卡片
for(let k of Object.keys(DIR_META)){
  let m=DIR_META[k];
  let el=document.createElement('div');el.className='dir-tag';el.dataset.key=k;
  el.innerHTML='<span class="dir-emoji">'+m.e+'</span><span class="dir-name">'+m.l+'</span><span class="dir-desc">'+m.d+'</span>';
  el.onclick=function(){
    this.classList.toggle('selected');
    selectedDirs=[...document.querySelectorAll('.dir-tag.selected')].map(e=>e.dataset.key);
    document.getElementById('btn-start').disabled=selectedDirs.length===0;
  };
  document.getElementById('dirs').appendChild(el);
}

function showSelectPage(){
  document.getElementById('page-welcome').style.display='none';
  document.getElementById('page-select').style.display='block';
}

function start(){
  fetch('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({dirs:selectedDirs})})
    .then(r=>r.json()).then(d=>{sessionId=d.session_id;showQuizPage();showQuestion(d)})
}

function showQuizPage(){
  document.getElementById('page-welcome').style.display='none';document.getElementById('page-select').style.display='none';
  document.getElementById('page-result').style.display='none';
  document.getElementById('page-quiz').style.display='block';
}

let selectedOption=-1;

function showQuestion(d){
  let q=d.question,p=d.progress;selectedOption=-1;isMultiSelect=false;selectedOptions=[];
  const multiBadge=document.getElementById('q-multi');
  if(q.multiple){
    isMultiSelect=true;
    multiBadge.style.display='inline-block';
  }else{
    multiBadge.style.display='none';
  }
  document.getElementById('btn-confirm').disabled=true;
  const isFirst=p.done===0;
  const backBtn=document.getElementById('btn-back');
  backBtn.disabled=false;
  if(isFirst){
    backBtn.textContent='← 重选方向';
    backBtn.style.background='rgba(255,149,0,.1)';backBtn.style.borderColor='rgba(255,149,0,.3)';backBtn.style.color='#e65100';
  }else{
    backBtn.disabled=!d.can_back;
    backBtn.textContent='← 上一步';
    backBtn.style.background='rgba(142,142,147,.1)';backBtn.style.borderColor='#e5e5ea';backBtn.style.color='#1d1d1f';
  }
  let dots='';
  for(let i=0;i<6;i++){let c=i<p.done?'dot done':(i===p.done?'dot active':'dot');dots+='<div class="'+c+'"></div>'}
  document.getElementById('progress').innerHTML=dots;
  document.getElementById('q-dim').textContent=DIM_META[q.dimension].l;
  document.getElementById('q-type').textContent={G:'梯度',S:'情景',P:'偏好',T:'两难',H:'习惯',C:'概念'}[q.type]||q.type;
  document.getElementById('q-text').textContent=q.text;
  let html='';
  q.options.forEach((o,i)=>{html+='<button class="opt-btn" onclick="selectOption('+i+')" id="opt-'+i+'">'+o.text+'</button>'});
  document.getElementById('q-options').innerHTML=html;
}

function selectOption(i){
  if(isMultiSelect){
    // 多选：切换选择状态
    const el=document.getElementById('opt-'+i);
    const idx=selectedOptions.indexOf(i);
    if(idx>=0){
      selectedOptions.splice(idx,1);
      el.classList.remove('multi-selected');
    }else{
      selectedOptions.push(i);
      el.classList.add('multi-selected');
    }
    document.getElementById('btn-confirm').disabled=selectedOptions.length===0;
  }else{
    // 单选：保持原有行为
    document.querySelectorAll('.opt-btn').forEach(e=>e.classList.remove('selected'));
    document.getElementById('opt-'+i).classList.add('selected');
    selectedOption=i;document.getElementById('btn-confirm').disabled=false;
  }
}

function confirmAnswer(){
  if(isMultiSelect){
    if(selectedOptions.length===0)return;
  }else{
    if(selectedOption<0)return;
  }
  document.getElementById('btn-confirm').disabled=true;document.getElementById('btn-back').disabled=true;
  const payload={session_id:sessionId};
  if(isMultiSelect) payload.option_indices=selectedOptions;
  else payload.option_index=selectedOption;
  fetch('/api/answer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
    .then(r=>r.json()).then(d=>{
      if(d.error){alert('出错了：'+d.error);document.getElementById('btn-confirm').disabled=false;document.getElementById('btn-back').disabled=false;return}
      if(d.done){document.getElementById('page-quiz').style.display='none';document.getElementById('page-result').style.display='block';showResult(d)}
      else showQuestion(d)
    }).catch(function(e){alert('网络错误，请检查网络连接');document.getElementById('btn-confirm').disabled=false;document.getElementById('btn-back').disabled=false})
}

function onBack(){
  if(document.getElementById('btn-back').textContent.includes('重选')){
    backToSelect();return
  }
  fetch('/api/go_back',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId})})
    .then(r=>r.json()).then(d=>{if(d.error){alert(d.error);return}showQuestion(d)})
}

function backToSelect(){
  sessionId='';
  document.querySelectorAll('.dir-tag.selected').forEach(e=>e.classList.remove('selected'));
  selectedDirs=[];document.getElementById('btn-start').disabled=true;
  document.getElementById('page-quiz').style.display='none';document.getElementById('page-result').style.display='none';
  document.getElementById('page-select').style.display='block';
}

// ===== 结果页 =====
function saveSessionBeforeLeave(){
  localStorage.setItem('ai_session_id',sessionId);
  // 把当前结果数据也存一份
  var rEl=document.getElementById('r-count');
  if(rEl&&rEl._resultData){
    localStorage.setItem('ai_result_data',JSON.stringify(rEl._resultData));
  }
}

function restoreSession(){
  var data=localStorage.getItem('ai_result_data');
  var sid=localStorage.getItem('ai_session_id');
  if(data&&sid){
    try{
      sessionId=sid;
      var r=JSON.parse(data);
      document.getElementById('page-welcome').style.display='none';
      document.getElementById('page-select').style.display='none';
      document.getElementById('page-quiz').style.display='none';
      document.getElementById('page-result').style.display='block';
      showResult(r);
      return true;
    }catch(e){}
  }
  return false;
}

function clearAndRestart(){
  localStorage.removeItem('ai_session_id');
  localStorage.removeItem('ai_result_data');
  location.reload();
}

function showResult(r){
  const sc=r.profile.scores, dims=['K','P','T','L','C'];
  // 保存结果数据到DOM元素属性上，供saveSessionBeforeLeave使用
  document.getElementById('r-count')._resultData=r;
  document.getElementById('r-count').textContent=r.profile.total_asked;

  // 画像类型
  const avg=dims.reduce((s,d)=>s+(sc[d]||0),0)/dims.filter(d=>sc[d]!==null).length;
  let label,tag;
  if(avg<1.2){label='🌱 探索者';tag='pb-探索者'}
  else if(avg<2.3){label='🚀 实践者';tag='pb-实践者'}
  else{label='🏆 领跑者';tag='pb-领跑者'}
  const badge=document.getElementById('r-badge');
  badge.textContent=label;badge.className='profile-badge '+tag;

  // 小雷达
  drawMiniRadar(sc,dims);

  // 维度进度条
  let miniHtml='';
  const weakDims=[];
  for(let d of dims){
    const s=sc[d]||0,pct=Math.min(s/3*100,100),c=DIM_COLORS[d];
    let level='低';if(s>=1)level='中';if(s>=2)level='高';
    if(s<1.5)weakDims.push({id:d,label:DIM_META[d].l,emoji:DIM_META[d].e});
    miniHtml+='<div class="dim-mini-item">'
      +'<span class="dm-label">'+DIM_META[d].e+' '+DIM_META[d].l+'</span>'
      +'<div class="dm-bar"><div class="dm-fill" style="width:'+pct+'%;background:'+c+'"></div></div>'
      +'<span class="dm-level" style="color:'+c+'">'+level+'</span>'
      +'</div>';
  }
  document.getElementById('r-mini-dims').innerHTML=miniHtml;

  // 短板
  const gapEl=document.getElementById('r-gap-list');
  if(weakDims.length>0){
    let g='';
    weakDims.forEach(w=>{
      g+='<div class="gap-item">'+w.emoji+' '+w.label+' — 需要加强基础</div>'
    });
    gapEl.innerHTML=g;
  }else{
    gapEl.innerHTML='<div class="gap-none">基础不错！可以直接挑战进阶课程</div>';
  }

  // 课程三级推荐
  renderTiers(sc,avg,dims,r.courses||[]);

  // 方向
  const dirA=r.direction_advice||[];
  let ch='';
  dirA.forEach(a=>{ch+='<span class="chip">→ '+a+'</span>'});
  document.getElementById('r-dir').innerHTML=ch||'<span style="color:#8e8e93;font-size:13px">你选的方向将指导课程筛选</span>';
}

// === 课程三级 ===
function renderTiers(scores,avg,dims,courses){
  // T1: 匹配的基础课（免费）
  const hasCourses=courses&&courses.length>0;

  // 根据分数推荐起点
  let recIdx=0; // 默认T1
  if(avg>=1.2&&avg<2.3)recIdx=1;
  else if(avg>=2.3)recIdx=2;

  let html='';

  // T1 — 基础入门（匹配的课程）
  html+='<div class="tier-card tier-1">'
    +'<div class="tier-head">'
    +'<span class="tier-name">基础入门</span>'
    +'<span class="tier-badge">免费课程</span>'
    +'</div>'
    +'<div class="tier-desc">针对你的画像匹配的免费入门课</div>';

  if(hasCourses){
    html+='<div style="margin-top:8px;display:flex;flex-direction:column;gap:6px">';
    courses.forEach(function(c){
      const ready=c.status==='ready';
      var courseUrl='/course/'+c.id;
      html+='<a href="'+courseUrl+'" class="course-card"'
        +(ready?'onclick="saveSessionBeforeLeave()"':'style="opacity:.5;pointer-events:none"')+'>'
        +'<div style="display:flex;align-items:center;gap:8px;padding:10px 12px;border-radius:10px;background:rgba(255,255,255,.5);border:1px solid rgba(0,0,0,.06)">'
        +'<span style="font-size:20px">'+(c.emoji||'📖')+'</span>'
        +'<div style="flex:1">'
        +'<div style="font-weight:600;font-size:14px">'+c.title+'</div>'
        +'<div style="font-size:12px;color:#636366">'+c.desc+'</div>'
        +'</div>'
        +(ready?'<span style="font-size:12px;color:#007aff;font-weight:500;white-space:nowrap">开始学习 →</span>'
          :'<span style="font-size:11px;color:#ff9500;font-weight:500;white-space:nowrap">制作中</span>')
        +'</div>'
        +'</a>';
    });
    html+='</div>';
  }else{
    html+='<div style="margin-top:8px;font-size:13px;color:#636366;padding:10px;border-radius:10px;background:rgba(255,255,255,.4);text-align:center">暂无匹配课程，更多免费课持续上线中...</div>';
  }
  html+='</div>';

  // T2 — 进阶
  html+='<div class="tier-card tier-2">'
    +'<div class="tier-head">'
    +'<span class="tier-name">进阶提升</span>'
    +'<span class="tier-badge">适中</span>'
    +'</div>'
    +'<div class="tier-desc">有一定基础后，深入学习技巧和方法</div>'
    +'<div class="tier-result">学完效果：能搭建自己的AI工作流</div>'
    +(recIdx===1?'<span class="tier-rec tag-fit">👈 推荐起点</span>':'')
    +'</div>';

  // T3 — 高阶
  html+='<div class="tier-card tier-3">'
    +'<div class="tier-head">'
    +'<span class="tier-name">高阶精通</span>'
    +'<span class="tier-badge">深度</span>'
    +'</div>'
    +'<div class="tier-desc">深入掌握AI原理与应用</div>'
    +'<div class="tier-result">学完效果：能独立设计AI方案</div>'
    +(recIdx===2?'<span class="tier-rec tag-adv">👈 推荐起点</span>':'')
    +'</div>';

  document.getElementById('r-tiers').innerHTML=html;
}

// 课程卡片点击（在新页面打开）
document.addEventListener('click',function(e){
  const card=e.target.closest('.course-card');
  if(card) return true; // 让链接正常跳转
});

// 尝试恢复上次的测试结果
restoreSession();

// === 小雷达 ===
function drawMiniRadar(sc,dims){
  const c=document.getElementById('miniRadar'),ctx=c.getContext('2d');
  const W=240,H=240,cx=120,cy=120,R=80,N=5,PI=Math.PI;
  ctx.clearRect(0,0,W,H);

  for(let r=1;r<=3;r++){
    const rr=R*r/3;ctx.beginPath();
    for(let i=0;i<N;i++){let a=-PI/2+i*2*PI/N,x=cx+rr*Math.cos(a),y=cy+rr*Math.sin(a);i===0?ctx.moveTo(x,y):ctx.lineTo(x,y)}
    ctx.closePath();ctx.strokeStyle='rgba(0,0,0,0.06)';ctx.lineWidth=1;ctx.stroke()
  }
  for(let i=0;i<N;i++){let a=-PI/2+i*2*PI/N;ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(cx+R*Math.cos(a),cy+R*Math.sin(a));ctx.strokeStyle='rgba(0,0,0,0.05)';ctx.lineWidth=1;ctx.stroke()}

  // 数据
  ctx.beginPath();
  for(let i=0;i<N;i++){
    let s=sc[dims[i]]||0,v=Math.min(s/3,1),r=R*v,a=-PI/2+i*2*PI/N;
    i===0?ctx.moveTo(cx+r*Math.cos(a),cy+r*Math.sin(a)):ctx.lineTo(cx+r*Math.cos(a),cy+r*Math.sin(a))
  }
  ctx.closePath();
  let g=ctx.createRadialGradient(cx,cy,0,cx,cy,R);g.addColorStop(0,'rgba(0,122,255,0.12)');g.addColorStop(1,'rgba(0,122,255,0.02)');
  ctx.fillStyle=g;ctx.fill();
  ctx.beginPath();
  for(let i=0;i<N;i++){
    let s=sc[dims[i]]||0,v=Math.min(s/3,1),r=R*v,a=-PI/2+i*2*PI/N;
    i===0?ctx.moveTo(cx+r*Math.cos(a),cy+r*Math.sin(a)):ctx.lineTo(cx+r*Math.cos(a),cy+r*Math.sin(a))
  }
  ctx.closePath();ctx.strokeStyle='rgba(0,122,255,0.4)';ctx.lineWidth=1.5;ctx.stroke();

  for(let i=0;i<N;i++){
    let s=sc[dims[i]]||0,v=Math.min(s/3,1),r=R*v,a=-PI/2+i*2*PI/N,x=cx+r*Math.cos(a),y=cy+r*Math.sin(a);
    ctx.beginPath();ctx.arc(x,y,3,0,2*PI);ctx.fillStyle=DIM_COLORS[dims[i]];ctx.fill();ctx.strokeStyle='#fff';ctx.lineWidth=1.5;ctx.stroke()
  }

  ctx.font='10px -apple-system, "PingFang SC", sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';
  for(let i=0;i<N;i++){
    let a=-PI/2+i*2*PI/N,lb=R+18,x=cx+lb*Math.cos(a),y=cy+lb*Math.sin(a);
    ctx.fillStyle='#8e8e93';ctx.fillText(DIM_META[dims[i]].e,x,y)
  }
}
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return HOME_HTML


@app.route('/api/start', methods=['POST'])
def api_start():
    data = request.get_json()
    dirs = data.get('dirs', ['A'])
    sid = uuid.uuid4().hex[:12]
    sess = Session(dirs, name=sid, qb=qb)
    sessions[sid] = sess
    q = sess.next_question()
    return jsonify({
        'session_id': sid,
        'question': question_to_dict(q),
        'progress': {'done': 0, 'total': 6}
    })


@app.route('/api/answer', methods=['POST'])
def api_answer():
    data = request.get_json()
    sid = data.get('session_id', '')
    sess = sessions.get(sid)
    if not sess:
        return jsonify({'error': '会话不存在'}), 404
    
    # 支持单选(int)和多选(list)
    indices = data.get('option_indices')
    if indices is None:
        indices = data.get('option_index', 0)
    
    sess.answer(indices)
    if sess.is_done():
        results = sess.get_results()
        rec = results['recommendation']
        p = sess.profile
        # 保存会话数据（Vercel只读环境跳过）
        try:
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '04_客户数据')
            os.makedirs(data_dir, exist_ok=True)
            with open(os.path.join(data_dir, f'{sid}.json'), 'w', encoding='utf-8') as f:
                json.dump(p.to_dict(), f, ensure_ascii=False, indent=2)
        except (OSError, PermissionError):
            pass  # Vercel只读文件系统，不报错
        courses = match_courses(p)
        del sessions[sid]
        return jsonify({
            'done': True,
            'profile': {
                'total_asked': p.total_asked,
                'scores': {d: p.get_dimension_score(d) for d in ['K','P','T','L','C']}
            },
            'level': rec['level'],
            'recommendations': rec['recommendations'],
            'direction_advice': rec['direction_advice'],
            'courses': courses,
        })
    else:
        next_q = sess.next_question()
        return jsonify({
            'done': False,
            'can_back': sess.can_go_back(),
            'question': question_to_dict(next_q),
            'progress': {'done': sess.profile.total_asked, 'total': 6}
        })


# ============================================================
# 课程匹配
# ============================================================
COURSE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '02_课程模板')

def match_courses(profile):
    """根据画像匹配推荐的课程"""
    scores = profile.get_all_scores()
    dirs = profile.directions
    dims = ['K','P','T','L','C']
    
    # 按分数从低到高排序维度
    scored_dims = [(scores.get(d,0) or 0, d) for d in dims]
    scored_dims.sort()
    
    matched = []
    used = set()
    
    # 先找精确匹配：(方向, 维度)
    for score_val, dim in scored_dims:
        if len(matched) >= 3:
            break
        for d in dirs:
            key = (d, dim)
            c = COURSE_MAP.get(key)
            if c and c['id'] not in used and c.get('status') == 'ready':
                matched.append(c)
                used.add(c['id'])
                break
    
    # 不够3个？用该维度的通用课
    if len(matched) < 3:
        for score_val, dim in scored_dims:
            if len(matched) >= 3:
                break
            if dim not in used:
                fb = COURSE_FALLBACK.get(dim)
                if fb and fb['id'] not in used:
                    matched.append(fb)
                    used.add(fb['id'])
                used.add(dim)
    
    return matched


@app.route('/api/go_back', methods=['POST'])
def api_go_back():
    data = request.get_json()
    sid = data.get('session_id', '')
    sess = sessions.get(sid)
    if not sess:
        return jsonify({'error': '会话不存在'}), 404
    prev_q = sess.go_back()
    if prev_q is None:
        return jsonify({'error': '没有上一题了'}), 400
    return jsonify({
        'question': question_to_dict(prev_q),
        'can_back': sess.can_go_back(),
        'progress': {'done': sess.profile.total_asked, 'total': 6}
    })


def _build_course_footer(course_id):
    """生成课程页底部：返回按钮（没有相关课程）"""
    parts = []
    parts.append('<div style="max-width:680px;margin:32px auto 0;padding:0 16px">')
    parts.append('<hr style="border:none;border-top:1px solid #e5e5ea;margin-bottom:20px">')
    parts.append('<div style="text-align:center;margin-bottom:40px">')
    parts.append('<a href="/" style="display:inline-flex;align-items:center;gap:6px;padding:10px 20px;border-radius:12px;background:rgba(0,122,255,.08);color:#007aff;text-decoration:none;font-size:15px;font-weight:500;transition:all .15s" onmouseover="this.style.background=\'rgba(0,122,255,.14)\'" onmouseout="this.style.background=\'rgba(0,122,255,.08)\'" onmousedown="this.style.transform=\'scale(.96)\'" onmouseup="this.style.transform=\'scale(1)\"">← 返回测试结果</a>')
    parts.append('</div>')
    parts.append('</div>')
    return '\n'.join(parts)


COMING_SOON_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AI学程 — 制作中</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;background:#f5f7fa;color:#1d1d1f;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:rgba(255,255,255,.88);backdrop-filter:blur(20px);border-radius:24px;padding:36px 28px;max-width:420px;width:100%;text-align:center;box-shadow:0 8px 40px rgba(0,0,0,.08);border:1px solid rgba(255,255,255,.6)}
.card h2{font-size:20px;margin:12px 0 6px}
.card .p1{font-size:14px;color:#636366;margin-bottom:16px;line-height:1.6}
.card .badge{display:inline-block;padding:4px 14px;border-radius:20px;font-size:12px;font-weight:600}
.card .badge-t2{background:rgba(255,149,0,.12);color:#ff9500}
.card .badge-t3{background:rgba(255,59,48,.08);color:#ff3b30}
.btn-back{display:inline-block;margin-top:18px;padding:10px 20px;border-radius:12px;background:rgba(0,122,255,.08);color:#007aff;text-decoration:none;font-size:15px;font-weight:500;transition:all .15s}
.btn-back:hover{background:rgba(0,122,255,.14)}
</style>
</head>
<body>
<div class="card">
<div style="font-size:48px">{EMOJI}</div>
<h2>{TITLE}</h2>
<p class="p1">这门课正在精心制作中，很快就能上线<br>先学同方向的免费课吧 😊</p>
<p><span class="badge badge-{LEVEL_LOWER}">{LEVEL} · 制作中</span></p>
<a class="btn-back" href="/">← 返回测试结果</a>
</div>
</body>
</html>'''


@app.route('/course/<course_id>')
def serve_course(course_id):
    """提供课程HTML页面"""
    # 先查COURSE_MAP
    course_info = None
    for c in list(COURSE_MAP.values()) + list(COURSE_FALLBACK.values()):
        if c['id'] == course_id and c.get('file'):
            course_info = c
            break

    if course_info:
        path = os.path.join(COURSE_DIR, course_info['file'])
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                html = f.read()
            # 注入返回按钮 + 相关课程
            footer = _build_course_footer(course_id)
            html = html.replace('</body>', footer + '\n</body>')
            # 注入相关CSS
            inject_css = '''\n/* 课程页底部注入 */
.course-footer{max-width:680px;margin:32px auto 0;padding:0 16px}\n'''
            html = html.replace('</style>', inject_css + '\n</style>')
            return html

    # 检查COMING_SOON
    cs = COMING_SOON.get(course_id)
    if cs:
        level_lower = cs['level'].lower()
        html = COMING_SOON_HTML.replace('{EMOJI}', cs['emoji']).replace('{TITLE}', cs['title']).replace('{LEVEL}', cs['level']).replace('{LEVEL_LOWER}', level_lower)
        return html, 200, {'Content-Type': 'text/html; charset=utf-8'}

    return '<h2>课程制作中...</h2><p>这门课还在路上，很快就好 😄</p>', 200, {'Content-Type': 'text/html; charset=utf-8'}


def question_to_dict(q):
    return {
        'id': q['id'],
        'text': q['text'],
        'dimension': q['dimension'],
        'type': q['type'],
        'multiple': q.get('multiple', False),
        'options': [{'text': o['text']} for o in q['options']]
    }


if __name__ == '__main__':
    print()
    print('=' * 50)
    print('  AI学程 Web 服务启动')
    print('  http://localhost:5800')
    print()
    print('  Ctrl+C 停止')
    print('=' * 50)
    print()
    try:
        from waitress import serve
        print('  使用 waitress (生产级服务器)')
        serve(app, host='0.0.0.0', port=5800, threads=8)
    except ImportError:
        from werkzeug.serving import run_simple
        print('  waitress 未安装，使用 Flask 内置服务器')
        print('  (建议 pip install waitress 提升性能)')
        print()
        run_simple('0.0.0.0', 5800, app, use_reloader=False)
