# Contributing

Thanks for helping make AI For Brokies better! This is a curated directory of free AI coding tools. Contributions of all kinds are welcome.

## Adding a New Tool

The easiest way to suggest a tool is to [open a new issue](https://github.com/Joe-Huber/AI-For-Brokies/issues/new?title=%5BAUTO%20NEW%20TOOL%5D&body=%23%23%23%20Tool%20Name%0A%0A%23%23%23%20Tool%20Link%0A%0A%23%23%23%20Category%0A%0A%23%23%23%20Description%0A%0A%23%23%23%20Free%20Tier%0A%0A%23%23%23%20Score%0A%0A%23%23%23%20Tags%0A%0A%23%23%23%20Notes&labels=New%20AI%20Tool) using the **Add a Tool** template. Fill in these fields:

- **Tool Name** – Name of the tool
- **Tool Link** – URL to the tool's homepage
- **Category** – e.g. `IDE`, `IDE Extension`, `Terminal App`, `API`, `Model's App`
- **Description** – One-line summary of what the tool does
- **Free Tier** – What's available at no cost
- **Score** – Rating out of 10 (e.g. `7/10`)
- **Tags** – Space-separated tags like `IDE-Extension` `Open-Source` `Terminal-App`
- **Notes** – Optional details, student offers, or caveats

Once submitted, a maintainer will review it. If approved, a bot commits the change automatically.

For an example, see [example_issue.md](example_issue.md).

## Editing Directly

You can also edit [tools.json](tools.json) by hand and regenerate the README:

```bash
python scripts/generate_readme.py
```

All tools must pass validation checks (run by CI on every PR):

- All fields are required (notes can be `-`)
- `url` must be a valid http(s) URL
- `score` must be an integer between 0–10
- `tags` must be a non-empty list of strings
- Names and URLs must be unique

## Running Validation & Link Checks Locally

```bash
# Validate tools.json and verify README matches
python scripts/generate_readme.py
git diff --exit-code README.md

# Check all tool links are reachable
python scripts/check_links.py
```

## Pull Requests

If you'd like to improve the project scripts, workflows, or this directory itself:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the validation scripts above
5. Open a pull request against `main`

The CI workflow will run validations automatically.

## Code of Conduct

Please be respectful and constructive. This is a small project — treat others the way you'd like to be treated. 💜
