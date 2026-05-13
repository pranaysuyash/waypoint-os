import os

MAIN_ID = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"

# Find all test .py files with the main agency ID
test_dir = "tests"
for root, dirs, files in os.walk(test_dir):
    for fname in files:
        if not fname.endswith(".py"):
            continue
        fpath = os.path.join(root, fname)
        with open(fpath, "r") as f:
            content = f.read()

        if MAIN_ID not in content:
            continue

        # Track if we made changes
        orig = content

        # Skip conftest.py comment references
        if "conftest.py" not in fpath:
            # Replace string-form agency_id in dicts
            content = content.replace('"' + MAIN_ID + '"', "TEST_AGENCY_ID")
            content = content.replace("'" + MAIN_ID + "'", "TEST_AGENCY_ID")
            content = content.replace('agency_id="' + MAIN_ID + '"', "agency_id=TEST_AGENCY_ID")
            content = content.replace("agency_id='" + MAIN_ID + "'", "agency_id=TEST_AGENCY_ID")
            content = content.replace('AGENCY_ID = "' + MAIN_ID + '"', "AGENCY_ID = TEST_AGENCY_ID")
            content = content.replace('== "' + MAIN_ID + '"', "== TEST_AGENCY_ID")

            # Ensure import of TEST_AGENCY_ID
            if "TEST_AGENCY_ID" in content and "from spine_api.persistence import" in content:
                # Check if TEST_AGENCY_ID is already in the import
                for line in content.split("\n"):
                    if "from spine_api.persistence import" in line and "TEST_AGENCY_ID" in line:
                        break
                else:
                    # Add TEST_AGENCY_ID to existing import
                    content = content.replace(
                        "from spine_api.persistence import TripStore",
                        "from spine_api.persistence import TripStore, TEST_AGENCY_ID"
                    )

        if content != orig:
            with open(fpath, "w") as f:
                f.write(content)
            print(f"Updated: {fpath}")

# Now handle conftest - add the guard test at end
with open("tests/conftest.py", "r") as f:
    content = f.read()

guard_test = """
# ---------------------------------------------------------------------------
# Hardcoded agency ID guard test
# ---------------------------------------------------------------------------
# This test ensures that no test code accidentally writes to the main
# agency. If this test fails, search for hardcoded
# d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b in test files.

def test_no_hardcoded_main_agency_in_test_source():
    \"\"\"Fail if any .py file under tests/ contains hardcoded main agency ID.\"\"\"
    import os
    import re

    main_id = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"
    violations = []

    for root, dirs, files in os.walk("tests"):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            with open(fpath) as f:
                for i, line in enumerate(f, 1):
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    if main_id in line:
                        # Allow the env var line in conftest
                        if os.path.basename(fpath) == "conftest.py" and "PUBLIC_CHECKER_AGENCY_ID" in line:
                            continue
                        # Allow import of TEST_AGENCY_ID
                        if "TEST_AGENCY_ID" in line:
                            continue
                        violations.append(f"{fpath}:{i}: {line.rstrip()}")

    assert not violations, (
        f"Hardcoded main agency ID found in {len(violations)} location(s):\\n"
        + "\\n".join(violations)
    )
"""

if "# Hardcoded agency ID guard test" not in content:
    content = content.rstrip() + "\n" + guard_test
    with open("tests/conftest.py", "w") as f:
        f.write(content)
    print("Added guard test to conftest.py")
else:
    print("Guard test already exists in conftest.py")