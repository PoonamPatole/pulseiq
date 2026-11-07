# Task 14 AI signals and forecast notes

## Anomalies

The source contains 405 flagged anomaly rows across distinct source records. The payroll rows carry a model-estimated total money at risk of INR 31,421,239.07 across 184 quantified records. The largest grouped exposure is **Unusual pay ratios** (145 records; INR 19,432,986.26), followed by **Gross pay unusually high** (13; INR 9,417,924.27). Attendance anomaly types have blank money estimates by contract; they are not treated as zero exposure. The estimates indicate potential exposure for human review, not confirmed loss.

## Forecast errors

`forecast_error.csv` contains the 12 company-level forecasts: six headcount and six monthly attrition forecasts from October 2026 through March 2027. Actual headcount and attrition data end in September 2026, so none of those forecast months has an actual value yet. Absolute error and percentage error are therefore N/A for all current rows; MAPE is not calculated. When actuals arrive, absolute percentage error is `abs(forecast - actual) / abs(actual) * 100`.

## Interpreting a 12% error

A 12% error cannot be called good or bad by itself. Finance and HR would need to know the metric and forecast horizon, an agreed baseline and tolerance, the cost of over- versus under-forecasting, how often the error falls outside the 80% band, and whether errors are persistent or one-off.
