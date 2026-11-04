All variables used in this document are sourced from Finaeon, except for
WTI Spot crude oil prices, which are obtained from FRED, and the
Fama–French factors, which are sourced from Kenneth French’s data
library.

## Stock Returns (Returns)

Stock returns are computed from equity price indices. For each period,
returns are calculated as $\frac{P_{t} - P_{t - 1}}{P_{t - 1}}$ where
($P_{t}$) denotes the current price level and ($P_{t - 1}$) the price
level in the previous period. The first observation for each country is
removed, as a lagged price is not available to compute a return. Returns
are kept in raw form and are not expressed in percentages. Throughout
the analysis, returns therefore represent relative price changes without
additional transformation.

## 3-Month Treasury Bills (TBills)

The Treasury bill rate corresponds to 3-month government securities,
expressed in annualized percentage points. The original data are
available at lower or mixed frequencies but are extracted at the monthly
frequency. When necessary, observed values are forward-filled until the
next publication date in order to construct a continuous monthly series,
without altering the level of the interest rate.

## Dividend Yield (DY)

Dividend yield is expressed in annual percentage terms. The original
data are available at a quarterly frequency. To ensure consistency with
the monthly panel, the most recently published dividend yield is forward
filled to the subsequent months until a new observation becomes
available. This treatment preserves the economic information content of
the data while avoiding artificial intra-quarter variation.

## Long-Term Government Bond Yield (GovBond)

Government bond yields correspond to 10-year sovereign bonds, expressed
in annual percentage points. These yields capture long-term sovereign
financing conditions and are used in levels. The series is harmonized to
monthly frequency without further transformation.

## Long-Term Corporate Bond Yield (CorpBond)

Corporate bond yields represent long-term corporate debt instruments and
are expressed in annual percentage points. This variable captures
private-sector financing conditions and credit risk. The data are used
in levels and aligned to monthly frequency.

## Exchange Rate (FX)

The exchange rate is measured as units of domestic currency per U.S.
dollar. This variable is a price level, not a return. No transformation
into growth rates or percentage changes is applied. The series is
directly incorporated into the monthly panel.

## Unemployment Rate (Unemployment)

The unemployment rate is expressed as a percentage of the labor force.
For certain periods, the original data are available only at an annual
frequency. In order to construct a monthly panel, observed annual values
are forward filled across the corresponding months until the next
release. This procedure ensures temporal consistency while preserving
the level of the variable.

## Price-to-Earnings Ratio (P/E)

The price-to-earnings (P/E) ratio is a unit-free valuation measure
reflecting equity market pricing relative to earnings. The variable is
used in levels and incorporated directly into the monthly panel without
further transformation.

## Gross Domestic Product (GDP)

Gross Domestic Product corresponds to nominal GDP, expressed in current
national currency units. The CPI is expressed in millions. Depending on
the period, the original data are available at annual or quarterly
frequency. To ensure consistency with the monthly panel, GDP
observations are converted to monthly frequency by forward filling the
most recent published value until a new observation becomes available.
No deflation is applied, and GDP is used as an indicator of aggregate
economic activity in nominal terms.

## Inflation

Inflation is constructed from the Consumer Price Index (CPI). The
inflation rate is calculated as
$\frac{{CPI}_{t} - {CPI}_{t - 1}}{{CPI}_{t - 1}}$. ${CPI}_{t}$ refers to
the level of the Consumer Price Index in period $t$, while
$CPI_{t - 1}$denotes the CPI in the previous period. Inflation is
measured as the relative change in the CPI between two consecutive
periods

Since CPI data is not uniformly reported at the same frequency across
countries, the computed inflation rate is annualized to ensure
comparability. The annualization factor is determined based on the time
gap between consecutive CPI observations. When the gap is approximately
twelve months, no adjustment is applied. If the data is available at a
semiannual frequency, the inflation rate is multiplied by two, while
quarterly observations are multiplied by four.

Finally, the annualized inflation series is forward-filled across the
corresponding months to obtain a balanced monthly frequency consistent
with the other macroeconomic variables included in the panel dataset.

## Spot crude Oil Price (WTI)

The crude oil price corresponds to the spot price of West Texas
Intermediate (WTI), expressed in U.S. dollars per barrel. The series is
not seasonally adjusted. The data are available at a monthly frequency
and are used in levels rather than returns. WTI is treated as a global
variable, identical across all countries in the panel, and is merged by
date to capture common energy price shocks affecting all economies.

## Fama–French Factors

The Mkt–RF, SMB, and HML factors are included as global variables,
identical for all countries. They are expressed in returns and capture,
respectively, the market, size, and value risk factors. The risk-free
rate (RF) is not treated as a risk factor and is therefore excluded from
the factor set used in the analysis.
