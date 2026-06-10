from sqlalchemy import inspect, text

from database.connection import engine
from config.settings import settings


def get_schema_context(sample_rows: int | None = None) -> str:
    sample_rows = sample_rows or settings.schema_sample_rows
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    parts = []

    for table in tables:
        columns = inspector.get_columns(table)
        pk = inspector.get_pk_constraint(table)
        fks = inspector.get_foreign_keys(table)

        cols_str = ", ".join(
            f"{c['name']} {c['type']!s}{' PK' if pk and c['name'] in pk.get('constrained_columns', []) else ''}"
            for c in columns
        )
        parts.append(f"TABLE {table} ({cols_str})")

        if fks:
            for fk in fks:
                parts.append(f"  FK: {fk['constrained_columns']} -> {fk['referred_table']}({fk['referred_columns']})")

        if sample_rows > 0:
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM {table} LIMIT {sample_rows}"))
                rows = result.fetchall()
                cols = result.keys()
            if rows:
                sample_str = "\n".join(str(dict(zip(cols, row))) for row in rows)
                parts.append(f"  Samples:\n{sample_str}")

    return "\n".join(parts)


def get_table_names() -> list[str]:
    inspector = inspect(engine)
    return inspector.get_table_names()


def get_columns_for_table(table: str) -> list[dict]:
    inspector = inspect(engine)
    return inspector.get_columns(table)