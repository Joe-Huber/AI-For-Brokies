import os
import re
import sys
from github import Github

def parse_issue_body(body):
    fields = {}
    patterns = {
        'tool_name': r'### Tool Name\s+(.*?)(?=###|$)',
        'tool_link': r'### Tool Link\s+(.*?)(?=###|$)',
        'category': r'### Category\s+(.*?)(?=###|$)',
        'description': r'### Description\s+(.*?)(?=###|$)',
        'free_tier': r'### Free Tier\s+(.*?)(?=###|$)',
        'score': r'### Score\s+(.*?)(?=###|$)',
        'tags': r'### Tags\s+(.*?)(?=###|$)',
        'notes': r'### Notes\s+(.*?)(?=$)',
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, body, re.DOTALL)
        if match:
            value = match.group(1).strip()
            fields[key] = value if value else None
        else:
            fields[key] = None

    return fields

def validate_fields(fields):
    errors = []

    if not fields.get('tool_name'):
        errors.append("Tool Name is required")
    if not fields.get('tool_link'):
        errors.append("Tool Link is required")
    if not fields.get('category'):
        errors.append("Category is required")
    if not fields.get('description'):
        errors.append("Description is required")
    if not fields.get('free_tier'):
        errors.append("Free Tier is required")

    score = fields.get('score', '')
    if score:
        if not re.match(r'^\d{1,2}/10$', score):
            errors.append("Score must be in format 'X/10' (e.g., 5/10)")
    else:
        errors.append("Score is required")

    return errors

def format_tags(tags_str):
    if not tags_str:
        return '-'
    tags = [t.strip().strip('`') for t in tags_str.split() if t.strip()]
    return ' '.join(f'`{tag}`' for tag in tags)

def create_table_row(fields):
    name = fields['tool_name']
    link = fields['tool_link']
    category = fields['category']
    description = fields['description']
    free_tier = fields['free_tier']
    score = fields['score']
    tags = format_tags(fields.get('tags', ''))
    notes = fields.get('notes', '-') or '-'

    return f"| [{name}]({link}) | {category} | {description} | {free_tier} | {score} | {tags} | {notes} |"

def main():
    token = os.environ.get('GITHUB_TOKEN')
    repo_name = os.environ.get('REPO_NAME')
    issue_number = os.environ.get('ISSUE_NUMBER')

    if not all([token, repo_name, issue_number]):
        print("Missing required environment variables")
        sys.exit(1)

    gh = Github(token)
    repo = gh.get_repo(repo_name)
    issue = repo.get_issue(int(issue_number))

    fields = parse_issue_body(issue.body)
    errors = validate_fields(fields)

    if errors:
        error_msg = "**Failed to add tool. Please fix the following errors:**\n\n"
        error_msg += "\n".join(f"- {e}" for e in errors)
        issue.create_comment(error_msg)
        issue.edit(state='closed')
        print("Validation failed:", errors)
        sys.exit(1)

    new_row = create_table_row(fields)

    with open('README.md', 'r') as f:
        content = f.read()

    last_row_match = list(re.finditer(r'\| \[.*?\]\(.*?\) \| .*? \| .*? \| .*? \| .*? \| .*? \| .*? \|', content))
    if not last_row_match:
        print("Could not find table in README")
        sys.exit(1)

    last_row_end = last_row_match[-1].end()
    updated_content = content[:last_row_end] + '\n' + new_row + content[last_row_end:]

    with open('README.md', 'w') as f:
        f.write(updated_content)

    issue.create_comment(f"**Tool '{fields['tool_name']}' has been added to the list!** The README has been updated.")
    issue.edit(state='closed')
    print(f"Successfully added {fields['tool_name']}")

if __name__ == '__main__':
    main()
