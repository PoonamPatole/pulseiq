# PQ-03 planted-issue comparison

Compared the 11 rows in `data/04_Validation_Vault/unlock_PQ-03_dq_known_issues.csv` with `audit.dq_results` after running all 14 checks. **All 11 planted issue categories were detected; zero were missed.** The matching checks are shown below.

| Key issue | Planted issue | Check result | Outcome and notes |
|---|---|---|---|
| DQ-01 | Four attendance rows after employee exit (`FA-X0001`–`FA-X0004`) | DQ-C05: 4 WARN | Caught all four. DQ-C06 also flags FA-X0004 for unpaid absence not reflected in payroll; that is an overlapping symptom. |
| DQ-02 | Duplicate payroll rows (`PI-X0001`, `PI-X0002`) | DQ-C03: 2 FAIL groups | Caught both duplicate employee/run groups. The result groups by employee and run, so the report shows those keys rather than the two planted item IDs. |
| DQ-03 | Payroll employees missing from `dim_employee` (`PI-X0003`, `PI-X0004`) | DQ-C04: 2 FAIL | Caught both orphan payroll rows. |
| DQ-04 | June 2026 payroll-to-ledger mismatch of INR 18,450 | DQ-C01: 5 FAIL months | Caught June 2026; its reported payroll-minus-ledger difference is approximately -INR 18,450. The same check also flags four other months, which require investigation rather than being attributed to this planted issue. |
| DQ-05 | Overpaid invoice `INV-00385` | DQ-C07: 1 WARN | Caught the INR 100 overpayment and negative balance. |
| DQ-06 | Twelve tasks completed before starting | DQ-C09: included in 20 WARN | Caught all 12 task IDs. |
| DQ-07 | Eight Done tasks missing completion dates | DQ-C09: included in 20 WARN | Caught all 8 task IDs. |
| DQ-08 | Two leave requests ending before they start | DQ-C10: 2 WARN | Caught both leave rows. |
| DQ-09 | Five stale attrition-risk predictions | DQ-C11: included in 410 WARN | Caught all five IDs. The combined freshness check also flags many historical anomaly-feed records; see limitations below. |
| DQ-10 | Expense total mismatch `EXP-00371` | DQ-C08: 1 WARN | Caught the INR 500 arithmetic difference. |
| DQ-11 | Overlapping SCD employee versions for key 100000 | DQ-C12: 1 FAIL | Caught the overlap for employee EMP-0001, including earlier key 100000. |

## Findings beyond the planted issues

- DQ-C01 reports five months with payroll/ledger differences. The answer key identifies the June 2026 INR 18,450 mismatch; the other four reported month differences are not explained by that planted issue and should be reconciled before payroll metrics are treated as final.
- DQ-C11 reports 410 stale records because it checks both attrition-risk `as_of_date` and anomaly-feed `scored_at`. It catches the five planted old risk predictions, but also flags the static historical anomaly sample as stale relative to the latest load. That makes the warning noisy for this supplied snapshot; a production freshness rule should distinguish a static historical sample from a newly arriving feed.
- DQ-C14 separately fails because the raw metric dictionary has no minimum group size for M19, M24, and M26. These are metadata gaps, not among the 11 planted data issues. Task 4 applies explicit effective thresholds in `metrics.metric_catalog`, while leaving the raw dictionary intact.
- DQ-C06 independently flags one unpaid-absence/payroll mapping discrepancy on FA-X0004. It overlaps the attendance-after-exit planted issue but does not replace the intended DQ-C05 check.

## Result

**Planted issues detected: 11/11. Missed: 0.** Detection is not the same as repair: the failing source rows remain in the raw/warehouse data, and the additional reconciliation and freshness findings still need owner review. The check self-test also passed all 14 injected-defect cases (those tests used scratch copies).
