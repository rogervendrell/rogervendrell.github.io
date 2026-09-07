#!/usr/bin/env python3
"""Generate projects/index.html from each project's summary/info.yml.

Usage:
    python3 scripts/generate_projects_index.py

See projects/SUMMARY_SCHEMA.md for the summary/info.yml format, and
scripts/README.md for setup instructions. Every project directory under
projects/ that contains a summary/info.yml is picked up automatically;
projects without one are skipped, and directories starting with "." or "_"
are ignored entirely.
"""
from __future__ import annotations

import html
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit(
        "Missing dependency: PyYAML.\n"
        "Install it with: pip install -r scripts/requirements.txt"
    )

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = REPO_ROOT / "projects"
OUTPUT_FILE = PROJECTS_DIR / "index.html"

REQUIRED_FIELDS = [
    "title",
    "year",
    "short_description",
    "thumbnail",
    "thumbnail_alt",
    "collaborators",
]


@dataclass
class Link:
    label: str
    url: str
    icon: str = "fas fa-link"


@dataclass
class Collaborator:
    name: str
    url: str | None = None


@dataclass
class Project:
    slug: str
    title: str
    year: int
    short_description: str
    thumbnail_url: str
    thumbnail_alt: str
    collaborators: list[Collaborator]
    tags: list[str] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    page_url: str = "index.html"


def is_external(url: str) -> bool:
    return url.startswith(("http://", "https://", "mailto:"))


def resolve(slug: str, url: str) -> str:
    """Resolve a URL from a project's info.yml relative to projects/index.html."""
    return url if is_external(url) else f"{slug}/{url}"


def load_project(project_dir: Path) -> Project | None:
    info_path = project_dir / "summary" / "info.yml"
    if not info_path.is_file():
        return None

    data = yaml.safe_load(info_path.read_text(encoding="utf-8")) or {}
    slug = project_dir.name

    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        raise ValueError(
            f"projects/{slug}/summary/info.yml is missing required field(s): "
            f"{', '.join(missing)}"
        )

    thumbnail_file = project_dir / "summary" / data["thumbnail"]
    if not thumbnail_file.is_file():
        raise ValueError(
            f"projects/{slug}/summary/info.yml points at thumbnail "
            f"'{data['thumbnail']}', which does not exist at {thumbnail_file}"
        )

    collaborators = [
        Collaborator(name=c["name"], url=c.get("url"))
        for c in data["collaborators"]
    ]
    links = [
        Link(label=l["label"], url=resolve(slug, l["url"]), icon=l.get("icon", "fas fa-link"))
        for l in data.get("links", [])
    ]

    return Project(
        slug=slug,
        title=data["title"],
        year=int(data["year"]),
        short_description=data["short_description"].strip(),
        thumbnail_url=f"{slug}/summary/{data['thumbnail']}",
        thumbnail_alt=data["thumbnail_alt"].strip(),
        collaborators=collaborators,
        tags=data.get("tags", []),
        links=links,
        page_url=f"{slug}/{data.get('page', 'index.html')}",
    )


def discover_projects() -> list[Project]:
    projects = []
    for entry in sorted(PROJECTS_DIR.iterdir()):
        if not entry.is_dir() or entry.name.startswith((".", "_")):
            continue
        project = load_project(entry)
        if project is not None:
            projects.append(project)
    # Reverse-chronological by year, then alphabetical by title as a tiebreaker.
    projects.sort(key=lambda p: (-p.year, p.title.lower()))
    return projects


def render_collaborators(collaborators: list[Collaborator]) -> str:
    parts = []
    for c in collaborators:
        name = html.escape(c.name)
        if c.url:
            parts.append(
                f'<span class="author-block"><a href="{html.escape(c.url)}" '
                f'target="_blank" rel="noopener noreferrer">{name}</a></span>'
            )
        else:
            parts.append(f'<span class="author-block">{name}</span>')
    return ",\n              ".join(parts)


def render_tags(tags: list[str]) -> str:
    if not tags:
        return ""
    pills = "\n".join(f'<span class="tag-pill">{html.escape(t)}</span>' for t in tags)
    return f'<div class="tag-pills">\n{pills}\n</div>'


def render_links(links: list[Link]) -> str:
    if not links:
        return ""
    buttons = "\n".join(
        f'''<span class="link-block">
            <a href="{html.escape(l.url)}" target="_blank" rel="noopener noreferrer"
               class="external-link button is-small is-rounded is-dark">
              <span class="icon"><i class="{html.escape(l.icon)}"></i></span>
              <span>{html.escape(l.label)}</span>
            </a>
          </span>'''
        for l in links
    )
    return f'<div class="project-links">\n{buttons}\n</div>'


