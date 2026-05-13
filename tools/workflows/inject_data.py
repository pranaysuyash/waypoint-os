"""Inject workflow JSON data into the HTML template.

Replaces the `const DATA = {...};` line in workflows.html with fresh data
from data/workflows.json, enabling a rebuild-when-JSON-changes workflow.

Strategy: find the line starting with `const DATA = `, replace the entire line.
No regex needed — the JSON is always on a single line.
"""
import json
import sys

JSON_PATH = '/Users/pranay/Projects/travel_agency_agent/data/workflows.json'
HTML_PATH = '/Users/pranay/Projects/travel_agency_agent/workflows.html'

def main():
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)

    with open(HTML_PATH, 'r') as f:
        html = f.read()

    # Split into lines and find the DATA line
    lines = html.split('\n')
    data_line_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('const DATA ='):
            data_line_idx = i
            break

    if data_line_idx is None:
        print("ERROR: Could not find 'const DATA = ...' line in HTML")
        sys.exit(1)

    # Build new line
    json_str = json.dumps(data, separators=(',', ':'))
    new_line = f"const DATA = {json_str};"

    # Replace
    old_line = lines[data_line_idx]
    lines[data_line_idx] = new_line
    html = '\n'.join(lines)

    with open(HTML_PATH, 'w') as f:
        f.write(html)

    print(f"✓ Injected {len(json_str):,} bytes of JSON into HTML (line {data_line_idx + 1})")
    print(f"✓ Total HTML size: {len(html):,} bytes")
    print(f"  Packages: {len(data['packages'])}")
    print(f"  Workflows: {len(data['workflows'])}")
    total_steps = sum(len(wf['steps']) for wf in data['workflows'])
    total_edges = sum(len(wf['edges']) for wf in data['workflows'])
    print(f"  Steps: {total_steps} across all workflows")
    print(f"  Edges: {total_edges} across all workflows")

if __name__ == '__main__':
    main()
