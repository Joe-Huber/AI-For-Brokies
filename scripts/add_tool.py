import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from github import Github

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import generate_readme


def parse_issue_body(body):
    fields = {}
    patterns = {
        "tool_name": r"### Tool Name\s+(.*?)(?=###|$)",
        "tool_link": r"### Tool Link\s+(.*?)(?=###|$)",
        "category": r"### Category\s+(.*?)(?=###|$)",
        "description": r"### Description\s+(.*?)(?=###|$)",
        "free_tier": r"### Free Tier\s+(.*?)(?=###|$)",
        "score": r"### Score\s+(.*?)(?=###|$)",
        "tags": r"### Tags\s+(.*?)(?=###|$)",
        "notes": r"### Notes\s+(.*?)(?=$)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, body or "", re.DOTALL)
        fields[key] = match.group(1).strip() if match and match.group(1).strip() else None

    return fields


def parse_score(score):
    if not score:
        return None

    match = re.fullmatch(r"([0-9]|10)/10", score.strip())
    if not match:
        return None

    return int(match.group(1))


def parse_tags(tags):
    if not tags:
        return []

    raw_tags = re.split(r"[\s,]+", tags.strip())
    return [tag.strip().strip("`") for tag in raw_tags if tag.strip().strip("`")]


def issue_fields_to_tool(fields):
    return {
        "name": fields.get("tool_name"),
        "url": fields.get("tool_link"),
        "category": fields.get("category"),
        "description": fields.get("description"),
        "free_tier": fields.get("free_tier"),
        "score": parse_score(fields.get("score")),
        "tags": parse_tags(fields.get("tags")),
        "notes": fields.get("notes") or "-",
    }


def validate_submission(fields, tool, existing_tools):
    errors = []

    required_fields = {
        "tool_name": "Tool Name",
        "tool_link": "Tool Link",
        "category": "Category",
        "description": "Description",
        "free_tier": "Free Tier",
        "score": "Score",
        "tags": "Tags",
    }

    for key, label in required_fields.items():
        if not fields.get(key):
            errors.append(f"{label} is required")

    parsed_url = urlparse(str(tool.get("url") or ""))
    if fields.get("tool_link") and (
        parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc
    ):
        errors.append("Tool Link must be a valid http(s) URL")

    if fields.get("score") and tool.get("score") is None:
        errors.append("Score must be in format 'X/10' from 0/10 through 10/10")

    name_key = str(tool.get("name") or "").casefold()
    url_key = str(tool.get("url") or "").rstrip("/").casefold()
    existing_names = {str(existing.get("name", "")).casefold() for existing in existing_tools}
    existing_urls = {str(existing.get("url", "")).rstrip("/").casefold() for existing in existing_tools}

    if name_key and name_key in existing_names:
        errors.append("Tool Name already exists")

    if url_key and url_key in existing_urls:
        errors.append("Tool Link already exists")

    return errors


def main():
    token = os.environ.get("GITHUB_TOKEN")
    repo_name = os.environ.get("REPO_NAME")
    issue_number = os.environ.get("ISSUE_NUMBER")

    if not all([token, repo_name, issue_number]):
        print("Missing required environment variables")
        sys.exit(1)

    gh = Github(token)
    repo = gh.get_repo(repo_name)
    issue = repo.get_issue(int(issue_number))

    fields = parse_issue_body(issue.body)
    existing_tools = generate_readme.load_tools()
    new_tool = issue_fields_to_tool(fields)
    errors = validate_submission(fields, new_tool, existing_tools)

    if errors:
        error_msg = "**Failed to add tool. Please fix the following errors:**\n\n"
        error_msg += "\n".join(f"- {error}" for error in errors)
        issue.create_comment(error_msg)
        issue.edit(state="closed")
        print("Validation failed:", errors)
        sys.exit(1)

    tools = [*existing_tools, new_tool]
    all_errors = generate_readme.validate_tools(tools)
    if all_errors:
        issue.create_comment("**Failed to add tool because tools.json validation failed.**")
        print("tools.json validation failed:", all_errors)
        sys.exit(1)

    generate_readme.save_tools(tools)
    generate_readme.render_readme(tools)

    issue.create_comment(
        f"**Tool '{new_tool['name']}' has been added to tools.json!** The README has been regenerated."
    )
    issue.edit(state="closed")
    print(f"Successfully added {new_tool['name']}")


if __name__ == "__main__":
    main()
