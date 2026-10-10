# Idea Funnel sources (D-024, D-025)

The PLANNER curates this list using PromptQL web search (D-025). sirooj can veto or edit any entry. The funnel only appends under "Discovered (unreviewed)".

Trust tiers:
- **A:** primary research, reproducible.
- **B:** practitioner with evidence (data, code, or stated sample).
- **C:** discussion; leads only.

Access rungs (`srj-research-web`): 0 = platform API (`arxiv`, `gh`, `praw`, `youtube-transcript-api`); 1 = `trafilatura`; 2 = `crawl4ai`; 3 = `browser-use`; `vault` = sirooj's Obsidian vault (manual capture, or `tools/tg_export.py`, see W5).

Rules for every source:
- **Spec, not code.** Read third-party code to understand an idea. Never commit it, never vendor GPL/AGPL code, and never run it on a challenge or funded account (own-code rule).
- **E-008 check.** Unconditioned US-index open scalping (ORB, ORB fade, Gao intraday momentum) is a dead idea. A candidate in that family must say what new condition it adds, or it is rejected.
- **Larp check** (tier C, and any B without data): is there a stated sample, costs, and out-of-sample? If not, it stays a lead.

## Curated: platforms
| Source | Access (rung) | Tier | Notes |
|---|---|---|---|
| arXiv q-fin.TR, q-fin.ST | `arxiv` (0) | A | intraday microstructure, volume, opening range, VWAP |
| SSRN (finance, market microstructure) | `trafilatura` (1) | A | summary only; often paywalled PDFs |
| Quantpedia (free pages) | `trafilatura` (1) | B | summary only; copyrighted |
| Concretum Research: concretumgroup.com + concretumgroup.substack.com (Zarattini, Aziz, Barbon) | `trafilatura` (1) | A/B | intraday VWAP and noise-area momentum on SPY/QQQ/ES/NQ with published code. Momentum papers are Gao-family: apply the E-008 check |
| Quantitativo (quantitativo.com) | `trafilatura` (1) | B | reimplements papers on ES/NQ with stats, e.g. "Intraday Momentum for ES and NQ", "Volume Shocks and Overnight Returns" |
| Robot Wealth (robotwealth.com, Kris Longmore) | `trafilatura` (1) | B | method and variance/overfitting discipline more than ready strategies |
| Alvarez Quant Trading blog | `trafilatura` (1) | B | rigorous rule testing; mostly equities/daily, good for method |
| TradingStats (tradingstats.net) | `crawl4ai` (2) | B | ES/NQ initial-balance, IB-VPOC and retest statistics 2015–2025. Futures, not CFD: re-measure on Dukascopy before trusting |
| IB Lab (iblab.io) | `crawl4ai` (2) | C | initial-balance stats across NQ, ES, GC, CL; leads only |
| ATAS Learn, NinjaTrader order-flow blog | `trafilatura` (1) | C | vocabulary for footprint/delta/VP concepts; vendor education, no evidence |
| GitHub (intraday, volume profile, VWAP strategies) | `gh` (0) | B | code as a spec only. Seeds: `ZovraT/MT5-volume-profile-indicator`, `Andre-Luis-Lopes-da-Silva/Volume-profile-for-metatrader-5`, topics `volume-profile`, `volume-profile-indicator` |
| MQL5 Code Base (mql5.com/en/code) | `crawl4ai` (2) | C | indicator/EA ideas, e.g. "Adaptive VWAP Institutional" (awran5). Spec only; capture to the vault, never to git |
| QuantConnect forum | `crawl4ai` (2) | C | leads; posts often include backtest links |
| Elite Trader, Automated Trading forum | `crawl4ai` (2) | C | leads only; many ORB/Gao threads (E-008) |
| r/algotrading | `praw` (0) | C | leads only |
| Forex Factory (trading systems threads) | `crawl4ai` (2) | C | leads only; heavy noise |
| YouTube (volume profile and order-flow educators) | `youtube-transcript-api` (0) | C | larp check on every video. sirooj names the channels |
| X / Twitter accounts | `vault`; the planner can search X live | C | see "Discovered"; promote after sirooj's review |
| Discord servers | `vault` (manual) | C | no automation (D-025). sirooj names the servers |
| Telegram channels | `vault` (`tg_export.py`, W5) | C | allow-list only; sirooj names the channels |

## Curated: seed reading list (tier A unless marked)
Grouped by the question they answer for this project.

**Validating the CFD volume proxy (D-006, D-007): how good is tick-rule CVD?**
- Ellis, Michaely, O'Hara (2000), "The Accuracy of Trade Classification Rules: Evidence from Nasdaq", JFQA.
- Chakrabarty, Pascual, Shkilko (2015), "Evaluating trade classification algorithms: Bulk volume classification versus the tick rule and the Lee-Ready algorithm".
- Perlin, Brooks, Dufour (2013), "On the performance of the tick test".
- Frömmel, D'Hoore, Lampaert (2020), "The Accuracy of Trade Classification Systems on the Foreign Exchange Market" (RUB/USD). Closest to the FX use case.

