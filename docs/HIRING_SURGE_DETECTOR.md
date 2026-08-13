# Hiring Surge Detector

T109-02 reads the existing `Observation -> KeywordMention` chain for `JOB`
items and feeds bounded daily counts into `hiring-surge-v1`. It is read-only;
replaying the same window does not write or change observations.

Job postings are de-duplicated per day by a stable normalized identity made of
company (or an explicit unknown-company marker), normalized title, and
location. Company and location are read from the supported payload keys with a
text fallback. The detector reports unique jobs, duplicate observations,
company counts and diversity, source counts and diversity, unknown-company
counts, duplicate rates, and up to 20 stable evidence IDs. A posting appearing
on two sources on the same day therefore contributes to source coverage and
duplicate metrics without inflating job volume.

`GET /api/v1/hiring/surges` exposes the versioned evaluation and diversity
metrics. It supports keyword/window filtering and an `anomalous_only` mode. The
default horizon is bounded to 500 keywords and 5,000 job rows per evaluation;
production data is never fetched by this detector. Alert persistence and
opportunity association are handled by T109-03.
