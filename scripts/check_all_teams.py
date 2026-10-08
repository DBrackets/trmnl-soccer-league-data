#!/usr/bin/env python3

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ESPN_URL_TEMPLATE = (
    "https://site.web.api.espn.com/apis/site/v2/sports/"
    "soccer/{league_slug}/teams"
)

DEFAULT_EXCLUDED_FILES = {
    "package.json",
    "package-lock.json",
    "composer.json",
    "composer.lock",
}


@dataclass
class CheckResult:
    filename: str
    league_slug: str
    endpoint: str
    status: str
    espn_count: int = 0
    local_count: int = 0
    missing_from_file: list = None
    extra_in_file: list = None
    name_mismatches: list = None
    error: str = ""


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Compare all league JSON files with their ESPN team endpoints."
    )

    parser.add_argument(
        "--directory",
        default=".",
        help="Directory containing league JSON files. Default: repository root.",
    )

    parser.add_argument(
        "--compare-names",
        choices=["true", "false"],
        default="false",
        help="Fail when matching IDs have different names.",
    )

    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help=(
            "Filename to skip. Repeat this argument for multiple files. "
            "Example: --exclude package.json"
        ),
    )

    parser.add_argument(
        "--report",
        default="all-team-comparison-report.md",
        help="Output path for the generated Markdown report.",
    )

    return parser.parse_args()


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
        raise ValueError("No teams found in ESPN's response.")

    return teams


def get_local_teams(payload):
    if not isinstance(payload, list):
        raise ValueError(
            "Expected a top-level JSON list of team objects."
        )

    teams = {}

    for item in payload:
        if not isinstance(item, dict):
            continue

        team_id = str(item.get("id", "")).strip()
        team_name = str(item.get("name", "")).strip()

        if not team_id:
            raise ValueError(
                'Found a team entry without an "id" field.'
            )

        if not team_name:
            raise ValueError(
                'Found a team entry without a "name" field.'
            )

        if team_id in teams:
            raise ValueError(
                f'Duplicate local team ID "{team_id}".'
            )

        teams[team_id] = team_name

    if not teams:
        raise ValueError("No local teams found in the JSON file.")

    return teams


def get_json_files(directory, excluded_files):
    directory_path = Path(directory).resolve()

    if not directory_path.is_dir():
        raise ValueError(f"Directory does not exist: {directory}")

    excluded = DEFAULT_EXCLUDED_FILES | set(excluded_files)

    return sorted(
        path
        for path in directory_path.glob("*.json")
        if path.name not in excluded
    )


def compare_teams(
    filename,
    league_slug,
    endpoint,
    local_teams,
    espn_teams,
    compare_names,
):
    local_ids = set(local_teams)
    espn_ids = set(espn_teams)

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
    passed = ids_match and (
        not compare_names or not name_mismatches
    )

    if passed and compare_names:
        status = "PASS — IDs and names match"
    elif passed:
        status = "PASS — IDs match"
    else:
        status = "FAIL — differences found"

    return CheckResult(
        filename=filename,
        league_slug=league_slug,
        endpoint=endpoint,
        status=status,
        espn_count=len(espn_teams),
        local_count=len(local_teams),
        missing_from_file=missing_from_file,
        extra_in_file=extra_in_file,
        name_mismatches=name_mismatches,
    )


def check_file(file_path, compare_names):
    league_slug = file_path.stem
    endpoint = ESPN_URL_TEMPLATE.format(league_slug=league_slug)

    try:
        with file_path.open(encoding="utf-8") as file:
            local_payload = json.load(file)

        local_teams = get_local_teams(local_payload)
        espn_payload = fetch_json(endpoint)
        espn_teams = get_espn_teams(espn_payload)

        return compare_teams(
            filename=file_path.name,
            league_slug=league_slug,
            endpoint=endpoint,
            local_teams=local_teams,
            espn_teams=espn_teams,
            compare_names=compare_names,
        )

    except (
        FileNotFoundError,
        HTTPError,
        URLError,
        TimeoutError,
        json.JSONDecodeError,
        ValueError,
    ) as error:
        return CheckResult(
            filename=file_path.name,
            league_slug=league_slug,
            endpoint=endpoint,
            status="ERROR",
            error=str(error),
            missing_from_file=[],
            extra_in_file=[],
            name_mismatches=[],
        )


def markdown_list(items):
    return "\n".join(f"- {item}" for item in items) if items else "_None_"


def build_report(results, compare_names):
    pass_count = sum(result.status.startswith("PASS") for result in results)
    fail_count = sum(
        result.status.startswith("FAIL") for result in results
    )
    error_count = sum(result.status == "ERROR" for result in results)

    overall_pass = fail_count == 0 and error_count == 0

    lines = [
        "# ESPN team-data comparison report",
        "",
        (
            "**Overall status:** ✅ All checks passed"
            if overall_pass
            else "**Overall status:** ❌ One or more checks failed"
        ),
        "",
        f"- League files checked: **{len(results)}**",
        f"- Passed: **{pass_count}**",
        f"- Failed: **{fail_count}**",
        f"- Errors: **{error_count}**",
        f"- Strict name comparison: **{compare_names}**",
        "",
        "## Summary",
        "",
        "| File | League slug | ESPN | Local | Result |",
        "|---|---|---:|---:|---|",
    ]

    for result in results:
        espn_count = str(result.espn_count) if result.espn_count else "—"
        local_count = str(result.local_count) if result.local_count else "—"

        lines.append(
            f"| `{result.filename}` | `{result.league_slug}` | "
            f"{espn_count} | {local_count} | {result.status} |"
        )

    for result in results:
        lines.extend(
            [
                "",
                f"## {result.filename}",
                "",
                f"- ESPN endpoint: `{result.endpoint}`",
                f"- Result: **{result.status}**",
            ]
        )

        if result.error:
            lines.extend(
                [
                    "",
                    "### Error",
                    "",
                    f"```text\n{result.error}\n```",
                ]
            )
            continue

        lines.extend(
            [
                "",
                "### IDs in ESPN but missing locally",
                "",
                markdown_list(
                    [
                        f"`{team_id}` — {result_missing_name(result, team_id)}"
                        for team_id in result.missing_from_file
                    ]
                ),
                "",
                "### IDs in the file but absent from ESPN",
                "",
                markdown_list(result.extra_in_file),
                "",
                "### Same ID, different name",
                "",
            ]
        )

        if result.name_mismatches:
            lines.extend(
                [
                    "| ID | ESPN `displayName` | Local `name` |",
                    "|---|---|---|",
                ]
            )

            for team_id, espn_name, local_name in result.name_mismatches:
                lines.append(
                    f"| `{team_id}` | {espn_name} | {local_name} |"
                )
        else:
            lines.append("_None_")

    lines.append("")
    return overall_pass, "\n".join(lines)


def result_missing_name(result, team_id):
    # The ID itself is the critical diagnostic. This helper keeps the
    # report generation independent from the original ESPN dictionary.
    return "Present in ESPN"


def main():
    args = parse_arguments()
    compare_names = args.compare_names == "true"

    try:
        files = get_json_files(args.directory, args.exclude)

        if not files:
            raise ValueError(
                "No eligible JSON files were found in the selected directory."
            )

        results = [
            check_file(file_path, compare_names)
            for file_path in files
        ]

        overall_pass, report = build_report(results, compare_names)

        Path(args.report).write_text(report, encoding="utf-8")
        print(report)

        return 0 if overall_pass else 1

    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
