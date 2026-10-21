"""Load every dataset CSV into the project's root-level pulseiq.duckdb."""

from pathlib import Path
import re

import duckdb


PROJECT_DIR = Path(__file__).resolve().parents[2]
CSV_DIR = PROJECT_DIR / "data" / "03_Data" / "csv"
DB_FILE = PROJECT_DIR / "pulseiq.duckdb"

with duckdb.connect(str(DB_FILE)) as con:
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    for csv_file in sorted(CSV_DIR.glob("*.csv")):
        table = csv_file.stem
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
            raise ValueError(f"Unexpected CSV filename: {csv_file.name}")
        con.execute(
            f'CREATE OR REPLACE TABLE raw."{table}" AS SELECT * FROM read_csv_auto(?, header=true)',
            [str(csv_file)],
        )
        count = con.execute(f'SELECT COUNT(*) FROM raw."{table}"').fetchone()[0]
        print(f"raw.{table:<32}{count:>8} rows")

print(f"Database created/updated: {DB_FILE}")
