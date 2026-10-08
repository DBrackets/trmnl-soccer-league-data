# trmnl-soccer-league-data

Static team-list JSON for the "[Copy] EPL Fixtures" TRMNL plugin's dynamic "My Team" picker.

Each file is a flat array of `{"name": "...", "id": "..."}` objects — the `id` is the ESPN team ID used
by `https://site.web.api.espn.com/apis/site/v2/sports/soccer/{league}/...` endpoints.

- `eng.1.json` — Premier League
- `eng.2.json` — Championship
- `eng.3.json` — League One
- `eng.4.json` — League Two

Rosters are a point-in-time snapshot (correct as of the 2026/27 season). Re-pull from
`https://site.web.api.espn.com/apis/site/v2/sports/soccer/{league}/teams` and regenerate each file
if promotion/relegation or a league restructure makes these stale — typically needed once a season,
around August.

Consumed by the TRMNL plugin's `myteam` custom field as an `xhrSelect` with `depends_on: league` and
`remote.url: https://raw.githubusercontent.com/DBrackets/trmnl-soccer-league-data/main/{{league}}.json`.
