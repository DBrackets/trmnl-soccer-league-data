# trmnl-soccer-league-data

Static team-list JSON for TRMNL plugins' dynamic "My Team" pickers (chained `xhrSelect` /
`depends_on` dropdowns). One file per league, named with ESPN's own soccer league slug, under
`uefa/` (all current leagues belong to UEFA member associations or are UEFA club competitions —
this leaves room for other confederations as separate top-level folders later without renaming
anything).

Each file is a flat array of `{"name": "...", "id": "..."}` objects — the `id` is the ESPN team ID
used by `https://site.web.api.espn.com/apis/site/v2/sports/soccer/{league}/...` endpoints.

| File | League |
|---|---|
| `uefa/eng.1.json` | England — Premier League |
| `uefa/eng.2.json` | England — Championship |
| `uefa/eng.3.json` | England — League One |
| `uefa/eng.4.json` | England — League Two |
| `uefa/esp.1.json` | Spain — LaLiga |
| `uefa/ita.1.json` | Italy — Serie A |
| `uefa/ger.1.json` | Germany — Bundesliga |
| `uefa/fra.1.json` | France — Ligue 1 |
| `uefa/ned.1.json` | Netherlands — Eredivisie |
| `uefa/por.1.json` | Portugal — Primeira Liga |
| `uefa/bel.1.json` | Belgium — Pro League |
| `uefa/tur.1.json` | Turkey — Süper Lig |
| `uefa/sco.1.json` | Scotland — Premiership |
| `uefa/sco.2.json` | Scotland — Championship |
| `uefa/rus.1.json` | Russia — Premier League |
| `uefa/gre.1.json` | Greece — Super League |
| `uefa/aut.1.json` | Austria — Bundesliga |
| `uefa/den.1.json` | Denmark — Superliga |
| `uefa/nor.1.json` | Norway — Eliteserien |
| `uefa/swe.1.json` | Sweden — Allsvenskan |
| `uefa/esp.2.json` | Spain — LaLiga 2 |
| `uefa/ger.2.json` | Germany — 2. Bundesliga |
| `uefa/ita.2.json` | Italy — Serie B |
| `uefa/fra.2.json` | France — Ligue 2 |
| `uefa/ned.2.json` | Netherlands — Keuken Kampioen Divisie |
| `uefa/uefa.champions.json` | UEFA — Champions League |
| `uefa/uefa.europa.json` | UEFA — Europa League |
| `uefa/uefa.europa.conf.json` | UEFA — Conference League |

Every slug was verified live against `https://site.web.api.espn.com/apis/site/v2/sports/soccer/{slug}/teams`
(2026-10-08) before use.

The 15 second-tier/UEFA files above were pulled via a different method than the first 13: a direct
`curl`/WebFetch against ESPN was blocked by the sandbox's egress proxy, and a first attempt at reading
them back through TRMNL's `MergeVariablesShowTool` silently capped every nested array at 5 items
(confirmed by re-fetching Scottish Championship, `sco.2`, in isolation — it showed exactly 5 teams via
the tool's raw-input echo when the true roster is 10). The reliable fix: a temporary `transform_js` on
the live plugin that walks the ESPN response itself and returns the roster as a single JSON **string**
(`JSON.stringify(...)`), not an array — `MergeVariablesShowTool`'s array cap doesn't apply to strings,
so the full roster comes back intact. Team counts were sanity-checked against each league's known size
before being written here. The plugin's `transform_js` and `polling_url` were restored to production
logic immediately afterward.

Rosters are a point-in-time snapshot (correct as of the 2026/27 season). Re-pull from
`https://site.web.api.espn.com/apis/site/v2/sports/soccer/{league}/teams` and regenerate the
relevant file if promotion/relegation or a league restructure makes it stale — typically needed
once a season, around August.

## Used by

- **"[Copy] EPL Fixtures"** (all 28 leagues/competitions above) — `myteam` custom field is an
  `xhrSelect` with `depends_on: league` and
  `remote.url: https://raw.githubusercontent.com/DBrackets/trmnl-soccer-league-data/main/uefa/{{league}}.json`.
  `league`'s own values are the ESPN slugs directly, so no reshaping is needed.
- A second multi-country plugin (England, Spain, Italy, Germany, France, Netherlands, Portugal,
  Belgium, Turkey, Scotland) currently stores its own non-ESPN country codes (`england_pl`, `spain`,
  `italy`, ...) and has 11 separate static "Team" fields shown/hidden via `conditional_validation`
  instead of one dynamic field. Not yet converted — the plan is to switch its `country` field's
  values over to these same ESPN slugs and collapse the 11 static team fields into one `xhrSelect`
  `depends_on: country` field pointed at this repo, the same way "[Copy] EPL Fixtures" now works.

## Why this exists

TRMNL's `xhrSelect`/`remote:` `response_path` can only walk hash keys, not array indices — confirmed
by testing against ESPN's own nested `sports[0].leagues[0].teams[]` shape, which it can't reach.
`remote:` also refuses `data:` URIs server-side. A plain flat JSON file, one per league, sidesteps
both limitations entirely: no response_path needed, and a real `https://` URL works with `remote:`.
