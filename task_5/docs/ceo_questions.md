# Five CEO questions for the workforce page

1. How many people are in the workforce at the end of the selected month?
2. Is headcount growing or shrinking, and by how much over the selected period?
3. Which departments have the largest reportable headcount?
4. How is visible headcount distributed across city tiers?
5. Which work modes are most common?

The dashboard answers these with KPI cards, a monthly trend, and department, city-tier, and work-mode comparisons. Every plotted number is read from an aggregate view in DuckDB's `metrics` schema.

The KPI row also includes M29, month-over-month headcount growth, which is checked in `mini_challenge.md`.

## Colour key

- Navy (`#1F4E79`): workforce size and headcount trend.
- Teal (`#2A9D8F`): workforce composition breakdowns.

These two colours have consistent meanings throughout the page.
