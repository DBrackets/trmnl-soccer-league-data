# trmnl-soccer-league-data

Static team-list JSON for ESPN API team codes. One file per league, named with ESPN's league slug. Filed 
under member associations.

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

Useful for `myteam` custom fields as an `xhrSelect` with `depends_on: league` and
  `remote.url: https://raw.githubusercontent.com/DBrackets/trmnl-soccer-league-data/main/uefa/{{league}}.json`.

## Adding another confederation
Each confederation gets its own top-level folder, holding the same flat `{"name", "id"}` JSON files named by ESPN slug.

## Checks
`scripts/check_all_teams.py --directory <folder>` checks one confederation folder at a time.

## Why this exists
TRMNL's `xhrSelect`/`remote:` `response_path` can only walk hash keys, not array indices — 
`remote:` also refuses `data:` URIs server-side. A plain flat JSON file, one per league, sidesteps
both limitations entirely: no response_path needed, and a real `https://` URL works with `remote:`.