**VWAP and volume profile**
- Zarattini, Aziz (2023), "Volume Weighted Average Price (VWAP): The Holy Grail for Day Trading Systems", SSRN 4631351.
- Jóźwicki, Trippner (2025), "Use of the volume profile in making investment decisions on the stock market" (ResearchGate). Tier B: check the method.
- CBOT, "A Six-Part Study Guide to Market Profile" (profiletrading.com PDF). Tier B: concepts (value area, initial balance), no tests.
- Dalton, Dalton, Jones, *Markets in Profile* (Wiley). Tier B book: auction-market theory.

**Order flow and impact (what OFI can and can't do)**
- Cont, Cucuringu, Zhang (2023), "Cross-impact of order flow imbalance in equity markets", Quantitative Finance.
- Tóth, Eisler, Bouchaud (2017), "The Short-Term Price Impact of Trades Is Universal".
- Eisler, Bouchaud, Kockelkoren (2009), "The price impact of order book events".

**FX intraday timing (pilot: EURUSD, GBPUSD, USDJPY)**
- Breedon, Ranaldo (2013), "Intraday Patterns in FX Returns and Order Flow", JMCB.
- Ito, Hashimoto (2006), "Intraday seasonality in activities of the foreign exchange markets: Evidence from the electronic broking system".
- Andersen, Bollerslev (1998), "Intraday volatility in interest-rate and foreign-exchange markets", J. Futures Markets.
- Krohn, Mueller, Whelan (2020), "Foreign Exchange Fixings and Returns Around the Clock".
- Husselmann, Kasikov (2019), "Trend-following market behaviour at the 4pm London time BFIX and WMR fixing windows".
- Evans, O'Neill, Rime, Saakvitne (2018), "Fixing the Fix? Assessing the Effectiveness of the 4pm Fix Benchmark".

**US index intraday (USA500IDXUSD, USATECHIDXUSD)**
- Gao, Han, Li, Zhou (2018), "Intraday Momentum: The First Half-Hour Return Predicts the Last Half-Hour Return". Reference only: dead idea, E-008.
- Zarattini, Aziz, Barbon (2024), "Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)", SSRN 4824172. Gao-family: E-008 check (the noise-area condition is the only new part).
- Iwanaga, Sakemoto (2026), "Does overnight return predict the first half-hour return for U.S. market indices?"
- Yu, Rentzler, Wolf (2005), "Nasdaq-100 Index Futures: Intraday Momentum or Reversal?"

**Overfitting and trial counting (E-016, `TRIALS.csv`)**
- Bailey, López de Prado (2014), "The Deflated Sharpe Ratio". Needs the trial count, which is why `TRIALS.csv` exists.
- Bailey, Borwein, López de Prado, Zhu (2016), "The Probability of Backtest Overfitting".

## Vault inbox (W5)
Root: `D:\SRJ Venture\private\vault\` (an Obsidian vault, outside git). The funnel reads `inbox\**` as rung `vault`.

```
vault\
  inbox\web\                 Obsidian Web Clipper output (articles, posts, forum threads)
  inbox\x\                   X posts/threads, pasted or clipped
  inbox\youtube\             transcript + your notes
  inbox\discord\<server>\    manual copy, one note per thread or day
  inbox\telegram\<channel>\  tg_export.py output, one note per day
  inbox\ea_code\<author>\<name>\   raw .mq5/.mqh/.pine + a README note
  papers\                    PDFs + one summary note each
  telegram_allowlist.txt
```

Front-matter on every note (the funnel rejects notes without it):
```
---
source: discord | telegram | x | web | youtube | ea_code | paper
url:
author:
date: YYYY-MM-DD
tier: A | B | C
captured_by: sirooj | tg_export | web_clipper
licence: unknown | MIT | GPL | proprietary | ...
---
```

Capture methods:
- **Web, X, forums:** Obsidian Web Clipper (browser extension) into `inbox\web\` or `inbox\x\`.
- **Telegram:** `tools/tg_export.py` (Telethon, your own account, read-only, allow-listed channels), or Telegram Desktop's built-in "Export chat history" for one-offs.
- **Discord:** copy manually. User-token exporters and self-bots break Discord's ToS and can get the account banned. A bot token is allowed only where the server admin invites the bot.
- **EA/indicator code:** paste into `inbox\ea_code\`. The funnel reads it as a spec; nothing from it is committed or run on an account.

## Out of scope
- Signal sellers, "pass your challenge" services, copy-trading groups, paid-signal Telegram channels.
- Prop-firm "pass rate" statistic aggregators (mostly affiliate sites with estimated numbers). Never use them as sim inputs.
- Crypto-only, options-only and single-stock ideas that don't port to the pilot CFDs.

## Discovered (unreviewed)
- 2026-10-10, planner, X live search. sirooj to review; promote or remove:
  - `@ConcretumR`: Concretum Research; intraday US futures backtests with code. (Likely B, matches the Concretum row.)
  - `@QuantifiedStrat`: rule-based strategy backtests with stats, incl. session effects. (C until checked.)
  - `@quantseeker`: summaries of academic papers on intraday volatility and time-of-day effects. (C; a pointer to A papers.)
  - `@alma271828`: futures posts on volume profile, VWAP and opening auctions with coded indicators. (C until checked.)
  - `@julie_wade`: VIX/realized-vol thresholds vs ES intraday ranges. (C until checked.)
