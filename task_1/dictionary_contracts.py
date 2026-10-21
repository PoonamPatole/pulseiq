"""Build transparent type/nullability checks from the supplied data dictionary."""

from __future__ import annotations

import pandas as pd


TYPE_ALIASES = {
    "text": "string",
    "string": "string",
    "integer": "integer",
    "int": "integer",
    "decimal": "decimal",
    "number": "decimal",
    "float": "decimal",
    "double": "decimal",
    "date": "date",
    "datetime": "timestamp",
    "timestamp": "timestamp",
    "boolean": "boolean",
    "bool": "boolean",
}


def inferred_fact_contracts(dictionary_file: str) -> dict[str, list[dict]]:
    """Return column type/nullability promises for fact columns in the dictionary.

    This source does not supply enumeration or business-rule promises. Those
    remain blank here and are never inferred from observed distinct values.
    """
    dictionary = pd.read_csv(dictionary_file, keep_default_na=False)
    result: dict[str, list[dict]] = {}
    for _, row in dictionary.iterrows():
        table = str(row["sheet"])
        if not table.startswith("fact_"):
            continue
        raw_type = str(row["data_type"]).strip().lower()
        normalized = TYPE_ALIASES.get(raw_type, raw_type)
        if normalized not in {"string", "integer", "decimal", "date", "timestamp", "boolean"}:
            raise ValueError(f"Unsupported dictionary type {raw_type!r} for {table}.{row['column']}")
        try:
            nullable = int(row["null_count"]) > 0
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid null_count for {table}.{row['column']}") from exc
        result.setdefault(table, []).append({
            "column_name": str(row["column"]),
            "data_type": normalized,
            "nullable": "yes" if nullable else "no",
            "rule_or_allowed_values": "",
            "contract_source": "data_dictionary_type_nullability",
        })
    return result
