# Backtest engine with honest statistics

A small Python backtester that tests one deliberately simple trading strategy on ten years of SPY data, then asks the question most backtests skip: **is the result real, or just noise?**

The strategy is not the point. The measurement is. The engine enforces a strict no-look-ahead rule in code, charges a transaction cost on every trade, and reports a bootstrap confidence interval around the Sharpe ratio instead of a single number.

**The short answer.** Before costs the strategy looks mildly positive (Sharpe 0.26). After a realistic cost of 5 bps per trade it loses money (Sharpe -0.30), and its 90% confidence interval of [-0.84, 0.22] contains zero. This backtest cannot tell it apart from a strategy with no edge at all, and simply holding SPY beat it comfortably over the same period.

**How to read this README.** Section 1 explains the ideas in plain English and needs no finance background. Section 2 presents the results and what they mean. Section 3 explains how the engine works and why it was built that way. Section 4 sets out what the results do not prove.

---

## 1. The ideas, from the ground up

### What a backtest is

A backtest replays history to answer one question: if I had followed this rule, what would have happened? You take a trading rule, walk through past prices one day at a time, let the rule decide what to hold each day, and record the profit or loss.

That sounds simple, and the simplicity is the danger. Three mistakes make most backtests look better than reality:

- **Look-ahead.** The rule accidentally uses information it could not have had at the time, such as tomorrow's price. A single day of misalignment can turn a useless rule into a spectacular one.
- **Ignoring costs.** Every trade costs money. A rule that trades often can look profitable on paper and lose money in practice.
- **Trusting a single number.** A good result over one stretch of history may simply be luck.

This project is built around guarding against all three.

### The strategy: mean reversion

Mean reversion is the idea that unusually large moves tend to partly reverse. If SPY has an unusually bad day, the strategy bets it will bounce back tomorrow. If it has an unusually good day, the strategy bets on a pullback.

To decide what counts as unusual, the strategy uses a **z-score**: how many standard deviations today's return sits away from the recent average.

```
z = (today's return - average of the last 20 daily returns)
    / standard deviation of the last 20 daily returns
```

**Example.** Over the last 20 days, SPY's daily returns have averaged about +0.05% with a standard deviation of about 1%. Today SPY falls 1.5%. Then z is roughly (-1.5 - 0.05) / 1 = -1.55. That is more than one standard deviation below normal, so the strategy goes long for tomorrow.

| z-score | What it means | Position held tomorrow |
|---|---|---|
| below -1 | unusually bad day | long (+1) |
| above +1 | unusually good day | short (-1) |
| between -1 and +1 | nothing unusual | flat (0), in cash |

A **position** is one number per day describing exposure to SPY. At +1 the strategy is fully invested, so if SPY rises 1% it makes 1%. At -1 it is short, so it makes 1% if SPY falls 1%. At 0 it holds cash and earns nothing either way.

The parameters (a 20-day window and a threshold of 1) were chosen once, before any results were seen, and never tuned. Adjusting them until the result looks good is the classic way to fool yourself with a backtest (see section 4).

### How performance is measured

Each statistic answers a different question.

| Statistic | The question it answers | How to read it |
|---|---|---|
| Annualised return | How much did it make per year, on average? | Higher is better. |
| Annualised volatility | How bumpy was the ride? | The spread of daily returns, scaled to a year. Lower is calmer. |
| Sharpe ratio | How much return did it earn per unit of risk? | Annualised return divided by annualised volatility. Below 0 means it lost money. Buy-and-hold SPY scored 0.79 here, a useful yardstick. |
| Max drawdown | What was the worst fall from a previous high? | -47% means that at its worst point the account was 47% below its previous peak. |
| Hit rate | On days it held a position, how often did it make money? | The share of in-market days with a positive return after costs. |
| Turnover | How much did it trade? | Total position change. Going from flat to long is 1 unit; flipping from long to short is 2 units. |

**Why annualise with 252 and the square root of 252.** There are about 252 trading days in a year. Average returns add up over time, so the yearly return is the daily average multiplied by 252. Volatility does not add up, but variance does (assuming each day is independent of the last), so yearly variance is 252 times daily variance, and yearly volatility, its square root, is the square root of 252 times daily volatility.

### Why costs matter

