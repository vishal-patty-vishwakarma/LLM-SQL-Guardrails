# Text-to-SQL with Guardrails

Natural language → LLM generates SQL → Guardrails validate → Execute safely → Results

## Architecture

```
User Question
     │
     ▼
┌──────────────────────┐     ┌──────────────────┐
│  Schema Context      │     │  Prompt Builder   │
│  (DDL + samples + FK)│────▶│  (system + 8      │
│                      │     │   few-shots)      │
└──────────────────────┘     └────────┬─────────┘
                                      │
                                      ▼
                              ┌──────────────────┐
                              │  Ollama Client    │
                              │  (phi)    │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │  SQL Validator    │
                              │  (8 rules via     │
                              │   sqlglot AST)    │
                              └────────┬─────────┘
                                       │
                            ┌──────────┴──────────┐
                            ▼                     ▼
                      ┌──────────┐       ┌──────────────┐
                      │  Blocked │       │  Safe Executor│
                      │  + error │       │  (read-only,  │
                      │  message │       │  row limit)   │
                      └──────────┘       └──────┬───────┘
                                                ▼
                                       ┌──────────────┐
                                       │  Formatter    │
                                       │  (DataFrame → │
                                       │   markdown)   │
                                       └──────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| LLM | Ollama + phi (default, 2.5GB) |
| SQL Validation | sqlglot (AST parsing) |
| Backend | FastAPI-style pipeline |
| Database | SQLite + SQLAlchemy |
| Frontend | Streamlit |
| Config | Pydantic Settings |

## Features

- **Natural language to SQL** via locally-hosted LLM
- **8 guardrails rules** blocking DDL, DML, transactions, comments, dangerous functions
- **AST-based parsing** with sqlglot (not regex)
- **Read-only execution** with `PRAGMA query_only = ON`
- **Streamlit chat UI** with schema viewer and guardrails panel
- **8 few-shot examples** covering simple filters to complex CTEs

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Pull the LLM model (2.5GB for phi, or 4GB for sqlcoder:7b)
python scripts/pull_model.py

# 3. Create and seed the database (858 rows, 5 tables)
python -c "from database.connection import init_db; init_db()"

# 4. Launch the app
python -m streamlit run frontend/app.py
```

## Project Structure

```
text-to-sql-guardrails/
├── config/              # Settings, schema DDL
├── database/            # SQLAlchemy connection, seed data
├── llm/                 # Ollama client, prompts, schema context
├── guardrails/          # SQL validation, AST parsing, rules
├── pipeline/            # Orchestrator, executor, formatter
├── frontend/            # Streamlit chat interface
├── tests/               # Unit + integration tests
└── notebooks/           # Prompt engineering, evaluations
```

## Model Options

Default is `phi` (3.8B, ~2.5GB). Swap in `config/settings.py` or `.env`:

| Model | Size | Download | Speed on CPU | SQL Quality |
|-------|------|----------|--------------|-------------|
| `phi` | 3.8B | 2.5 GB | Fast | Good |
| `sqlcoder:7b` | 7B | 4 GB | Slow | Best |
| `codellama:7b` | 7B | 4 GB | Slow | Good |
| `tinyllama` | 1.1B | 0.6 GB | Very fast | Ok |

## Guardrails Rules

| Rule | Check | Action |
|------|-------|--------|
| G001 | Block DDL/DML (DROP, INSERT, etc.) | Block |
| G003 | Block transaction control | Block |
| G005 | Block SQL comments | Block |
| G006 | Require single statement | Block |
| G008 | Block dangerous functions | Block |
| G007 | Require LIMIT clause | Warn |
| G009 | Check nesting depth | Warn |
| G010 | Check table join count | Warn |

## Example Questions

- "Show all products in the Electronics category"
- "What's the total revenue by country?"
- "Top 5 customers by lifetime value"
- "Monthly order count for 2024"
- "Which categories have no products in stock?"
