# Task 11 findings and tie-out notes

## Reconciliation

The supplied workbook README headline section lists dataset counts rather than monthly P&L totals. Its ledger and expense row counts are 6,784 and 501; the loaded warehouse has the same counts. The account dimension has 5 group rows and 42 detail rows. Task 11 filters to active detail accounts, so group headings are not added to their children.

`tieout.csv` compares all 18 months (Apr 2025–Sep 2026) with governed views M16–M18. Revenue matches M16, net profit matches M17, and operating margin matches M18 in every month to the cent (margin differences are floating-point precision only). Revenue uses accounts 4001–4004; other income account 4900 is displayed separately and included in net profit. This is a tie-out to governed metrics, not to a separate PQ-11 answer key; none is supplied in the validation vault.

## Three findings

1. **The April 2026 margin drop came as expenses grew faster than revenue.** From March to April 2026, revenue rose 11.4% (INR 74.88m to INR 83.45m), while expenses rose 20.7% (INR 59.64m to INR 72.00m). Net profit fell from INR 15.48m to INR 11.45m and margin from 20.67% to 13.72%.
2. **Incentives and salaries drove the ledger expense increase.** Salaries and wages rose from INR 43.43m to INR 47.06m; incentives and bonus rose from INR 4.79m to INR 14.26m. Together those two accounts explain about INR 13.20m of the INR 12.36m net expense increase; other accounts offset part of the increase.
3. **Vendor-bill spend is concentrated in property, cloud, and marketing, while the largest vendor is a property vendor.** Across the 18-month expense feed, Office Rent totals INR 38.15m, Cloud Hosting INR 27.93m, and Marketing & Advertising INR 21.42m. Skyline Realty Holdings is the top vendor at INR 16.88m, followed by StratoHost Infrastructure at INR 14.20m and NimbusCloud Services at INR 13.73m. These are bill amounts excluding GST, not total ledger expenses.

## Three plausible causes when revenue grows but margin falls

1. **Variable compensation or headcount cost rises faster than sales.** The March–April ledger shows the incentive and salary increases above. Prove the cause with payroll employee counts, bonus eligibility/payouts, hiring dates, and payroll-to-ledger reconciliation for those months.
2. **Revenue mix shifts toward lower-margin services.** In March–April, software services plus SaaS revenue fell from INR 64.71m to INR 59.36m, while consulting plus support revenue rose from INR 10.17m to INR 24.08m. Prove or reject this with service-line delivery costs, utilization, project hours, and gross margin by contract or product line.
3. **One-off or timing-sensitive operating costs increase.** April includes INR 2.12m of insurance expense and higher marketing spend; expense postings can also include accruals, reversals, or timing shifts (professional fees were a net credit in April). Prove the cause with bill references, payment/accrual schedules, renewal terms, and matched journal entries across adjacent months.

These explanations are hypotheses to investigate. The dashboard identifies the movements but does not establish why they happened.