Every time the position changes, a real trader pays: commission, the gap between buying and selling prices (the bid-ask spread), and the price moving against them while the order fills (slippage). This project models all of that as a flat **5 basis points per unit of turnover**. One basis point is 0.01%, so 5 bps is 0.05%.

That sounds negligible, but a strategy that changes position every couple of days pays it hundreds of times. The cost sweep in section 2 shows exactly how much the conclusion depends on it.

### Why a confidence interval, not just a Sharpe ratio

A Sharpe ratio measured over ten years is an estimate, not a fact. Run the same strategy over a different ten years and you would get a different number. The real question is how much it could plausibly vary.

The **bootstrap** answers that without assuming anything about the shape of returns:

1. Take the strategy's 2,514 daily returns.
2. Draw 2,514 of them at random, *with replacement*, so some days appear twice and some not at all. This is a plausible alternative history.
3. Compute the Sharpe ratio of that alternative history.
4. Repeat 10,000 times.

The spread of those 10,000 Sharpe ratios shows how much the estimate wobbles. Cutting off the lowest 5% and highest 5% leaves the **90% confidence interval**.

**How to read it.** If the interval contains zero, the data cannot rule out that the true Sharpe is zero, meaning the strategy may have no edge and the result may be luck. That is an inconclusive result rather than a failure, and it is reported as it stands.

*Precisely:* if the whole procedure were repeated on many independent samples of history, about 90% of the intervals built this way would contain the true Sharpe ratio. It is a statement about the method, not a 90% probability attached to this one interval.

---

## 2. Results

**Data:** SPY daily bars, 2016-08-22 to 2026-08-21 (2,514 trading days), from Yahoo Finance via the `yfinance` Python library. Prices are adjusted for dividends, so buy-and-hold includes reinvested dividends. This is also why prices in the CSV sit below SPY's quoted historical prices.
**Cost:** 5 bps per unit of turnover.
**Benchmark:** buy-and-hold SPY, run through the same engine. It goes long on day two and stays long, paying for one unit of turnover.

| Statistic | Mean reversion | Buy and hold |
|---|---|---|
| Annualised return | -3.31% | 14.17% |
| Annualised volatility | 11.04% | 18.00% |
| Sharpe ratio | -0.30 | 0.79 |
| Max drawdown | -47.4% | -33.7% |
| Hit rate (days in the market) | 46.9% | 55.5% |
| Total turnover (units) | 1,223 | 1 |

**Bootstrap:** 90% confidence interval for the strategy's Sharpe ratio: **[-0.84, 0.22]** (10,000 resamples, seed 42). Zero is inside the interval.

**Cost sensitivity:**

| Cost (bps) | Sharpe (net of costs) |
|---|---|
| 0 | 0.26 |
| 1 | 0.14 |
| 2 | 0.03 |
| 5 | -0.30 |
| 10 | -0.85 |
| 20 | -1.94 |

### What the results say

**1. Costs decide the outcome.** Before costs, the strategy earns a small positive return: a Sharpe of 0.26, roughly +2.8% a year. But it trades a lot. A turnover of 1,223 units over ten years means a position change about every two days. At 5 bps that costs roughly 6.1% a year (about 122 units a year at 0.05% each), more than double what the strategy earns, which turns +2.8% into -3.3%. The Sharpe crosses zero at roughly 2.3 bps (interpolated between the 2 and 5 bps runs). Whatever edge the strategy has is too small to pay for the trading it takes to capture it.

**2. The result cannot be told apart from zero.** The interval [-0.84, 0.22] contains zero. A rule of thumb shows why this was always likely. With T years of data, the uncertainty (standard error) of an annualised Sharpe ratio is roughly the square root of 1/T. With ten years that is about 0.32, so a 90% interval stretches about 0.52 either side of the estimate. The interval here is 1.06 wide, which matches. In other words, with ten years of daily data a strategy needs a Sharpe of roughly 0.5 or more before it can be told apart from zero at all. By the same rule of thumb, even the cost-free Sharpe of 0.26 would very likely not clear that bar.

**3. Buy-and-hold won on every measure.** It had a higher return (14.2% against -3.3%), a higher Sharpe (0.79 against -0.30), a shallower worst drawdown (-33.7% against -47.4%) and a better hit rate. This was one particular decade in which SPY rose strongly, so it does not show that mean reversion can never work. It shows that this version, over this period, did worse than doing nothing clever.

