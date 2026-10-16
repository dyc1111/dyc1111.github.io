#!/usr/bin/env python3
"""Render work-specific publication metadata into the static homepage."""

import json
from html import escape
from pathlib import Path
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
START = "      <!-- PUBLICATIONS:START -->"
END = "      <!-- PUBLICATIONS:END -->"


def asset_url(folder, filename):
    path = (folder / filename).resolve()
    if not path.is_relative_to(folder.resolve()) or not path.is_file():
        raise ValueError(f"Missing or invalid publication asset: {folder.name}/{filename}")
    return quote(path.relative_to(ROOT).as_posix())


def render_publication(folder, data):
    authors = []
    for author in data["authors"]:
        name = escape(author["name"])
        if author.get("marker"):
            name += f'<sup>{escape(author["marker"])}</sup>'
        if author.get("highlight"):
            name = f"<strong>{name}</strong>"
        if author.get("url"):
            url = author["url"]
            if urlsplit(url).scheme:
                if urlsplit(url).scheme not in {"http", "https"}:
                    raise ValueError(f"Invalid author URL: {author['name']}")
            elif not (ROOT / url).is_file():
                raise ValueError(f"Missing local author page: {url}")
            name = f'<a href="{escape(url, quote=True)}">{name}</a>'
        authors.append(name)

    teaser = asset_url(folder, data["teaser"])
    full_teaser = asset_url(folder, data.get("teaser_pdf", data["teaser"]))
    teaser_label = "View the full-size publication teaser"
    if data.get("teaser_pdf"):
        teaser_label += " (PDF)"
    size = data.get("teaser_size")
    dimensions = f' width="{int(size[0])}" height="{int(size[1])}"' if size else ""
    arxiv = data.get("arxiv_url")
    if arxiv:
        if urlsplit(arxiv).scheme != "https" or not urlsplit(arxiv).netloc:
            raise ValueError(f"arxiv_url must be a full HTTPS URL: {folder.name}")
        paper_link = f'<p><a href="{escape(arxiv, quote=True)}">arXiv</a></p>'
    else:
        paper_link = '<p class="placeholder">arXiv (link to be added)</p>'

    return f'''      <article class="publication">
        <a class="teaser-link" href="{full_teaser}" aria-label="{teaser_label}">
          <img class="teaser" src="{teaser}" alt="{escape(data['teaser_alt'], quote=True)}"{dimensions} loading="lazy">
        </a>
        <div class="publication-details">
          <h3>{escape(data['title'])}</h3>
          <p>{', '.join(authors)}.</p>
          <p><em>{escape(data['status'])}</em></p>
          {paper_link}
        </div>
      </article>'''


def main():
    entries = []
    for metadata in sorted((ROOT / "publications").glob("*/publication.json")):
        entries.append((metadata.parent, json.loads(metadata.read_text(encoding="utf-8"))))
    entries.sort(key=lambda entry: entry[1].get("order", 0))
    publications = "\n".join(render_publication(folder, data) for folder, data in entries)

    homepage = ROOT / "index.html"
    html = homepage.read_text(encoding="utf-8")
    if html.count(START) != 1 or html.count(END) != 1:
        raise ValueError("The homepage must contain exactly one pair of publication markers.")
    before, _, remaining = html.partition(START)
    _, _, after = remaining.partition(END)
    updated = f"{before}{START}\n{publications}\n{END}{after}"
    if updated != html:
        homepage.write_text(updated, encoding="utf-8")
    print(f"Rendered {len(entries)} publication(s) into index.html.")


if __name__ == "__main__":
    main()
