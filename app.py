import streamlit as st

from core.file_io import read_uploaded_file
from core.project_state import MODULES, create_empty_project, get_module_input, has_current, save_version
from core.diff_utils import diff_html
from core.run_module import run_module
from core.export_utils import export_docx_bytes

try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass

st.set_page_config(page_title="Podcast SOP Script Editor", layout="wide")

st.markdown(
    """
<style>
  /* 隐藏 Streamlit 顶部白条/菜单 */
  #MainMenu, header, footer { visibility: hidden; }
  section[data-testid="stSidebar"] > div { padding-top: 0; }
  .block-container { padding-top: 0.5rem; padding-bottom: 2rem; max-width: 1400px; }
  section[data-testid="stSidebar"] {
    border-right: 1px solid #e2e8f0;
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  }
  section[data-testid="stSidebar"] .stMarkdown h2 { font-size: 1rem; font-weight: 600; color: #475569; }
  .ds-preview {
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 18px;
    background: #fafbfc;
  }
  .ds-teleprompter { font-size: 18px; line-height: 1.85; }
  [data-testid="stTabs"] [role="tab"] { font-weight: 500; padding: 0.5rem 1rem; }
  div[data-testid="stVerticalBlock"] > div:has([data-testid="stButton"]) { gap: 0.5rem; }
  .stMarkdown h3 { color: #1e293b; font-weight: 600; }
  /* 文件上传区中文文案 */
  [data-testid='stFileUploaderDropzoneInstructions'] > div > span { display: none; }
  [data-testid='stFileUploaderDropzoneInstructions'] > div::before { content: '拖拽文件到此处'; }
  [data-testid='stFileUploaderDropzoneInstructions'] > div > small { display: none; }
  [data-testid='stFileUploaderDropzoneInstructions'] > div::after { content: '单文件最大 200MB，支持 DOCX、TXT、SRT'; display: block; }
  [data-testid='stFileDropzoneInstructions'] { text-indent: -9999px; line-height: 0; }
  [data-testid='stFileDropzoneInstructions']::after { content: '单文件最大 200MB，支持 DOCX、TXT、SRT'; line-height: initial; text-indent: 0; display: block; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("""<div style="display:flex;align-items:baseline;gap:0.75rem;margin:0.4rem 0 0.8rem 0;">
  <span style="font-size:28px;font-weight:700;letter-spacing:0.02em;">🎙 播客文案编辑器</span>
  <span style="font-size:14px;color:#64748b;">播客 / 公众号 / 社媒一体化文案工作台</span>
</div>
""", unsafe_allow_html=True)

if "project" not in st.session_state:
    st.session_state["project"] = create_empty_project()

project = st.session_state["project"]

# 项目标题、发稿用途 一行
top_row = st.columns([2, 1])
with top_row[0]:
    project_title = st.text_input("项目标题", value=project["meta"].get("title", ""), placeholder="例如：第12期｜AI创业访谈")
with top_row[1]:
    _options = ["公众号深度访谈", "播客口播", "社媒素材"]
    _idx = _options.index(project["meta"].get("purpose", "公众号深度访谈")) if project["meta"].get("purpose") in _options else 0
    purpose = st.selectbox("发稿用途", _options, index=_idx)

project["meta"]["title"] = project_title
project["meta"]["purpose"] = purpose

# 按发稿用途显示的模块：公众号 A->B->C，播客 A->B->E，社媒 A->B->C->D
PURPOSE_TABS = {
    "公众号深度访谈": [("A", "重清洗"), ("B", "逻辑重排"), ("C", "媒体成稿")],
    "播客口播": [("A", "重清洗"), ("B", "逻辑重排"), ("E", "播客朗读")],
    "社媒素材": [("A", "重清洗"), ("B", "逻辑重排"), ("C", "媒体成稿"), ("D", "传播增强")],
}
current_tabs = PURPOSE_TABS.get(purpose, PURPOSE_TABS["公众号深度访谈"])

with st.sidebar:
    st.header("项目控制台")

    st.subheader("输入区")
    uploaded = st.file_uploader(
        "上传逐字稿（docx / txt / srt）",
        type=["docx", "txt", "srt"],
        accept_multiple_files=False,
        help="拖拽文件到此处，或点击「浏览文件」选择。支持 docx、txt、srt，单文件最大 200MB。",
    )
    lang = st.selectbox("语言选择", ["中文", "英文", "双语"], index=0, key="meta_lang_ui")
    speaker_rules = st.text_area(
        "说话人标签规则（如：主持人/嘉宾/观众）",
        value="\n".join(project["meta"].get("speakers", ["主持人", "嘉宾"])),
        height=120,
        key="meta_speakers_ui",
    )

    st.subheader("模型设置区")
    provider = st.selectbox("模型选择", ["DeepSeek", "OpenAI", "Qwen", "本地"], index=0, key="provider_ui")
    temperature = st.slider("温度", min_value=0.0, max_value=1.0, value=project["settings"]["temperature"], step=0.05)
    max_tokens = st.slider(
        "最大长度（tokens）",
        min_value=256,
        max_value=32768,
        value=int(project["settings"]["max_tokens"]),
        step=256,
    )
    strict_no_add = st.toggle("严格不增内容", value=bool(project["settings"]["strict_no_add"]))

    project["meta"]["lang"] = {"中文": "zh", "英文": "en", "双语": "bi"}[lang]
    project["meta"]["speakers"] = [s.strip() for s in speaker_rules.splitlines() if s.strip()]
    provider_map = {"DeepSeek": "deepseek", "OpenAI": "openai", "Qwen": "qwen", "本地": "local"}
    project["settings"]["model_provider"] = provider_map[provider]
    project["settings"]["temperature"] = float(temperature)
    project["settings"]["max_tokens"] = int(max_tokens)
    project["settings"]["strict_no_add"] = bool(strict_no_add)

    if uploaded is not None:
        try:
            raw_text, _ext = read_uploaded_file(uploaded.name, uploaded.getvalue())
            project["input_raw"] = raw_text
            st.success("已读取并写入逐字稿。")
        except Exception as e:
            st.error(f"读取文件失败：{e}")

    st.subheader("项目状态")
    st.caption(f"逐字稿：{len(project['input_raw'])} 字")
    workflow_modules = [m for m, _ in current_tabs]
    st.caption(" | ".join(f"{m} {'✓' if has_current(project, m) else '○'}" for m in workflow_modules))

tabs = st.tabs([f"{m} {name}" for m, name in current_tabs])

for tab, (module, _) in zip(tabs, current_tabs, strict=True):
    with tab:
        st.subheader(f"模块 {module}")
        module_input = get_module_input(project, module, purpose)

        # 工具栏：运行、重新生成、保存、下一步
        btn_cols = st.columns([1, 1, 1, 2])
        with btn_cols[0]:
            can_run = bool(module_input.strip())
            if st.button("▶ 运行本模块", key=f"{module}_run", disabled=not can_run):
                with st.spinner("正在调用模型生成..."):
                    try:
                        result = run_module(
                            module_name=module,
                            input_text=module_input,
                            settings=dict(project["settings"]),
                        )
                        project[module]["current"] = result["text"]
                        if f"{module}_editor" in st.session_state:
                            del st.session_state[f"{module}_editor"]
                        if not result["post_check_ok"]:
                            st.warning(f"后置校验提示：{result['post_check_msg']}")
                    except Exception as e:
                        st.error(f"生成失败：{e}")
        with btn_cols[1]:
            can_regen = bool(project[module]["current"].strip()) and can_run
            if st.button("🔄 重新生成", key=f"{module}_regen", disabled=not can_regen):
                save_version(project, module, project[module]["current"], settings_snapshot=dict(project["settings"]))
                with st.spinner("正在重新生成..."):
                    try:
                        result = run_module(
                            module_name=module,
                            input_text=module_input,
                            settings=dict(project["settings"]),
                        )
                        project[module]["current"] = result["text"]
                        if f"{module}_editor" in st.session_state:
                            del st.session_state[f"{module}_editor"]
                        if not result["post_check_ok"]:
                            st.warning(f"后置校验提示：{result['post_check_msg']}")
                    except Exception as e:
                        st.error(f"重新生成失败：{e}")
        with btn_cols[2]:
            if st.button("💾 保存为版本", key=f"{module}_save_version"):
                edited = st.session_state.get(f"{module}_editor", project[module]["current"]) or project[module]["current"]
                if (edited or "").strip():
                    save_version(project, module, edited, settings_snapshot=dict(project["settings"]))
                    st.success("已保存为新版本。")
                else:
                    st.warning("内容为空，未保存。")
        with btn_cols[3]:
            can_next = bool(project[module]["current"].strip())
            if st.button("下一步 →", key=f"{module}_next", disabled=not can_next):
                st.success("已确认当前版本，可进入下一模块。")

        # 大型主编辑器（通过 session_state 初始化，避免与 value 冲突）
        if f"{module}_editor" not in st.session_state:
            st.session_state[f"{module}_editor"] = project[module]["current"]
        edited_content = st.text_area(
            "主编辑区",
            height=560,
            key=f"{module}_editor",
            label_visibility="collapsed",
            placeholder="运行本模块后将在此显示生成结果，可直接编辑…",
        )
        # 同步编辑内容到 current（用于导出、保存为版本等）
        project[module]["current"] = edited_content

        opt_col1, opt_col2 = st.columns(2)
        with opt_col1:
            with st.expander("📊 差异对比", expanded=False):
                original = module_input
                output = project[module]["current"]
                gran = st.radio(
                    "对比粒度",
                    options=["按行", "按词"],
                    horizontal=True,
                    key=f"{module}_diff_gran",
                )
                st.components.v1.html(
                    diff_html(original, output, granularity="word" if gran.startswith("按词") else "line"),
                    height=300,
                    scrolling=True,
                )
        with opt_col2:
            history = project[module]["history"]
            with st.expander("📜 历史版本", expanded=False):
                if history:
                    options = [f"{h['version_id']}  ({h['time']})" for h in reversed(history)]
                    selected = st.selectbox("回滚到", options=options, key=f"{module}_rollback_select")
                    if st.button("回滚", key=f"{module}_rollback_btn"):
                        version_id = selected.split()[0]
                        for h in reversed(history):
                            if h["version_id"] == version_id:
                                project[module]["current"] = h["text"]
                                st.success(f"已回滚到 {version_id}")
                                st.rerun()
                                break
                else:
                    st.caption("暂无历史版本。")

st.divider()
st.markdown("### 📤 导出")
export_col1, export_col2, export_col3 = st.columns([1, 1, 2])
with export_col1:
    export_purpose = st.selectbox("发稿用途（导出源）", ["公众号深度访谈", "播客口播", "社媒素材"], index=0)
with export_col2:
    export_format = st.selectbox("导出格式", ["markdown", "txt", "docx"], index=0)
with export_col3:
    purpose_to_module = {
        "公众号深度访谈": "C",
        "播客口播": "E",
        "社媒素材": "D",
    }
    export_module = purpose_to_module[export_purpose]
    versions = project[export_module]["history"]
    version_options = ["current"] + [h["version_id"] for h in reversed(versions)]
    chosen_version = st.selectbox("选择版本", options=version_options, index=0)
    if chosen_version == "current":
        export_text = project[export_module]["current"].strip()
    else:
        export_text = ""
        for h in reversed(versions):
            if h["version_id"] == chosen_version:
                export_text = (h["text"] or "").strip()
                break

    filename_base = project["meta"].get("title") or f"module-{export_module}"
    filename_base = filename_base.strip() or f"module-{export_module}"

    if export_format == "docx":
        try:
            docx_bytes = export_docx_bytes(text=export_text, title=project["meta"].get("title") or None)
            st.download_button(
                f"下载 DOCX（模块 {export_module} / {chosen_version}）",
                data=docx_bytes,
                file_name=f"{filename_base}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                disabled=not bool(export_text),
            )
        except Exception as e:
            st.error(f"DOCX 导出不可用：{e}")
    else:
        ext = "md" if export_format == "markdown" else "txt"
        st.download_button(
            f"下载（模块 {export_module} / {chosen_version}）",
            data=export_text,
            file_name=f"{filename_base}.{ext}",
            disabled=not bool(export_text),
        )
