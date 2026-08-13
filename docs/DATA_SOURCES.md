# Data Sources

## Source modes

- `KEYWORD`: 接收系统生成的关键词 Probe，例如 GitHub Search。
- `REGION`: 接收地区/市场代码，例如 Google Trends Trending Now RSS。
- `PUSH_ONLY`: 系统不主动采集，由授权研究环境推送 Observation，例如 Instrumented App。

## GitHub

- Method: `OFFICIAL_API`
- Evidence: `A`
- Query mode: `KEYWORD`
- Current surface: repository search.

## Google Trends Trending Now

- Method: `OFFICIAL_EXPORT`
- Evidence: `B`
- Query mode: `REGION`
- Current surface: Trending Now RSS export.
- Default regions: `US,TW`; configure with `GOOGLE_TRENDS_GEOS`.

Google Trends Help states that Trending Now supports RSS export and covers 100+ countries/regions. The separate Google Trends API remains an Alpha program with limited tester access as of 2026-08-12. Therefore this project does not present the Alpha API as generally available.

Official references:

- https://support.google.com/trends/answer/3076011
- https://developers.google.com/search/apis/trends

## Instrumented App

- Method: `INSTRUMENTED_APP`
- Evidence: `C`
- Query mode: `PUSH_ONLY`
- Active `collect()` is intentionally rejected.
- Authorized observations use `/api/v1/instrumented-app/observations`.
