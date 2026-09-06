"""Static regression contracts for the production container boundaries.

These checks do not replace a Docker build, image inspection, or vulnerability
scan. They prevent the repository from silently regressing the source-level
controls that can be verified without a Docker daemon: immutable base-image
references, non-root runtime identities, and build-context exclusions.
"""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DOCKERFILES = (
    ROOT / "Dockerfile",
    ROOT / "Dockerfile.spine_api",
    ROOT / "Dockerfile.frontend",
    ROOT / "frontend" / "Dockerfile",
)


def test_all_production_dockerfiles_pin_every_base_image_to_a_digest() -> None:
    """A mutable tag must not be able to change the runtime underneath a lock."""

    for dockerfile in DOCKERFILES:
        lines = dockerfile.read_text(encoding="utf-8").splitlines()
        stages = {
            match.group(1)
            for line in lines
            if (match := re.match(r"\s*FROM\s+\S+\s+AS\s+(\S+)", line, re.IGNORECASE))
        }
        from_lines = [
            line.strip()
            for line in lines
            if line.strip().upper().startswith("FROM ")
            and line.strip().split()[1].lower() not in {stage.lower() for stage in stages}
        ]
        assert from_lines, dockerfile
        assert all("@sha256:" in line for line in from_lines), (dockerfile, from_lines)


def test_runtime_stages_drop_root_and_copy_as_runtime_identity() -> None:
    """Runtime stages must use an explicit non-root identity and owned layers."""

    expectations = {
        ROOT / "Dockerfile": "USER appuser:appuser",
        ROOT / "Dockerfile.spine_api": "USER appuser:appuser",
        ROOT / "Dockerfile.frontend": "USER nextjs:nodejs",
        ROOT / "frontend" / "Dockerfile": "USER nextjs:nodejs",
    }
    for dockerfile, user_line in expectations.items():
        text = dockerfile.read_text(encoding="utf-8")
        assert user_line in text, dockerfile
        assert "STOPSIGNAL SIGTERM" in text, dockerfile
        assert "--chown=" in text, dockerfile
        if "nextjs:nodejs" in user_line:
            assert "COPY --from=builder --chown=nextjs:nodejs /app/public" in text


def test_api_dependency_stages_use_the_frozen_lock_without_packaging_source() -> None:
    """The dependency layer must be independent from optional source/docs files."""

    for dockerfile in (ROOT / "Dockerfile", ROOT / "Dockerfile.spine_api"):
        text = dockerfile.read_text(encoding="utf-8")
        assert "uv sync --frozen --no-dev --no-install-project" in text


def test_root_context_excludes_secrets_and_runtime_state_but_keeps_static_inputs() -> None:
    """Docker context policy must exclude local state independently of Git."""

    text = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    required = (
        ".env",
        ".env.*",
        "**/.env",
        "**/.env.*",
        "*.pem",
        "*.key",
        "data/*",
        "data/runs/",
        "data/documents/",
        "data/audit/",
        "data/trips/",
        "data/drafts/",
        "data/memory/",
        "data/proposals/",
        "data/fixtures/",
        "data/evals/",
    )
    assert all(pattern in text.splitlines() for pattern in required)
    assert "!data/cities.json" in text.splitlines()
    assert "!data/cities5000.txt" in text.splitlines()
    assert "!data/config/seasonal_campaigns.json" in text.splitlines()
    assert "!.env.example" not in text.splitlines()


def test_frontend_context_excludes_dotenv_and_local_build_state() -> None:
    """The nested frontend build context needs its own ignore policy."""

    text = (ROOT / "frontend" / ".dockerignore").read_text(encoding="utf-8")
    lines = text.splitlines()
    for pattern in (".env", ".env.*", "*.pem", "*.key", "node_modules/", ".next/"):
        assert pattern in lines


def test_compose_service_images_are_digest_pinned_and_internal_state_is_not_published() -> None:
    """Compose's stateful dependencies must be reproducible and mesh-only."""

    text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert re.search(r"image:\s+redis:7\.4-alpine@sha256:[0-9a-f]{64}", text)
    assert re.search(r"image:\s+postgres:16-alpine@sha256:[0-9a-f]{64}", text)
    assert '"5432:5432"' not in text
    assert '"6379:6379"' not in text
