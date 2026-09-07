# scripts/

## `generate_projects_index.py`

Regenerates `projects/index.html` (the projects homepage) from every
`projects/<project>/summary/info.yml`. Run it manually whenever you add a project or edit a
summary, and commit the resulting `projects/index.html` along with your other changes.

Setup (once):

```bash
pip install -r scripts/requirements.txt
```

Run:

```bash
python3 scripts/generate_projects_index.py
```

See [`projects/SUMMARY_SCHEMA.md`](../projects/SUMMARY_SCHEMA.md) for the `summary/info.yml`
format used to add or edit a project's entry on the homepage.
