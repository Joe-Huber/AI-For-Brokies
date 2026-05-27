import json
from pathlib import Path
from urllib.parse import urlparse

ROOT_DIR = Path(__file__).resolve().parents[1]
README_PATH = ROOT_DIR / "README.md"
TOOLS_PATH = ROOT_DIR / "tools.json"
TOOLS_HEADING = "## My Top Free Tools 💜"
TOOLS_TABLE_PREFIX = "\n\n\n\n"
TOOLS_NOTE = "Tool data lives in [tools.json](tools.json). Tag descriptions are in [tags.md](tags.md). Run `python scripts/generate_readme.py` after editing tools.json."

REQUIRED_FIELDS = (
    "name",
    "url",
    "category",
    "description",
    "free_tier",
    "score",
    "tags",
    "notes",
)


def load_tools(path=TOOLS_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tools(tools, path=TOOLS_PATH):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tools, f, indent=2)
        f.write("\n")


def validate_tool(tool, index=None):
    label = f"Tool #{index + 1}" if index is not None else "Tool"
    errors = []

    for field in REQUIRED_FIELDS:
        value = tool.get(field)
        if value is None or value == "" or value == []:
            errors.append(f"{label}: {field} is required")

    parsed_url = urlparse(str(tool.get("url", "")))
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        errors.append(f"{label}: url must be a valid http(s) URL")

    score = tool.get("score")
    if not isinstance(score, int) or score < 0 or score > 10:
        errors.append(f"{label}: score must be an integer from 0 to 10")

    tags = tool.get("tags")
    if not isinstance(tags, list) or not all(isinstance(tag, str) and tag.strip() for tag in tags):
        errors.append(f"{label}: tags must be a non-empty list of strings")

    return errors


def validate_tools(tools):
    errors = []
    seen_names = {}
    seen_urls = {}

    if not isinstance(tools, list):
        return ["tools.json must contain a list of tools"]

    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            errors.append(f"Tool #{index + 1}: must be an object")
            continue

        errors.extend(validate_tool(tool, index))

        name_key = str(tool.get("name", "")).casefold()
        url_key = str(tool.get("url", "")).rstrip("/").casefold()

        if name_key:
            if name_key in seen_names:
                errors.append(f"Tool #{index + 1}: duplicate name also used by tool #{seen_names[name_key] + 1}")
            else:
                seen_names[name_key] = index

        if url_key:
            if url_key in seen_urls:
                errors.append(f"Tool #{index + 1}: duplicate url also used by tool #{seen_urls[url_key] + 1}")
            else:
                seen_urls[url_key] = index

    return errors


def markdown_cell(value):
    return str(value).strip().replace("\n", "<br>").replace("|", "\\|")


def format_tags(tags):
    return " ".join(f"`{markdown_cell(tag)}`" for tag in tags) if tags else "-"


def tool_to_row(tool):
    return [
        f"[{markdown_cell(tool['name'])}]({markdown_cell(tool['url'])})",
        markdown_cell(tool["category"]),
        markdown_cell(tool["description"]),
        markdown_cell(tool["free_tier"]),
        f"{tool['score']}/10",
        format_tags(tool["tags"]),
        markdown_cell(tool.get("notes") or "-"),
    ]


def render_tools_table(tools):
    headers = ["Tool", "Category", "Description", "Free tier", "Score", "Tags", "Notes"]
    rows = [tool_to_row(tool) for tool in tools]
    widths = [len(header) for header in headers]

    for row in rows:
        widths = [max(width, len(cell)) for width, cell in zip(widths, row)]

    header = "| " + " | ".join(header.ljust(width) for header, width in zip(headers, widths)) + " |"
    separator_cells = []
    for header_name, width in zip(headers, widths):
        marker = "-" * (width + 2)
        separator_cells.append(marker[:-1] + ":" if header_name == "Score" else marker)
    separator = "|" + "|".join(separator_cells) + "|"

    rendered_rows = []
    for row in rows:
        cells = []
        for header_name, cell, width in zip(headers, row, widths):
            cells.append(cell.rjust(width) if header_name == "Score" else cell.ljust(width))
        rendered_rows.append("| " + " | ".join(cells) + " |")

    return "\n".join([header, separator, *rendered_rows])


def render_readme(tools, readme_path=README_PATH):
    errors = validate_tools(tools)
    if errors:
        raise ValueError("\n".join(errors))

    readme = readme_path.read_text(encoding="utf-8")
    prefix, separator, _ = readme.partition(TOOLS_HEADING)

    if not separator:
        raise ValueError(f"Could not find {TOOLS_HEADING!r} section in README.md")

    table = render_tools_table(tools)
    new_content = f"{prefix}{TOOLS_HEADING}{TOOLS_TABLE_PREFIX}{table}\n\n{TOOLS_NOTE}\n"
    readme_path.write_text(new_content, encoding="utf-8")


def main():
    tools = load_tools()
    render_readme(tools)


if __name__ == "__main__":
    main()
