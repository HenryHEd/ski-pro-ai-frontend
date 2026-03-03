#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ski Pro AI — 轻量级前端（前后端分离版）
==========================================
本文件是纯展示层，不含任何 AI/CV 计算代码。
所有分析任务由 Modal 后端 API 完成。

本地运行：
    MODAL_API_URL=https://xxx--ski-pro-ai-api-web-api.modal.run \
    streamlit run app_frontend.py

免费部署到 Streamlit Cloud：
    1. 将 frontend/ 目录推到 GitHub 仓库
    2. Streamlit Cloud → New app → 选该仓库 → main file: app_frontend.py
    3. Secrets 里添加 MODAL_API_URL = <你的 Modal API 地址>

绑定自定义域名 skiproai.online：
    Streamlit Cloud → Settings → Custom domain → 填入 skiproai.online
"""
import os
import streamlit as st
import time
import requests

# 必须在导入 modal 之前注入 Token
if "MODAL_TOKEN_ID" in st.secrets:
    os.environ["MODAL_TOKEN_ID"] = st.secrets["MODAL_TOKEN_ID"]
    os.environ["MODAL_TOKEN_SECRET"] = st.secrets["MODAL_TOKEN_SECRET"]

# ── 后端 API 地址
#    优先级：st.secrets["MODAL_API_URL"] > 环境变量 MODAL_API_URL
try:
    API_URL = st.secrets["MODAL_API_URL"].rstrip("/")
except Exception:
    API_URL = os.environ.get("MODAL_API_URL", "").rstrip("/")

# ── 轮询参数 ────────────────────────────────────────────────────────────────
POLL_INTERVAL_SEC  = 5     # 每 5 秒轮询一次
MAX_POLL_ATTEMPTS  = 180   # 最多等 15 分钟（超时提示）

import io


# ════════════════════════════════════════════════════════════════════════════
# 页面配置
# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Ski Pro AI · 滑雪诊断系统",
    page_icon="⛷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 全局样式（与原 app.py 保持一致的 Apple 风格）──────────────────────────
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background: #f5f5f7 !important;
    color: #1d1d1f !important;
    font-family: -apple-system, "SF Pro Display", "PingFang SC",
                 "Helvetica Neue", sans-serif !important;
}
.stApp { background: radial-gradient(circle at 75% 8%,
    rgba(255,255,255,0.92) 0%, #f5f5f7 60%) !important; }
[data-testid="stHeader"] {
    background: rgba(245,245,247,0.82) !important;
    backdrop-filter: blur(20px) !important;
    border-bottom: 1px solid rgba(0,0,0,0.06) !important;
}
.block-container { padding-top: 0 !important; max-width: 1100px; }
.apple-card {
    background: rgba(255,255,255,0.72);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 2rem 2.2rem;
    margin-bottom: 1.4rem;
    border: 1px solid rgba(255,255,255,0.45);
    box-shadow: 0 8px 32px rgba(31,38,135,0.07);
}
.section-label {
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.12em;
    color: #aeaeb2; text-transform: uppercase;
    margin-bottom: 0.6rem; display: block;
}
/* 步骤条 */
.step-bar { display:flex; align-items:center; justify-content:center;
    gap:0; margin:0 auto 2.4rem; max-width:440px; }
.step-item { display:flex; flex-direction:column; align-items:center;
    gap:0.3rem; flex:1; }
.step-dot { width:28px; height:28px; border-radius:50%;
    background:#e5e5ea; display:flex; align-items:center;
    justify-content:center; font-size:0.75rem; font-weight:600; color:#aeaeb2; }
.step-dot.active { background:#0071e3; color:#fff;
    box-shadow:0 2px 10px rgba(0,113,227,0.35); }
.step-dot.done   { background:#34c759; color:#fff; }
.step-line { flex:1; height:2px; background:#e5e5ea; margin-bottom:1.4rem; }
.step-line.done  { background:#34c759; }
.step-label { font-size:0.68rem; color:#aeaeb2; font-weight:500; letter-spacing:0.04em; }
.step-label.active { color:#0071e3; font-weight:600; }
.step-label.done   { color:#34c759; }
/* 主按钮 */
div.stButton > button {
    background:#0071e3 !important; color:#fff !important;
    border:none !important; border-radius:12px !important;
    font-weight:500 !important; font-size:1rem !important;
    padding:0.65rem 2rem !important;
    box-shadow:0 2px 8px rgba(0,113,227,0.28) !important;
    width:100% !important;
}
div.stButton > button:hover { background:#0077ed !important; }
/* metric */
[data-testid="stMetricValue"] { color:#0071e3 !important;
    font-size:1.9rem !important; font-weight:600 !important; }
[data-testid="stMetricLabel"] { color:#6e6e73 !important; font-size:0.8rem !important; }
/* 进度条 */
[data-testid="stProgressBar"] > div > div > div {
    background:#0071e3 !important; border-radius:4px !important; }
/* 下载按钮 */
div.stDownloadButton > button {
    background:#fff !important; color:#0071e3 !important;
    border:1.5px solid #0071e3 !important; border-radius:12px !important; }
div.stDownloadButton > button:hover {
    background:#0071e3 !important; color:#fff !important; }
.video-label { color:#0071e3; font-weight:600; font-size:0.9rem;
    letter-spacing:0.04em; margin-bottom:0.5rem; }
.pulse-dot { display:inline-block; width:8px; height:8px;
    border-radius:50%; background:#0071e3;
    animation:pulse 1.4s ease-in-out infinite;
    margin-right:6px; vertical-align:middle; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1);}
    50%{opacity:0.3;transform:scale(0.6);} }
hr { border:none !important;
    border-top:1px solid rgba(0,0,0,0.08) !important; margin:1.5rem 0 !important; }
[data-testid="stAlert"] { border-radius:14px !important; }
@keyframes fadeSlideUp { from{opacity:0;transform:translateY(20px);}
    to{opacity:1;transform:translateY(0);} }
.animate-in { animation:fadeSlideUp 0.52s cubic-bezier(0.25,0.46,0.45,0.94) both; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# Session State 初始化
# ════════════════════════════════════════════════════════════════════════════
_STAGES = ["upload", "analyzing", "result"]

def _init():
    defaults = {
        "stage":          "upload",
        "job_id":         None,
        "user_name":      "",
        "video_filename": "",
        "video_bytes":    None,
        "poll_count":     0,
        "result_meta":    None,   # Modal 返回的完整 JSON
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()


# ════════════════════════════════════════════════════════════════════════════
# 工具函数
# ════════════════════════════════════════════════════════════════════════════
def _check_api_url():
    if not API_URL:
        st.error(
            "⚠️ 未配置 Modal API 地址！\n\n"
            "请在环境变量或 Streamlit Secrets 中设置：\n"
            "`MODAL_API_URL = https://xxx--ski-pro-ai-api-web-api.modal.run`"
        )
        st.stop()


def _submit_video(video_bytes: bytes, filename: str) -> str:
    # 如果你的 Secrets 填的是 https://henryhed--analyze.modal.run
    # 那么这里直接使用 API_URL，不要加 /analyze
    resp = requests.post(
        f"{API_URL}", # 去掉 /analyze
        files={"video": (filename, video_bytes, "video/mp4")},
        timeout=60,
    )
    # ... 其余不变
    resp.raise_for_status()
    return resp.json()["job_id"]


def _poll_status(job_id: str) -> dict:
    """GET /status/{job_id}，返回 meta dict。"""
    resp = requests.get(f"{API_URL}/status/{job_id}", timeout=15)
    resp.raise_for_status()
    return resp.json()


def _download_file(job_id: str, file_key: str) -> bytes:
    """GET /file/{job_id}/{file_key}，返回文件原始字节。"""
    resp = requests.get(f"{API_URL}/file/{job_id}/{file_key}", timeout=60)
    resp.raise_for_status()
    return resp.content


# ════════════════════════════════════════════════════════════════════════════
# 步骤指示器
# ════════════════════════════════════════════════════════════════════════════
_STAGE_LABEL = {"upload": "上传", "analyzing": "分析中", "result": "报告"}

def _render_steps():
    cur_idx = _STAGES.index(st.session_state.stage)
    dots, lines = [], []
    for i, s in enumerate(_STAGES):
        lbl = _STAGE_LABEL[s]
        if i < cur_idx:
            dots.append(f'<div class="step-dot done">✓</div>'
                        f'<div class="step-label done">{lbl}</div>')
            lines.append('<div class="step-line done"></div>')
        elif i == cur_idx:
            dots.append(f'<div class="step-dot active">{i+1}</div>'
                        f'<div class="step-label active">{lbl}</div>')
            if i < len(_STAGES) - 1:
                lines.append('<div class="step-line"></div>')
        else:
            dots.append(f'<div class="step-dot">{i+1}</div>'
                        f'<div class="step-label">{lbl}</div>')
            if i < len(_STAGES) - 1:
                lines.append('<div class="step-line"></div>')

    html = ""
    for i, d in enumerate(dots):
        html += f'<div class="step-item">{d}</div>'
        if i < len(lines):
            html += lines[i]
    st.markdown(f'<div class="step-bar animate-in">{html}</div>',
                unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# Hero 品牌头部
# ════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="animate-in" style="text-align:center;padding:3rem 0 1.6rem">
  <div style="font-size:3rem;font-weight:700;letter-spacing:-0.045em;
              color:#1d1d1f;line-height:1.05">Ski Pro AI</div>
  <div style="font-size:1rem;color:#6e6e73;margin-top:0.5rem;
              font-weight:300;letter-spacing:0.01em">
    专业级滑雪姿态数字分析系统
  </div>
  <div style="font-size:0.82rem;color:#aeaeb2;margin-top:0.25rem;
              letter-spacing:0.02em">
    每一个转弯，都是一次数据的升华。
  </div>
</div>
""", unsafe_allow_html=True)

