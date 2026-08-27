"""Assemble the synced markdown mirror into an MkDocs docs_dir.

Source layout (kept by the private-repo sync):
  README.md / README.es.md
  CHANGELOG.md
  docs/*.md / docs/*.es.md
  apps/<app>/README.md / apps/<app>/README.es.md

Target layout (generated, gitignored):
  site_docs/index.md
  site_docs/changelog.md
  site_docs/infrastructure/...
  site_docs/apps/<app>/index.md
"""

from __future__ import annotations

import re
import shutil
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DOCS = ROOT / "docs"
SOURCE_APPS = ROOT / "apps"
OUTPUT = ROOT / "site_docs"

APPS = (
    "core",
    "user_levels",
    "users",
    "main",
    "training",
    "challenge",
    "communication",
    "boards",
    "landing",
    "links",
    "streaming",
    "pricing",
    "keyboard_api",
)

INFRA_FILES = (
    "docker",
    "backups",
    "user-levels-cache",
)

# Paths that exist only in the private origin repo (not in this docs mirror).
_PRIVATE_ONLY = re.compile(
    r"\[([^\]]*)\]\(((?:\./|\.\./)*)((?:scripts|\.github)/[^)]+)\)"
)

_LINK_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    # Root-relative app / docs / changelog links
    (
        re.compile(r"\((\./)?apps/([^/]+)/README(?:\.es)?\.md(#.*?)?\)"),
        r"(apps/\2/index.md\3)",
    ),
    (
        re.compile(r"\((\./)?docs/README(?:\.es)?\.md(#.*?)?\)"),
        r"(infrastructure/index.md\2)",
    ),
    (
        re.compile(r"\((\./)?docs/([^)#]+?)(?:\.es)?\.md(#.*?)?\)"),
        r"(infrastructure/\2.md\3)",
    ),
    (
        re.compile(r"\((\./)?CHANGELOG(?:\.es)?\.md(#.*?)?\)"),
        r"(changelog.md\2)",
    ),
    # Keep original ../ depth when rewriting (apps/X → ../../docs/... needs ../../infrastructure/)
    (
        re.compile(r"\(((?:\.\./)+)README(?:\.es)?\.md(#.*?)?\)"),
        r"(\1index.md\2)",
    ),
    (
        re.compile(r"\(((?:\.\./)+)docs/README(?:\.es)?\.md(#.*?)?\)"),
        r"(\1infrastructure/index.md\2)",
    ),
    (
        re.compile(r"\(((?:\.\./)+)docs/([^)#]+?)(?:\.es)?\.md(#.*?)?\)"),
        r"(\1infrastructure/\2.md\3)",
    ),
    (
        re.compile(r"\(((?:\.\./)+)apps/([^/]+)/README(?:\.es)?\.md(#.*?)?\)"),
        r"(\1apps/\2/index.md\3)",
    ),
    (
        re.compile(r"\(\.\./([^/]+)/README(?:\.es)?\.md(#.*?)?\)"),
        r"(../\1/index.md\2)",
    ),
    # Sibling locale files inside the same folder (docker.es.md → docker.md)
    (
        re.compile(r"\(([^/\s)\[\]]+)(?:\.es)\.md(#.*?)?\)"),
        r"(\1.md\2)",
    ),
)


def neutralize_private_links(content: str) -> str:
    """Turn links to private-repo paths into inline code (no broken site links)."""
    return _PRIVATE_ONLY.sub(r"`\3`", content)


def ascii_slug_fragment(fragment: str) -> str:
    """Match Material/MkDocs heading ids (accents stripped)."""
    normalized = unicodedata.normalize("NFKD", fragment)
    return normalized.encode("ascii", "ignore").decode("ascii")


def normalize_anchor_links(content: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return f"](#{ascii_slug_fragment(match.group(1))})"

    return re.sub(r"\]\(#([^)]+)\)", replace, content)


def rewrite_links(content: str) -> str:
    content = neutralize_private_links(content)
    for pattern, replacement in _LINK_RULES:
        content = pattern.sub(replacement, content)
    return normalize_anchor_links(content)


def write_page(source: Path, destination: Path) -> None:
    if not source.is_file():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = source.read_text(encoding="utf-8")
    destination.write_text(rewrite_links(text), encoding="utf-8", newline="\n")


def assemble() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)

    write_page(ROOT / "README.md", OUTPUT / "index.md")
    write_page(ROOT / "README.es.md", OUTPUT / "index.es.md")
    write_page(ROOT / "CHANGELOG.md", OUTPUT / "changelog.md")

    write_page(SOURCE_DOCS / "README.md", OUTPUT / "infrastructure" / "index.md")
    write_page(SOURCE_DOCS / "README.es.md", OUTPUT / "infrastructure" / "index.es.md")
    for name in INFRA_FILES:
        write_page(SOURCE_DOCS / f"{name}.md", OUTPUT / "infrastructure" / f"{name}.md")
        write_page(
            SOURCE_DOCS / f"{name}.es.md",
            OUTPUT / "infrastructure" / f"{name}.es.md",
        )

    for app in APPS:
        app_dir = SOURCE_APPS / app
        write_page(app_dir / "README.md", OUTPUT / "apps" / app / "index.md")
        write_page(app_dir / "README.es.md", OUTPUT / "apps" / app / "index.es.md")

    page_count = sum(1 for path in OUTPUT.rglob("*.md") if path.is_file())
    print(f"Assembled {page_count} pages into {OUTPUT.relative_to(ROOT)}/")


def main() -> int:
    assemble()
    return 0


if __name__ == "__main__":
    sys.exit(main())
