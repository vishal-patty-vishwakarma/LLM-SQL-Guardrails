import streamlit as st

from pipeline.orchestrator import run_pipeline
from llm.schema_context import get_schema_context

st.set_page_config(page_title="Text-to-SQL Guardrails", layout="wide")

st.title("Text-to-SQL with Guardrails")
st.markdown("Ask questions in plain English. Get safe SQL and results.")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Database Schema")
    schema = get_schema_context(sample_rows=1)
    st.code(schema, language="sql")

    st.header("About")
    st.markdown(
        "- **LLM**: phi (Ollama) - swap model in config/settings.py\n"
        "- **Guardrails**: sqlglot AST validation\n"
        "- **Database**: SQLite (e-commerce)"
    )

    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sql" in message:
            with st.expander("Generated SQL"):
                st.code(message["sql"], language="sql")
        if "validation" in message:
            v = message["validation"]
            if v.errors:
                st.error("; ".join(str(e) for e in v.errors))
            if v.warnings:
                st.warning("\n".join(v.warnings))
            if v.valid and not v.errors:
                st.success("Guardrails passed")
        if "results" in message:
            st.dataframe(message["results"], use_container_width=True)

if prompt := st.chat_input("Ask a question about the data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        status_placeholder.info("⏳ Generating SQL (15-30s on CPU)...")
        result = run_pipeline(prompt)

        if result.error:
            status_placeholder.error("❌ " + result.error)
        else:
            status_placeholder.success("✅ Done")

        if result.sql:
            with st.expander("Generated SQL", expanded=True):
                st.code(result.sql, language="sql")

        if result.validation.errors:
            st.error("; ".join(str(e) for e in result.validation.errors))
        elif result.validation.warnings:
            for w in result.validation.warnings:
                st.warning(w)
        else:
            st.success("Guardrails passed")

        if result.results is not None:
            st.dataframe(result.results, use_container_width=True)
            st.caption(f"Rows: {len(result.results)} | Columns: {len(result.results.columns)}")
        elif result.error:
            st.error(result.error)

    st.session_state.messages.append({
        "role": "assistant",
        "content": result.markdown or result.error or "No results.",
        "sql": result.sql,
        "validation": result.validation,
        "results": result.results,
    })