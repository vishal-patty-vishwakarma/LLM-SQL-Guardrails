# Architecture

## Data Flow

```
┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
│ User   │──▶│ LLM    │──▶│ Guard- │──▶│ Safe   │──▶│ Form-  │
│        │   │ Client │   │ rails  │   │ Exec-  │   │ atter  │
│Question│   │(Ollama)│   │(sqlglot│   │ utor   │   │(pandas)│
└────────┘   └────────┘   │  AST)  │   │(read-  │   └────────┘
                          └────────┘   │ only)  │
                                       └────────┘
```

## Layer Responsibilities

### Config Layer (`config/`)
- Central configuration via Pydantic Settings
- Schema DDL used for both DB creation and LLM context

### Database Layer (`database/`)
- SQLAlchemy engine with SQLite
- WAL mode for concurrent access
- `PRAGMA foreign_keys = ON` enforced per-connection
- Seed data: 5 tables, 858 rows

### LLM Layer (`llm/`)
- Ollama wrapper with streaming support
- Schema context builder (DDL + FKs + sample rows)
- 8 few-shot examples covering all SQL patterns

### Guardrails Layer (`guardrails/`)
- sqlglot AST parsing (not regex)
- 8 composable rules with block/warn actions
- Typed exceptions (SecurityError, ComplexityError)

### Pipeline Layer (`pipeline/`)
- Orchestrator ties all layers together
- Safe executor enforces read-only at database level
- Formatter converts DataFrames to markdown/dict

### Frontend Layer (`frontend/`)
- Streamlit chat interface
- Schema viewer, SQL display, results table
- Guardrails panel showing validation results

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| sqlglot over regex | AST parsing catches structurally dangerous queries regex would miss |
| PRAGMA query_only | Defense in depth - blocks writes at database level |
| Separate guardrails layer | Can be tested independently, swapped, or extended |
| Local LLM (Ollama) | No API costs, privacy, works offline |
| SQLite | Zero setup, portable, good enough for learning portfolio |