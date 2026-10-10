---
name: srj-research-web
description: How the CODER finds and fetches web sources (papers, blogs, forums, videos, repos) with the free fetch ladder and the capped DeepAPI search. Use for any web research, including Idea Funnel runs.
---

# SRJ research-web (D-024)

Informed by `davidondrej/skills` (deepapi, varied-search, browser-use, signal-from-expert) and rewritten for SRJ.

## Setup (once, task W2)
- Install into the optional `research` dependency group, not the core deps: `trafilatura`, `crawl4ai`, `browser-use`, `arxiv`, `youtube-transcript-api`, `yt-dlp`, and optionally `praw`.
- Keep every cache and browser binary on D: (C: is nearly full), for example `PLAYWRIGHT_BROWSERS_PATH=D:\SRJ Venture\.cache\ms-playwright`. Confirm each tool's variable and record it in `docs/RUNBOOK.md`.
- Secrets (the DeepAPI key, Reddit app keys) live in `D:\SRJ Venture\.secrets\`, outside the repo. Never print, log or commit them.

## Fetch ladder: always use the lowest rung that works
0. **Platform API.** arXiv → `arxiv`. YouTube → `youtube-transcript-api`, plus `yt-dlp` for metadata. Reddit → `praw`. GitHub → `gh`.
1. **Static page** → `trafilatura` (main text to markdown).
2. **Empty or shell result** → `crawl4ai` (headless render to markdown).
3. **Needs clicks, pagination or a login** → `browser-use`. Stop and ask the OPERATOR before any login, purchase, CAPTCHA, form submission or consent prompt.

Go up one rung only when the current rung fails or returns no real text. Log which rung worked for each source.

## Discovery
1. Start from `research/funnel/SOURCES.md` (curated).
2. Use platform search before open-web search: an arXiv query, `gh search repos`, YouTube through `yt-dlp` `ytsearch`, Reddit search through `praw`.
3. Use open-web search through DeepAPI `POST /v1/search/web` only when steps 1–2 don't reach the funnel floor:
   - Run at least 5 separate, varied queries per topic, and ask for 10+ results per query.
   - Send a unique `Idempotency-Key` per POST, and reuse it on a retry.
   - Send `dryRun: true` first when unsure of the cost.
   - **Weekly cap: $3.00** across all DeepAPI calls (Monday–Sunday, Asia/Bangkok). Log each call's `debitMicrousd` in `research/funnel/runs.log`. At the cap, stop searching and log `deepapi_cap_reached`.
   - Use deep research (`/v1/research/deep`) only when a relay asks for it, with the relay's `maxCostUsd`.
   - If no key is set, skip DeepAPI and log `deepapi_unavailable`. Never block on it.

## Saving sources (verbatim, private)
- Save every source you will cite as `D:\SRJ Venture\private\funnel\sources\<hash>\NN-slug.md`: a header (title, URL, author, published date, retrieval date, rung), then the verbatim main text. Strip layout junk only; never edit the prose.
- That folder is outside the repo. Never commit source text: the repo is public.
- Committed files may carry one quote per source, of at most 15 words, copied from the saved file and cited as `NN-slug.md:START-END`.

## Source scepticism (larp check)
Record for every source:
- Is there a real trade list or P&L, or only a screenshot or a claim?
- Is the performance in-sample only, out-of-sample, live, or unstated?
- Does the author sell a course, an indicator, signals, or a challenge-passing service?
- Is the volume real exchange volume, footprint or L2? We only have bid-tick count and tick-rule CVD, so note the port.
- Does an independent source corroborate or contradict it?

## Never
- Download market data, or treat a source's numbers as SRJ evidence.
- Use the browser for something a plain fetch can read.
- Bypass paywalls, logins or robots blocks.
