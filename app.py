import streamlit as st
import tempfile
import os
from markitdown import MarkItDown
import google.generativeai as genai

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DocumentExtractor",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background-color: #0e0e11; color: #e8e8e8; }
[data-testid="stSidebar"] { background-color: #16161a; border-right: 1px solid #2a2a2e; }
h1 { font-family: 'DM Mono', monospace !important; font-size: 1.6rem !important; color: #ffffff !important; }
h2, h3 { font-family: 'DM Sans', sans-serif !important; font-weight: 600 !important; color: #ffffff !important; }
.metric-row { display: flex; gap: 1rem; margin: 1rem 0; }
.metric-box { background: #1c1c21; border: 1px solid #2a2a2e; border-radius: 6px; padding: 0.8rem 1.2rem; flex: 1; text-align: center; }
.metric-box .value { font-family: 'DM Mono', monospace; font-size: 1.4rem; color: #c8f565; }
.metric-box .label { font-size: 0.72rem; color: #666; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 2px; }
.tag { display: inline-block; background: #1e2a14; color: #c8f565; border: 1px solid #3a5020; border-radius: 4px; padding: 2px 10px; font-size: 0.75rem; font-family: 'DM Mono', monospace; margin-right: 6px; }
.divider { border: none; border-top: 1px solid #2a2a2e; margin: 1.5rem 0; }
[data-testid="stTextInput"] input { background: #1c1c21 !important; border: 1px solid #2a2a2e !important; color: #e8e8e8 !important; border-radius: 6px !important; }
.stButton > button { background: #c8f565 !important; color: #0e0e11 !important; border: none !important; border-radius: 6px !important; font-family: 'DM Sans', sans-serif !important; font-weight: 600 !important; padding: 0.4rem 1.2rem !important; }
.stButton > button:hover { background: #d4f77a !important; }
[data-testid="stFileUploader"] { background: #16161a !important; border: 1px dashed #2a2a2e !important; border-radius: 8px !important; }
code { font-family: 'DM Mono', monospace !important; background: #1c1c21 !important; color: #c8f565 !important; }
[data-testid="stExpander"] { background: #16161a !important; border: 1px solid #2a2a2e !important; border-radius: 8px !important; }
[data-testid="stAlert"] { background: #1c1c21 !important; border: 1px solid #2a2a2e !important; border-radius: 8px !important; }
.caption { font-size: 0.78rem; color: #555; font-family: 'DM Mono', monospace; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ◈ DocumentExtractor")
    st.markdown('<p class="caption">v1.0 · AI Document Intelligence</p>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key:
        api_key = st.text_input("Gemini API Key", type="password", placeholder="AIza...")
        st.markdown('<p class="caption">Get a free key at aistudio.google.com</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="caption">API key loaded ✓</p>', unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<p class="caption">Supported formats</p>', unsafe_allow_html=True)
    for fmt in ["PDF", "DOCX", "XLSX", "PPTX", "TXT", "CSV", "HTML"]:
        st.markdown(f'<span class="tag">{fmt}</span>', unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<p class="caption">Built with Streamlit · MarkItDown · Gemini</p>', unsafe_allow_html=True)

# ── Main ──────────────────────────────────────────────────────────────────────
if not api_key:
    st.markdown("## ◈ DocumentExtractor")
    st.markdown("##### Extract structure and meaning from any document using AI.")
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.info("Enter your Gemini API key in the sidebar to get started.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

def ask_gemini(prompt):
    response = model.generate_content(prompt)
    return response.text

st.markdown("## ◈ DocumentExtractor")
st.markdown("##### Upload documents. Extract structure. Ask questions.")
st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── Upload ────────────────────────────────────────────────────────────────────
uploaded_files = st.file_uploader(
    "Drop your files here",
    accept_multiple_files=True,
    type=["pdf", "docx", "xlsx", "pptx", "txt", "csv", "html"]
)

if not uploaded_files:
    st.markdown('<p class="caption">No files uploaded yet. Max 200MB total.</p>', unsafe_allow_html=True)
    st.stop()

# ── Process ───────────────────────────────────────────────────────────────────
if "master_text" not in st.session_state or st.session_state.get("file_count") != len(uploaded_files):
    md_converter = MarkItDown()
    master_text = ""
    failed = []

    with st.spinner("Converting documents..."):
        progress = st.progress(0)
        for i, uploaded_file in enumerate(uploaded_files):
            suffix = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            try:
                result = md_converter.convert(tmp_path)
                master_text += f"\n\n## {uploaded_file.name}\n{result.text_content}"
            except Exception as e:
                failed.append(uploaded_file.name)
            finally:
                os.unlink(tmp_path)
            progress.progress((i + 1) / len(uploaded_files))

    st.session_state.master_text = master_text
    st.session_state.file_count = len(uploaded_files)
    if failed:
        st.warning(f"Could not convert: {', '.join(failed)}")

master_text = st.session_state.master_text

# ── Stats ─────────────────────────────────────────────────────────────────────
word_count = len(master_text.split())
char_count = len(master_text)
file_count = len(uploaded_files)

st.markdown(f"""
<div class="metric-row">
    <div class="metric-box">
        <div class="value">{file_count}</div>
        <div class="label">Files Processed</div>
    </div>
    <div class="metric-box">
        <div class="value">{word_count:,}</div>
        <div class="label">Words Extracted</div>
    </div>
    <div class="metric-box">
        <div class="value">{char_count:,}</div>
        <div class="label">Characters</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.success(f"✓ {file_count} file(s) converted to Markdown successfully.")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["  🧠 AI Summary  ", "  💬 Ask a Question  ", "  📄 Raw Markdown  "])

with tab1:
    st.markdown("#### Structured Extraction")
    st.markdown('<p class="caption">Extracts key topics, dates, names, and numbers from your documents.</p>', unsafe_allow_html=True)
    if st.button("Generate Summary"):
        with st.spinner("Analyzing..."):
            prompt = f"""Analyze these documents and return a clean structured summary with these sections:

**Key Topics** — main subjects covered
**Important Dates & Deadlines** — any dates mentioned
**Names, Companies & Projects** — entities found
**Numbers & Figures** — budgets, quantities, percentages
**Key Takeaways** — 3 bullet points max

Documents:
{master_text[:8000]}"""
            result = ask_gemini(prompt)
            st.markdown(result)

with tab2:
    st.markdown("#### Document Q&A")
    st.markdown('<p class="caption">Ask anything. The AI answers using only your uploaded documents.</p>', unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_question = st.chat_input("Ask a question about your documents...")
    if user_question:
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                qa_prompt = f"""Answer this question using ONLY the document content below.
If the answer is not found in the documents, say exactly: "This information is not in the uploaded documents."
Be concise and precise.

Question: {user_question}

Documents:
{master_text[:8000]}"""
                answer = ask_gemini(qa_prompt)
                st.markdown(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})

with tab3:
    st.markdown("#### Extracted Markdown")
    st.download_button(
        "⬇ Download .md file",
        master_text,
        file_name="extracted.md",
        mime="text/markdown"
    )
    with st.expander("Preview extracted content"):
        st.markdown(f"```\n{master_text[:3000]}{'...' if len(master_text) > 3000 else ''}\n```")