def render_project(project: Project) -> str:
    return f'''
    <div class="project-entry">
      <div class="project-thumb">
        <a href="{html.escape(project.page_url)}">
          <img src="{html.escape(project.thumbnail_url)}" alt="{html.escape(project.thumbnail_alt)}">
        </a>
      </div>
      <div class="project-text">
        <h3 class="title is-4"><a href="{html.escape(project.page_url)}">{html.escape(project.title)}</a></h3>
        <div class="is-size-6 publication-authors">
              {render_collaborators(project.collaborators)}
        </div>
        <p class="project-description">{html.escape(project.short_description)}</p>
        {render_tags(project.tags)}
        {render_links(project.links)}
      </div>
    </div>'''


PAGE_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="description" content="Projects by Roger Vendrell Colet.">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Projects - Roger Vendrell Colet</title>

  <link href="https://fonts.googleapis.com/css?family=Google+Sans|Noto+Sans|Castoro"
        rel="stylesheet">

  <link rel="stylesheet" href="./static/css/bulma.min.css">
  <link rel="stylesheet" href="./static/css/fontawesome.all.min.css">
  <link rel="stylesheet" href="./static/css/index.css">

  <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
  <script defer src="./static/js/fontawesome.all.min.js"></script>
  <script src="./static/js/index.js"></script>
</head>
<body>
<!-- This page is generated from each project's summary/info.yml by
     scripts/generate_projects_index.py -- see projects/SUMMARY_SCHEMA.md.
     Edit the info.yml files (or the template below) and re-run the script
     rather than hand-editing the project list. -->

<nav class="navbar" role="navigation" aria-label="main navigation">
  <div class="navbar-brand">
    <a role="button" class="navbar-burger" aria-label="menu" aria-expanded="false">
      <span aria-hidden="true"></span>
      <span aria-hidden="true"></span>
      <span aria-hidden="true"></span>
    </a>
  </div>
  <div class="navbar-menu">
    <div class="navbar-start" style="flex-grow: 1; justify-content: center;">
      <a class="navbar-item" href="../index.html">
        <span class="icon"><i class="fas fa-home"></i></span>
      </a>
    </div>
  </div>
</nav>

<section class="hero about-me">
  <div class="hero-body">
    <div class="container is-max-desktop">
      <div class="columns is-vcentered">
        <div class="column is-two-thirds">
          <h1 class="title is-1 publication-title">Roger Vendrell Colet</h1>
          <!-- TODO: replace this placeholder bio with your own. -->
          <div class="content about-bio">
            <p>
              Add a short bio here: who you are, what you work on, and what ties these
              projects together. A couple of sentences is plenty.
            </p>
          </div>
          <div class="about-links">
            <!-- TODO: add/remove contact links as needed. -->
            <a href="https://www.linkedin.com/in/roger-vendrell-colet/" target="_blank" rel="noopener noreferrer">LinkedIn</a>
            /
            <a href="https://github.com/rogervendrell" target="_blank" rel="noopener noreferrer">GitHub</a>
            /
            <a href="mailto:rogervendrell7@gmail.com">Email</a>
          </div>
        </div>
        <div class="column is-one-third has-text-centered">
          <!-- TODO: replace with a real photo, e.g. static/img/profile.jpg -->
          <div class="about-photo-placeholder">
            <span>RVC</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="container is-max-desktop">
    <h2 class="title is-3">Projects</h2>
    <div class="project-list">
{project_entries}
    </div>
  </div>
</section>

<footer class="footer">
  <div class="container">
    <div class="columns is-centered">
      <div class="column is-8">
        <div class="content has-text-centered">
          <p>
            The project pages themselves are adapted from the
            <a href="https://nerfies.github.io">Nerfies project page</a>, licensed
            under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative
            Commons Attribution-ShareAlike 4.0 International License</a>. This homepage's
            layout is inspired by
            <a href="https://pratulsrinivasan.github.io/" target="_blank" rel="noopener noreferrer">pratulsrinivasan.github.io</a>.
          </p>
        </div>
      </div>
    </div>
  </div>
</footer>

</body>
</html>
"""


def main() -> None:
    projects = discover_projects()
    if not projects:
        print("No projects with a summary/info.yml were found under projects/.", file=sys.stderr)

    entries_html = "\n".join(render_project(p) for p in projects)
    OUTPUT_FILE.write_text(PAGE_TEMPLATE.format(project_entries=entries_html), encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE.relative_to(REPO_ROOT)} with {len(projects)} project(s):")
    for p in projects:
        print(f"  - {p.year}  {p.title}  ({p.slug})")


if __name__ == "__main__":
    main()