_render_steps()
_check_api_url()


# ════════════════════════════════════════════════════════════════════════════
# STAGE 1 — 上传
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.stage == "upload":

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown(
            '<span class="section-label">上传视频</span>'
            '<div style="font-size:1.5rem;font-weight:600;color:#1d1d1f;margin-bottom:0.25rem">'
            '上传您的滑雪视频</div>'
            '<p style="color:#6e6e73;font-size:0.88rem;margin-bottom:1rem">'
            '支持 MP4 / MOV 格式 · 建议时长 30 秒至 5 分钟</p>',
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader(
            "拖拽或点击上传视频",
            type=["mp4", "MP4", "mov", "MOV"],
            label_visibility="collapsed",
        )
        st.markdown("<br>", unsafe_allow_html=True)
        user_name = st.text_input(
            "昵称（用于报告署名）",
            placeholder="例如：张教练",
            value=st.session_state.user_name,
        )

    with col_right:
        st.markdown("""
<div class="apple-card animate-in">
  <span class="section-label">AI 深度分析</span>
  <div style="font-size:1.4rem;font-weight:600;color:#1d1d1f;margin-bottom:0.8rem">
    云端 AI 实时诊断
  </div>
  <div style="font-size:0.85rem;color:#3a3a3c;line-height:2">
    📡 &nbsp;5 维战力雷达图 · 综合评分<br>
    🤖 &nbsp;AI 教练专业建议报告<br>
    🎬 &nbsp;原片 vs 骨骼标注对比视频<br>
    📐 &nbsp;立刃角 · 膝盖角 · 重心 · 相似度全指标
  </div>
  <div style="margin-top:1.2rem;padding:0.8rem 1rem;background:rgba(0,113,227,0.06);
              border-radius:12px;border:1px solid rgba(0,113,227,0.12);
              font-size:0.82rem;color:#0071e3;font-weight:600">
    ⚡ 由 NYU 算法团队 AI 支持 · 按需启动
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    btn_col, _ = st.columns([1, 2])
    with btn_col:
        start_btn = st.button("开始 AI 分析  →", use_container_width=True)



# ════════════════════════════════════════════════════════════════════════════
# 工具函数定义 (必须放在调用逻辑之前)
# ════════════════════════════════════════════════════════════════════════════

# 统一放在 _init() 之后，UI 逻辑之前



# 2. 优化 STAGE 1 的逻辑
if st.session_state.stage == "upload":
    # ... 原有的 UI 代码 ...
    
    if start_btn:
    if not uploaded:
        st.warning("请先上传滑雪视频！")
    else:
        try:
            # 读取视频字节
            video_bytes = uploaded.read()

            # 调用 Modal API（直接上传视频）
            job_id = _submit_video(video_bytes, uploaded.name)

            # 存 session
            st.session_state.job_id = job_id
            st.session_state.user_name = user_name.strip()
            st.session_state.video_filename = uploaded.name
            st.session_state.video_bytes = video_bytes
            st.session_state.stage = "analyzing"
            st.session_state.poll_count = 0

            st.rerun()

        except Exception as e:
            st.error(f"提交失败：{e}\n\n请检查 Modal API 是否已部署。")

# ════════════════════════════════════════════════════════════════════════════
# STAGE 2 — 轮询等待
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "analyzing":

    job_id = st.session_state.job_id
    _, mid_col, _ = st.columns([1, 4, 1])
    with mid_col:
        st.markdown('<div class="apple-card animate-in">', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:1.6rem;font-weight:600;color:#1d1d1f;'
            'letter-spacing:-0.02em;margin-bottom:0.25rem">☁️ AI数据库 云端分析中…</div>'
            '<p style="color:#6e6e73;font-size:0.88rem;margin-bottom:1.2rem">'
            'AI 正在提取骨骼、计算立刃角、生成诊断报告，请稍候（通常 2–5 分钟）</p>',
            unsafe_allow_html=True,
        )

        poll   = st.session_state.poll_count
        pct    = min(int(poll / MAX_POLL_ATTEMPTS * 95) + 3, 95)
        bar    = st.progress(pct, text=f"分析中… 已等待约 {poll * POLL_INTERVAL_SEC} 秒")
        status_ph = st.empty()
        status_ph.markdown(
            f'<p style="color:#6e6e73;font-size:0.88rem">'
            f'<span class="pulse-dot"></span>'
            f'任务 ID：<code>{job_id}</code></p>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if poll >= MAX_POLL_ATTEMPTS:
            st.error("分析超时（超过 15 分钟）。请检查 Modal 后端日志，或重新上传视频。")
            if st.button("← 重新上传"):
                for k in ["stage", "job_id", "poll_count", "result_meta"]:
                    st.session_state.pop(k, None)
                st.rerun()
        else:
            # 查询一次状态
            try:
                meta = _poll_status(job_id)
            except Exception as e:
                st.warning(f"查询状态暂时失败（{e}），将继续重试…")
                meta = {"status": "processing"}

            if meta.get("status") == "done":
                st.session_state.result_meta = meta
                st.session_state.stage       = "result"
                st.rerun()
            elif meta.get("status") == "error":
                st.error(f"后端分析出错：{meta.get('error', '未知错误')}")
                if st.button("← 重新上传"):
                    for k in ["stage", "job_id", "poll_count", "result_meta"]:
                        st.session_state.pop(k, None)
                    st.rerun()
            else:
                st.session_state.poll_count += 1
                time.sleep(POLL_INTERVAL_SEC)
                st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# STAGE 3 — 结果展示
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "result":
    import plotly.graph_objects as go
    from datetime import datetime

    meta      = st.session_state.result_meta or {}
    job_id    = st.session_state.job_id
    user_name = st.session_state.user_name
    stats     = meta.get("stats", {})
    avail     = meta.get("available_files", [])

    report_date = datetime.now().strftime("%Y 年 %m 月 %d 日")
    report_no   = f"SKILAB-{datetime.now().strftime('%Y%m%d')}-{job_id[:6].upper()}"

    # ── 荣誉勋章 ──────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:1.4rem;'
        f'background:linear-gradient(135deg,rgba(0,113,227,0.08),rgba(52,170,220,0.06));'
        f'border:1.5px solid rgba(0,113,227,0.2);border-radius:20px;'
        f'padding:1.4rem 2rem;margin-bottom:1.6rem;animate-in" class="animate-in">'
        f'<div style="width:72px;height:72px;border-radius:50%;'
        f'background:linear-gradient(145deg,#0071e3,#34aadc);'
        f'display:flex;align-items:center;justify-content:center;'
        f'font-size:2rem;box-shadow:0 4px 16px rgba(0,113,227,0.35);flex-shrink:0">⛷</div>'
        f'<div>'
        f'<div style="font-size:1.12rem;font-weight:700;color:#1d1d1f">'
        f'Ski Pro AI 云端诊断报告</div>'
        f'<div style="font-size:0.8rem;color:#6e6e73;margin-top:0.2rem">'
        f'{user_name} · {report_date}</div>'
        f'<div style="font-size:0.72rem;font-family:monospace;color:#0071e3;'
        f'background:rgba(0,113,227,0.08);border-radius:6px;padding:2px 8px;'
        f'margin-top:0.4rem;display:inline-block">报告编号：{report_no}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # ── 第一行：雷达图 + 教练报告图 ───────────────────────────────────────
    radar_col, coach_col = st.columns([1, 1])

    with radar_col:
        st.markdown(
            '<span class="section-label">5 维战力雷达图</span>'
            '<div style="font-size:1.1rem;font-weight:600;color:#1d1d1f;margin-bottom:0.8rem">'
            '综合战力评估</div>',
            unsafe_allow_html=True,
        )
        sim    = min(stats.get("avg_similarity_score", 70), 100)
        edge   = min(stats.get("max_edge_angle", 35) / 45 * 100, 100)
        knee   = min(100 - abs(stats.get("avg_knee_angle", 145) - 145) / 1.2, 100)
        lean   = min(100 - abs(stats.get("avg_lean_angle", 12) - 12) / 0.8, 100)
        smooth = round(sim * 0.4 + edge * 0.3 + knee * 0.3, 1)

        cats  = ["稳定性", "立刃角度", "爆发力", "重心控制", "动作流畅度"]
        uvals = [round(sim,1), round(edge,1), round(knee,1), round(lean,1), round(smooth,1)]
        pvals = [92, 88, 85, 90, 87]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=uvals + [uvals[0]], theta=cats + [cats[0]],
            fill="toself", fillcolor="rgba(0,113,227,0.18)",
            line=dict(color="#0071e3", width=2.5), name=user_name,
            hovertemplate="%{theta}: %{r:.1f}<extra></extra>",
        ))
        fig.add_trace(go.Scatterpolar(
            r=pvals + [pvals[0]], theta=cats + [cats[0]],
            fill="toself", fillcolor="rgba(52,199,89,0.08)",
            line=dict(color="#34c759", width=1.5, dash="dot"), name="冠军参考",
            hovertemplate="%{theta}: %{r:.1f}<extra></extra>",
        ))
        fig.update_layout(
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, range=[0, 100],
                    tickfont=dict(size=10, color="#aeaeb2"),
                    gridcolor="rgba(0,0,0,0.08)", linecolor="rgba(0,0,0,0.08)"),
                angularaxis=dict(
                    tickfont=dict(size=12, color="#1d1d1f", family="PingFang SC"),
                    gridcolor="rgba(0,0,0,0.06)", linecolor="rgba(0,0,0,0.1)"),
            ),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=30, b=30, l=60, r=60),
            legend=dict(orientation="h", yanchor="bottom", y=-0.15,
                        xanchor="center", x=0.5, font=dict(size=11, color="#6e6e73")),
            height=380,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with coach_col:
        st.markdown('<span class="section-label">AI 教练报告</span>',
                    unsafe_allow_html=True)
        if "coach_report_png" in avail:
            try:
                img_bytes = _download_file(job_id, "coach_report_png")
                st.image(img_bytes, use_container_width=True)
            except Exception:
                st.info("教练报告图加载失败，请从下方下载")
        else:
            st.info("教练报告图尚未生成")

    # ── 第二行：核心指标 ───────────────────────────────────────────────────
    if stats:
        st.markdown('<span class="section-label">核心指标数据</span>',
                    unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("相似度得分",   f"{stats.get('avg_similarity_score', 0):.1f}")
        m2.metric("最大立刃角",   f"{stats.get('max_edge_angle', 0):.1f}°")
        m3.metric("平均膝盖角",   f"{stats.get('avg_knee_angle', 0):.1f}°")
        m4.metric("平均身体倾斜", f"{stats.get('avg_lean_angle', 0):.1f}°")
        st.divider()

    # ── 第三行：分屏对比视频 ───────────────────────────────────────────────
    st.markdown(
        '<span class="section-label">左右分屏对比</span>'
        '<div style="font-size:1.1rem;font-weight:600;color:#1d1d1f;margin-bottom:1rem">'
        '原片 vs AI 骨骼标注</div>',
        unsafe_allow_html=True,
    )
    v_col1, v_col2 = st.columns(2)
    with v_col1:
        st.markdown('<div class="video-label">原片回放</div>', unsafe_allow_html=True)
        if st.session_state.video_bytes:
            st.video(st.session_state.video_bytes)
    with v_col2:
        st.markdown('<div class="video-label">AI 骨骼纠偏</div>', unsafe_allow_html=True)
        _video_key = "comparison_video" if "comparison_video" in avail else "skeleton_video"
        if _video_key in avail:
            try:
                vid_bytes = _download_file(job_id, _video_key)
                st.video(vid_bytes)
            except Exception:
                st.info("骨骼视频加载失败，请从下方下载")
        else:
            st.info("骨骼视频未生成")

    st.divider()

    # ── 第四行：战力报告图 ─────────────────────────────────────────────────
    if "ski_report_jpg" in avail:
        st.markdown('<span class="section-label">战力诊断报告</span>',
                    unsafe_allow_html=True)
        try:
            report_bytes = _download_file(job_id, "ski_report_jpg")
            st.image(report_bytes, use_container_width=True)
        except Exception:
            st.info("战力报告图加载失败，请从下方下载")
        st.divider()

    # ── 第五行：AI 教练寄语 ────────────────────────────────────────────────
    def _coach_quote(s: dict) -> str:
        if not s:
            return "每一帧数据背后，都是你对滑雪的热爱与坚持。继续练习，你的姿态会越来越接近冠军水准。"
        sim  = s.get("avg_similarity_score", 0)
        edge = s.get("max_edge_angle", 0)
        knee = s.get("avg_knee_angle", 145)
        if sim >= 85:
            op = f"你的整体姿态相似度达到 {sim:.1f}，已超越 {min(int(sim), 97)}% 的雪友，"
        elif sim >= 70:
            op = f"你的整体姿态相似度为 {sim:.1f}，正处于快速进步的黄金区间，"
        else:
            op = f"你的姿态基础扎实，相似度得分 {sim:.1f} 有较大提升空间，"
        if edge >= 40:
            mid = f"入弯立刃角高达 {edge:.1f}°，展现出出色的激进风格。"
        elif edge >= 25:
            mid = f"入弯立刃角为 {edge:.1f}°，说明你已掌握弧线转弯的核心要领。"
        else:
            mid = f"入弯立刃角为 {edge:.1f}°，建议专项训练压刃技术以提升弯道速度。"
        tail = ("膝盖弯曲角度控制到位，重心稳定是你最大的优势，继续保持！"
                if abs(knee - 145) <= 10
                else "建议重点强化后程压板稳定性与膝盖缓冲训练，潜力巨大。")
        return op + mid + tail

    st.markdown(
        f'<span class="section-label">AI 教练寄语</span>'
        f'<div style="background:linear-gradient(135deg,rgba(0,113,227,0.07),rgba(90,200,250,0.06));'
        f'border-left:4px solid #0071e3;border-radius:0 16px 16px 0;'
        f'padding:1.4rem 1.8rem;font-size:1.05rem;color:#1d1d1f;'
        f'line-height:1.7;font-style:italic">"{_coach_quote(stats)}"'
        f'<div style="font-size:0.78rem;color:#aeaeb2;margin-top:0.8rem;font-style:normal">'
        f'— Ski Pro AI 教练系统 · {report_date}</div></div>',
        unsafe_allow_html=True,
    )
    st.divider()

    # ── 下载区 ─────────────────────────────────────────────────────────────
    st.markdown('<span class="section-label">下载报告</span>', unsafe_allow_html=True)
    dl_cols = st.columns(4)
    _dl_map = [
        ("ski_report_jpg",   "战力报告 JPG",   f"Ski_Report_{user_name}.jpg",   "image/jpeg"),
        ("coach_report_png", "教练报告 PNG",   f"Ski_Coach_{user_name}.png",    "image/png"),
        ("skeleton_video",   "骨骼视频 MP4",   f"Ski_Skeleton_{user_name}.mp4", "video/mp4"),
        ("analysis_csv",     "骨骼数据 CSV",   f"Ski_Analysis_{user_name}.csv", "text/csv"),
    ]
    for col, (key, label, fname, mime) in zip(dl_cols, _dl_map):
        if key in avail:
            try:
                data = _download_file(job_id, key)
                col.download_button(label, data=data, file_name=fname,
                                    mime=mime, use_container_width=True)
            except Exception:
                col.caption(f"⚠ {label} 暂时无法下载")

    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_c, _ = st.columns([1, 1, 1])
    with btn_c:
        if st.button("重新分析", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    st.markdown(
        '<div style="text-align:center;color:#aeaeb2;font-size:0.78rem;'
        'margin-top:3rem;padding-bottom:2rem;letter-spacing:0.03em">'
        'Ski Pro AI · Powered by Modal + MediaPipe · skiproai.online'
        '</div>',
        unsafe_allow_html=True,
    )
