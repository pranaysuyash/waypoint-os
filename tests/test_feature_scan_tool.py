import json
import subprocess
from pathlib import Path


def test_feature_scan_uses_current_scan_date_and_all_file_globs(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "a.py").write_text("alpha_signal = True\n")
    (project / "b.py").write_text("beta_signal = True\n")

    catalog = tmp_path / "catalog.json"
    catalog.write_text(
        json.dumps(
            {
                "project": "fixture_project",
                "baseline_score": 0,
                "baseline_max": 1,
                "features": [
                    {
                        "id": "X",
                        "name": "Scanner Quality",
                        "priority": "P0",
                        "baseline_score": 0,
                        "baseline_max": 1,
                        "sub_features": [
                            {
                                "id": "X1",
                                "name": "Multi glob evidence",
                                "evidence": {
                                    "files": ["a.py", "b.py"],
                                    "min_search_terms": ["alpha_signal", "beta_signal"],
                                },
                            }
                        ],
                    }
                ],
            }
        )
    )

    result = subprocess.run(
        [
            "python3",
            "tools/feature_scan.py",
            str(project),
            "--catalog",
            str(catalog),
            "--json",
            "--scan-date",
            "2026-05-11",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)

    assert payload["scanned_at"] == "2026-05-11"
    sub = payload["features"][0]["subs"][0]
    assert sub["status"] == "done"
    assert sub["matched_terms"] == ["alpha_signal", "beta_signal"]