**4. Lower volatility does not mean lower risk.** The strategy's volatility (11%) is well below buy-and-hold's (18%), yet its worst drawdown is deeper. Its volatility is low because it sits in cash on most days, earning exactly zero. Its drawdown is deep because the cost drag is a steady, compounding loss, roughly 6% a year every year, with no rebound to win it back. Volatility measures day-to-day bumpiness; drawdown measures how far you can fall over time. They are different kinds of risk.

**5. The measurement did its job.** Taken alone, the cost-free Sharpe of 0.26 invites a story about a modest, working edge. The cost model and the confidence interval together show that story is not supported by the data. Catching that, and reporting it plainly, is what this project was built to do.

---

## 3. How it works

### The pipeline

```
data/spy.csv
    |
    v   data.py        load_bars(): parse dates, coerce junk to NaN, drop bad rows
bars (one row per trading day)
    |
    v   engine.py      run_backtest(bars, strategy, cost_bps)
    |                  calls strategies.py: mean_reversion(history), once per day
BacktestResult         positions, returns, turnover, costs, net returns, equity curve
    |
    v   stats.py       Sharpe, volatility, drawdown, hit rate, bootstrap interval
run.py                 prints every number in this README
```

Each file has one job. The engine knows nothing about z-scores, and `stats.py` knows nothing about trading. Testing a different strategy means changing a single argument to `run_backtest`.

### Data loading

`load_bars` requires Open, High, Low, Close and Volume columns and raises an error if any are missing. Non-numeric values such as `"n/a"` are converted to missing values, and any row with a missing value is **dropped rather than forward-filled**. Forward-filling would invent a price that never traded, which on a volatile day could be badly wrong. The trade-off is that a return calculated across a dropped row spans more than one trading day.

### No look-ahead, enforced in code

Every strategy follows one contract: it receives price history **up to and including day t**, and returns the position to hold on **day t+1**.

The engine enforces this by construction. On each day it passes the strategy a slice of the data that ends at that day (`bars.iloc[:i+1]`). Future rows are simply not in the object the strategy receives, so they cannot be used, by accident or otherwise.

The engine then shifts each decision forward one day: the position decided from day t's data is the position actually held on day t+1. The last decision is discarded, because there is no day after the final bar to hold it on.

A worked example, using the same numbers as the alignment test (the rule here is "go long after any close below 95"):

| Day | Close | Rule decides (for tomorrow) | Position held today | Return today |
|---|---|---|---|---|
| 1 | 100 | flat | 0 | |
| 2 | 100 | flat | 0 | 0% |
| 3 | 90 | **long** | 0 | -10% (not held) |
| 4 | 100 | flat | **+1** | **+11.1%** (earned) |
| 5 | 110 | flat | 0 | +10% (not held) |

The signal fires on day 3, after the fall. The profit lands on day 4, the bounce. If the profit appeared on day 3, the rule would be trading on a price it had not yet seen.

The common shortcut is to give the strategy the entire dataset and shift its signal afterwards. That works only if nothing inside the strategy peeks forward, so it is enforced by convention. Here it is enforced by the structure of the code.

### Four tests guard the engine

| Test | What it checks |
|---|---|
| Strategy never sees the future | A recording strategy logs the last date it is shown on every call. The log must match the trading days exactly, in order, never running ahead. |
| Oracle produces impossible results | A deliberately cheating strategy peeks at tomorrow's return from outside the engine. It must produce an absurd Sharpe above 5. |
| Alignment on a hand-computed series | The worked example above. The +11.1% must land on day 4 and every other day must be zero. |
| Cost accounting in isolation | On flat prices, a strategy that flips long and short has a hand-computed turnover of 9 units. At 10 bps, total cost must be exactly 0.9%. |

The oracle test sounds backwards: why write a test where cheating succeeds? It is a **positive control**. It proves the engine's arithmetic is sensitive to look-ahead. If perfect foresight did *not* produce an impossible result, positions and returns would be misaligned in a way that would also hide a real look-ahead bug.

### Simple returns and log returns

There are two ways to measure a daily return, and each is right for a different job.

