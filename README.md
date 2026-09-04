## What this does not prove

This project analyses the last 10 years of OHLCV bars of SPY only.
Results have not been tested on any other ETF or stock, and should not
be assumed to generalise beyond SPY over this specific historical
window.

Because this project holds a single, fixed ticker rather than selecting
among a universe of stocks, survivorship bias, which arises from
testing only on companies that remained in an index long enough to
still be listed today, has no mechanism to enter here. This isn't a
limitation we avoided by design; the bias simply doesn't apply to a
single-ticker backtest.

This does not currently account for transaction costs. Because costs
are charged per trade, a higher-frequency version of this strategy
would appear more favourable here than it would once realistic costs
were included. The reported numbers should be read as an upper bound
on performance, not a realistic estimate of tradeable returns.

We enforce a no-look-ahead policy when computing returns: a trading
signal computed from data available on day t is only ever evaluated
against the return realised from day t to day t+1, never against day
t's own return. This is standard practice, but it is easy to break
silently, since a single misplaced .shift() is enough. We state it
explicitly and test for it directly rather than relying on convention.

To avoid overconfidence in a single point-estimate Sharpe ratio, we
report a 90% bootstrap confidence interval alongside it, built by
resampling the observed daily returns with replacement 10,000 times and
taking the 5th and 95th percentiles of the resulting Sharpe values. If
this interval contains zero, we report that plainly. It means the
observed Sharpe is not statistically distinguishable from a strategy
with no real edge, and the result should be treated as inconclusive
rather than rounded up to "the strategy works."