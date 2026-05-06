import argparse
import re
import ssl
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import generate_readme

DEFAULT_TIMEOUT = 15
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^)\s]+)\)")
URL_RE = re.compile(r"https?://[^\s<>)]+")
USER_AGENT = "AI-For-Brokies link checker"
WARNING_STATUSES = {403, 429}


@dataclass
class LinkResult:
    label: str
    url: str
    status: str
    ok: bool
    warning: bool = False


def extract_links(tools):
    links = []
    seen = set()

    def add_link(label, url):
        key = url.rstrip("/")
        if key in seen:
            return
        seen.add(key)
        links.append((label, url))

    for tool in tools:
        name = tool.get("name", "Unknown tool")
        url = tool.get("url")
        if url:
            add_link(f"{name} homepage", url)

        for field in ("free_tier", "notes"):
            value = str(tool.get(field) or "")
            field_label = field.replace("_", " ")
            for match in MARKDOWN_LINK_RE.finditer(value):
                add_link(f"{name} {field_label}", match.group(1))
            for match in URL_RE.finditer(value):
                add_link(f"{name} {field_label}", match.group(0))

    return links


def check_url(label, url, timeout):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return LinkResult(label, url, "invalid URL", False)

    for method in ("HEAD", "GET"):
        request = Request(url, method=method, headers={"User-Agent": USER_AGENT})
        try:
            context = ssl.create_default_context()
            with urlopen(request, timeout=timeout, context=context) as response:
                status_code = response.getcode()
                status = f"HTTP {status_code}"
                warning = status_code in WARNING_STATUSES
                ok = status_code < 400 or warning
                return LinkResult(label, url, status, ok, warning)
        except HTTPError as error:
            if method == "HEAD" and error.code in {405, 501}:
                continue
            status = f"HTTP {error.code}"
            warning = error.code in WARNING_STATUSES
            return LinkResult(label, url, status, warning, warning)
        except URLError as error:
            if method == "HEAD":
                continue
            return LinkResult(label, url, str(error.reason), False)
        except TimeoutError:
            if method == "HEAD":
                continue
            return LinkResult(label, url, "timed out", False)

    return LinkResult(label, url, "unreachable", False)


def print_results(results):
    failed = [result for result in results if not result.ok]
    warnings = [result for result in results if result.warning]

    for result in results:
        marker = "WARN" if result.warning else "OK" if result.ok else "FAIL"
        print(f"[{marker}] {result.label}: {result.url} ({result.status})")

    print()
    print(f"Checked {len(results)} links: {len(failed)} failed, {len(warnings)} warnings")

    return failed


def main():
    parser = argparse.ArgumentParser(description="Check links referenced by tools.json.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Timeout per request in seconds.")
    parser.add_argument("--limit", type=int, help="Only check the first N unique links.")
    parser.add_argument("--list", action="store_true", help="List links without checking them.")
    args = parser.parse_args()

    tools = generate_readme.load_tools()
    links = extract_links(tools)
    if args.limit:
        links = links[: args.limit]

    if args.list:
        for label, url in links:
            print(f"{label}: {url}")
        print()
        print(f"Found {len(links)} unique links")
        return

    results = [check_url(label, url, args.timeout) for label, url in links]
    failed = print_results(results)

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