- **Simple returns** (`today / yesterday - 1`) are used inside the engine. Daily profit is `position x return - cost`, and that arithmetic only holds for simple returns: they scale directly with position size, and costs subtract from them directly.
- **Log returns** (`log(today / yesterday)`) are used for the statistics. They add up across time, which is what makes annualising by 252 exact and lets drawdown be computed from a cumulative sum.

`run.py` converts once, at the boundary between the two, with `np.log1p(net_returns)`.

### Transaction costs

```
turnover on day t = |position on day t - position on day t-1|
cost on day t     = turnover x cost_bps / 10,000
net return        = gross return - cost
```

The engine was built in two stages: first with costs switched off, until the look-ahead and alignment tests passed, then with costs added and tested separately. This kept the two kinds of bug apart, since a misaligned day and a double-charged cost look identical from the outside.

### Numerical stability: Welford's algorithm

The textbook formula for variance, `E[X^2] - (E[X])^2`, is correct on paper but fails on a computer when the mean is large compared with the spread.

Take values around 100,000,000 with noise of about 1. Their squares are around 10^16. A standard floating-point number holds only about 15 to 16 significant digits, so the formula subtracts two enormous, nearly equal numbers, and what is left is mostly rounding error. This is called **catastrophic cancellation**.

Welford's algorithm avoids it by updating a running mean and a running sum of squared deviations one value at a time, so it never forms the enormous squares. `welford.py` implements it (`RunningStats`), and a test runs both methods on 10,000 values around 100,000,000 with noise of standard deviation 1. The naive formula **loses every significant figure**: it returns a variance of exactly 0, against a true value of about 0.975. Welford's result agrees with the true value to about 9 significant figures. The headline statistics use pandas' standard deviation, which already uses a stable two-pass method; `welford.py` demonstrates the problem and the fix.

---

## 4. What this does not prove

**One asset, one period.** This project analyses ten years of daily SPY bars only. The results have not been tested on any other ETF or stock, and should not be assumed to generalise beyond SPY over this specific window.

**Survivorship bias does not apply here.** Survivorship bias arises when you select from a universe of stocks and test only those that survived long enough to still be listed today. This project holds a single, fixed ticker with no selection step, so the bias has no way to enter. That is not something avoided by design; it simply does not apply to a single-ticker backtest.

**One set of parameters, untested for robustness.** Only one parameter set (20 days, threshold 1) was ever run, so no adjustment for testing many variations is needed. Equally, nothing here shows whether nearby choices would behave similarly.

**Simplified costs.** Costs are a flat 5 bps per unit of turnover. Real costs vary with the spread, market conditions and trade size. The cost sweep shows the conclusion is sensitive to this figure: the Sharpe is positive below roughly 2.3 bps and negative above it.

**Idealised trade timing.** The backtest assumes a position decided from day t's close is held over day t+1, priced from that same close. In practice the signal is only known once the market has closed, so a real trade would fill at a later price. This flatters the strategy slightly.

**The bootstrap assumes independent days.** Resampling days independently destroys the patterns real returns have, such as volatile days clustering together. The interval is therefore likely too narrow: an optimistic estimate of the uncertainty, not a conservative one.

**Zero risk-free rate.** The Sharpe ratios here do not subtract the return available on cash. For part of this period cash paid several percent a year, which would lower both strategies' Sharpe ratios.

---

## Reproduce

```
python -m venv venv
venv\Scripts\activate            # Windows; on macOS/Linux: source venv/bin/activate
pip install pandas numpy pytest

python run.py                    # prints every number in this README
python -m pytest                 # runs all 15 tests
```

The bootstrap uses a fixed seed (42), so `run.py` produces identical output on every run.

## Project layout

```
backtest/
  data/spy.csv              raw daily SPY bars
  data/sample_bars.csv      small fixture used by the data tests
  src/backtest/
    data.py                 load and clean the CSV
    strategies.py           the Strategy contract and mean_reversion
    engine.py               run_backtest and BacktestResult
    stats.py                performance statistics and bootstrap
    welford.py              numerically stable running variance
  tests/
    test_data.py            4 tests: loading, junk rows, missing columns
    test_engine.py          4 tests: look-ahead, oracle, alignment, costs
    test_stats.py           5 tests: each statistic against hand-computed values
    test_welford.py         2 tests: Welford vs the naive formula
  run.py                    reproduces every number in this README
```
