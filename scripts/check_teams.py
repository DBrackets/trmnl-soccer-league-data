#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Compare a repository team JSON file with an ESPN teams endpoint."
    )

    parser.add_argument(
        "--file",
        required=True,
        help="Repository-relative path to the local JSON file.",
    )

    parser.add_argument(
        "--endpoint",
        required=True,
        help="HTTPS ESPN teams endpoint to compare against.",
    )

    parser.add_argument(
        "--compare-names",
        choices=["true", "false"],
        default="false",
        help="Fail when a matching ID has a different team name.",
    )

    parser.add_argument(
        "--report",
        default="team-comparison-report.md",
        help="Path for the generated Markdown report.",
    )

    return parser.parse_args()


def get_repository_file(path_string):
    repository_root = Path.cwd().resolve()
    requested_path = Path(path_string)

    if requested_path.is_absolute():
        raise ValueError(
            "Use a repository-relative file path, not an absolute path."
        )

    file_path = (repository_root / requested_path).resolve()

    if repository_root not in file_path.parents and file_path != repository_root:
        raise ValueError(
            "The requested file must be inside this repository."
        )

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Cannot find repository file: {path_string}"
        )

    return file_path


def validate_endpoint(endpoint):
    parsed = urlparse(endpoint)

    if parsed.scheme != "https":
        raise ValueError("The endpoint must use HTTPS.")

    if parsed.netloc not in {
        "site.api.espn.com",
        "site.web.api.espn.com",
    }:
        raise ValueError(
            "The endpoint host must be site.api.espn.com "
            "or site.web.api.espn.com."
        )

    if not parsed.path.endswith("/teams"):
        raise ValueError(
            "The endpoint must be an ESPN URL ending in /teams."
        )

    return endpoint


def fetch_json(url):
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "trmnl-soccer-league-data-team-checker/1.0",
        },
    )

    with urlopen(request, timeout=30) as response:
        return json.load(response)


def get_espn_teams(payload):
    teams = {}

    for sport in payload.get("sports", []):
        for league in sport.get("leagues", []):
            for item in league.get("teams", []):
                team = item.get("team", {})
                team_id = str(team.get("id", "")).strip()
                team_name = str(team.get("displayName", "")).strip()

                if team_id:
                    teams[team_id] = team_name

    if not teams:
        raise ValueError(
            "No teams were found in the ESPN response. "
            "Check that the supplied URL is a valid ESPN soccer "
            "endpoint ending in /teams."
        )

    return teams


def get_local_teams(payload):
    if not isinstance(payload, list):
        raise ValueError(
            "The local JSON must be a top-level list of objects, "
            'for example: [{"name": "Team", "id": "123"}].'
        )

    teams = {}

    for item in payload:
        if not isinstance(item, dict):
            continue

        team_id = str(item.get("id", "")).strip()
        team_name = str(item.get("name", "")).strip()

        if team_id:
            teams[team_id] = team_name

    if not teams:
        raise ValueError(
            'No teams were found. Each entry must contain an "id" '
            'and a "name" field.'
        )

    return teams


def markdown_list(items):
    if not items:
        return "_None_"

    return "\n".join(f"- {item}" for item in items)


def make_report(
    file_path,
    endpoint,
    compare_names,
    espn_teams,
    local_teams,
):
    espn_ids = set(espn_teams)
    local_ids = set(local_teams)

    missing_from_file = sorted(espn_ids - local_ids)
    extra_in_file = sorted(local_ids - espn_ids)

    name_mismatches = sorted(
        (
            team_id,
            espn_teams[team_id],
            local_teams[team_id],
        )
        for team_id in espn_ids & local_ids
        if espn_teams[team_id] != local_teams[team_id]
    )

    ids_match = not missing_from_file and not extra_in_file
    exact_match = ids_match and (
        not compare_names or not name_mismatches
    )

    if exact_match and compare_names:
        status = "✅ IDs and names match exactly"
    elif exact_match:
        status = "✅ IDs match; name differences are informational"
    else:
        status = "❌ Differences found"

    lines = [
        "# Team comparison report",
        "",
        f"**Status:** {status}",
        "",
        f"- Repository file: `{file_path}`",
        f"- ESPN endpoint: `{endpoint}`",
        f"- Compare names strictly: **{compare_names}**",
        f"- ESPN team records: **{len(espn_teams)}**",
        f"- Repository team records: **{len(local_teams)}**",
        "",
        "## IDs in ESPN but missing locally",
        "",
        markdown_list(
            [
                f"`{team_id}` — {espn_teams[team_id]}"
                for team_id in missing_from_file
            ]
        ),
        "",
        "## IDs in the file but absent from ESPN",
        "",
        markdown_list(
            [
                f"`{team_id}` — {local_teams[team_id]}"
                for team_id in extra_in_file
            ]
        ),
        "",
        "## Same ID, different name",
        "",
    ]

    if name_mismatches:
        lines.extend(
            [
                "| ID | ESPN `displayName` | Local `name` |",
                "|---|---|---|",
            ]
        )

        for team_id, espn_name, local_name in name_mismatches:
            lines.append(
                f"| `{team_id}` | {espn_name} | {local_name} |"
            )
    else:
        lines.append("_None_")

    lines.append("")

    return exact_match, "\n".join(lines)


def main():
    args = parse_arguments()
    compare_names = args.compare_names == "true"

    try:
        file_path = get_repository_file(args.file)
        endpoint = validate_endpoint(args.endpoint)

        with file_path.open(encoding="utf-8") as file:
            local_payload = json.load(file)

        espn_payload = fetch_json(endpoint)

        local_teams = get_local_teams(local_payload)
        espn_teams = get_espn_teams(espn_payload)

        exact_match, report = make_report(
            args.file,
            endpoint,
            compare_names,
            espn_teams,
            local_teams,
        )

        Path(args.report).write_text(report, encoding="utf-8")
        print(report)

        return 0 if exact_match else 1

    except FileNotFoundError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    except (HTTPError, URLError, TimeoutError) as error:
        print(
            f"ERROR: Could not retrieve ESPN data: {error}",
            file=sys.stderr,
        )
        return 2
    except (json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
