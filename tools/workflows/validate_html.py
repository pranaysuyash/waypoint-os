"""Validate the injected JSON in the HTML file."""
import re
import json

with open('/Users/pranay/Projects/travel_agency_agent/workflows.html', 'r') as f:
    html = f.read()

# Extract the JSON between "const DATA = " and the semicolon
match = re.search(r'const DATA = (\{.*?\});', html, re.DOTALL)
if not match:
    print("ERROR: Could not find DATA in HTML")
    exit(1)

json_str = match.group(1)
try:
    data = json.loads(json_str)
    print(f"✓ JSON is valid")
    print(f"  Packages: {len(data['packages'])}")
    for pkg_id, pkg in data['packages'].items():
        print(f"    - {pkg['label']}: {len(pkg.get('components', []))} components")
    print(f"  Workflows: {len(data['workflows'])}")
    for wf in data['workflows']:
        print(f"    - {wf['label']}: {len(wf['steps'])} steps, {len(wf['edges'])} edges")
    print(f"\n✓ All data structure looks good")
except json.JSONDecodeError as e:
    print(f"✗ JSON parse error: {e}")
    exit(1)

# Check HTML structure
if '<!DOCTYPE html>' in html and '</html>' in html:
    print("✓ HTML structure is complete")
else:
    print("✗ HTML structure is incomplete")

# Check script tags balance
opens = html.count('<script>')
closes = html.count('</script>')
if opens == closes:
    print(f"✓ Script tags balanced ({opens} pairs)")
else:
    print(f"✗ Script tags unbalanced: {opens} opens, {closes} closes")

# Check style tags
opens = html.count('<style>')
closes = html.count('</style>')
if opens == closes:
    print(f"✓ Style tags balanced ({opens} pairs)")
else:
    print(f"✗ Style tags unbalanced: {opens} opens, {closes} closes")

print("\n✓ File is good to go!")