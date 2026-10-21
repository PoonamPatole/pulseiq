"""Compare each source CSV's data-row count with its raw DuckDB table."""

import csv
import re
from pathlib import Path

import duckdb


PROJECT_DIR = Path(__file__).resolve().parent.parent
CSV_DIR = PROJECT_DIR / "data" / "03_Data" / "csv"
DB_FILE = PROJECT_DIR / "pulseiq.duckdb"


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        next(reader, None)  # Exclude the header row.
        return sum(1 for _ in reader)


def main() -> None:
    if not DB_FILE.exists():
        raise FileNotFoundError(f"Database not found: {DB_FILE}. Run python etl.py first.")

    results = []
    with duckdb.connect(str(DB_FILE), read_only=True) as con:
        for csv_path in sorted(CSV_DIR.glob("*.csv")):
            table = csv_path.stem
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
                raise ValueError(f"Unexpected CSV filename for a table: {csv_path.name}")
            csv_rows = count_csv_rows(csv_path)
            try:
                db_rows = con.execute(f"SELECT COUNT(*) FROM raw.{table}").fetchone()[0]
            except duckdb.CatalogException:
                db_rows = None
            results.append((table, csv_rows, db_rows, csv_rows == db_rows))

    print(f"{'TABLE':32} {'CSV ROWS':>10} {'DB ROWS':>10} {'MATCH':>8}")
    print("-" * 64)
    for table, csv_rows, db_rows, matches in results:
        db_value = "MISSING" if db_rows is None else str(db_rows)
        print(f"{table:32} {csv_rows:>10} {db_value:>10} {str(matches):>8}")

    mismatches = [row for row in results if not row[3]]
    print(f"\nChecked {len(results)} CSV files; mismatches: {len(mismatches)}")
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
