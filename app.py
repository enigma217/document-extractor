import streamlit as st
import tempfile
import os
import json
import fitz  # pymupdf
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
.tag { display: inline-block; background: #1e2a14; color: #c8f565; border: 1px solid #3a5020; border-radius: 4px; padding: 2px 10px; font-size: 0.75rem; font-family: 'DM Mono', monospace; margin-right: 6px; margin-bottom: 4px; }
.divider { border: none; border-top: 1px solid #2a2a2e; margin: 1.5rem 0; }
[data-testid="stTextInput"] input { background: #1c1c21 !important; border: 1px solid #2a2a2e !important; color: #e8e8e8 !important; border-radius: 6px !important; }
.stButton > button { background: #c8f565 !important; color: #0e0e11 !important; border: none !important; border-radius: 6px !important; font-family: 'DM Sans', sans-serif !important; font-weight: 600 !important; padding: 0.4rem 1.2rem !important; }
.stButton > button:hover { background: #d4f77a !important; }
[data-testid="stFileUploader"] { background: #16161a !important; border: 1px dashed #2a2a2e !important; border-radius: 8px !important; }
code { font-family: 'DM Mono', monospace !important; background: #1c1c21 !important; color: #c8f565 !important; }
[data-testid="stExpander"] { background: #16161a !important; border: 1px solid #2a2a2e !important; border-radius: 8px !important; }
[data-testid="stAlert"] { background: #1c1c21 !important; border: 1px solid #2a2a2e !important; border-radius: 8px !important; }
.caption { font-size: 0.78rem; color: #555; font-family: 'DM Mono', monospace; }
.json-preview { background: #1c1c21; border: 1px solid #2a2a2e; border-radius: 8px; padding: 1rem; font-family: 'DM Mono', monospace; font-size: 0.78rem; color: #c8f565; white-space: pre-wrap; max-height: 400px; overflow-y: auto; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ◈ DocumentExtractor")
    st.markdown('<p class="caption">v2.0 · AI Document Intelligence</p>', unsafe_allow_html=True)
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
    st.markdown('<p class="caption">Output</p>', unsafe_allow_html=True)
    for fmt in ["Markdown .md", "Structured .json"]:
        st.markdown(f'<span class="tag">{fmt}</span>', unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<p class="caption">Built with Streamlit · MarkItDown · Gemini</p>', unsafe_allow_html=True)

# ── Main ──────────────────────────────────────────────────────────────────────
if not api_key:
    st.markdown("## ◈ DocumentExtractor")
    st.markdown("##### Upload documents. Get structured Markdown and JSON.")
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.info("Enter your Gemini API key in the sidebar to get started.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

st.markdown("## ◈ DocumentExtractor")
st.markdown("##### Upload documents. Get structured Markdown and JSON instantly.")
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

# ── Process files ─────────────────────────────────────────────────────────────
if "master_text" not in st.session_state or st.session_state.get("file_count") != len(uploaded_files):
    md_converter = MarkItDown()
    master_text = ""
    failed = []

    with st.spinner("Converting documents..."):
        progress = st.progress(0)
        for i, uploaded_file in enumerate(uploaded_files):
            suffix = os.path.splitext(uploaded_file.name)[1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            try:
                if suffix == ".pdf":
                    doc = fitz.open(tmp_path)
                    pdf_text = ""
                    for page in doc:
                        pdf_text += page.get_text()
                    doc.close()
                    master_text += f"\n\n## {uploaded_file.name}\n{pdf_text}"
                else:
                    result = md_converter.convert(tmp_path)
                    master_text += f"\n\n## {uploaded_file.name}\n{result.text_content}"
            except Exception as e:
                failed.append(f"{uploaded_file.name} ({e})")
            finally:
                os.unlink(tmp_path)
            progress.progress((i + 1) / len(uploaded_files))

    st.session_state.master_text = master_text
    st.session_state.file_count = len(uploaded_files)
    st.session_state.json_data = None
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

st.success(f"✓ {file_count} file(s) converted successfully.")
st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── MD Download always available ──────────────────────────────────────────────
st.markdown("### Downloads")
st.download_button(
    label="⬇ Download Markdown (.md)",
    data=master_text,
    file_name="extracted.md",
    mime="text/markdown",
    use_container_width=False
)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── Extract JSON ──────────────────────────────────────────────────────────────
st.markdown("### Extract Structured JSON")
st.markdown('<p class="caption">Runs one AI call to extract entities, dates, topics, and figures.</p>', unsafe_allow_html=True)

if st.button("⚡ Extract JSON"):
    with st.spinner("Extracting structured data..."):
        prompt = f"""You are a document intelligence engine. Extract structured data from the documents below.

Return ONLY valid JSON with no explanation, no markdown, no code fences. Just raw JSON.

Use this exact structure:
{{
  "document_count": <number of source files>,
  "key_topics": ["topic1", "topic2"],
  "entities": {{
    "people": ["name1", "name2"],
    "organizations": ["org1", "org2"],
    "locations": ["loc1", "loc2"],
    "projects": ["project1", "project2"]
  }},
  "dates_and_deadlines": ["date1", "date2"],
  "financial_figures": ["figure1", "figure2"],
  "key_numbers": ["stat1", "stat2"],
  "summary": "2-3 sentence summary of all documents combined"
}}

If a field has no data, use an empty array [].

Documents:
{master_text[:8000]}"""

        try:
            response = model.generate_content(prompt)
            raw = response.text.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(raw)
            st.session_state.json_data = parsed
        except json.JSONDecodeError:
            st.session_state.json_data = {"raw_output": raw}
        except Exception as e:
            st.error(f"Extraction failed: {e}")

# ── JSON results ──────────────────────────────────────────────────────────────
if st.session_state.get("json_data"):
    json_str = json.dumps(st.session_state.json_data, indent=2)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.download_button(
        label="⬇ Download JSON (.json)",
        data=json_str,
        file_name="extracted.json",
        mime="application/json",
        use_container_width=False
    )

    st.markdown("**JSON Preview**")
    st.markdown(f'<div class="json-preview">{json_str}</div>', unsafe_allow_html=True)