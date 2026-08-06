# Documentation workflow

## Ownership

Reference documentation is edited in the repository that implements the documented behavior. The
docsite owns only site-wide landing pages, navigation, theme configuration, and publication
instrumentation.

## Add or update documentation

1. Edit Markdown and assets in the source project's `docs/` directory.
2. From `klab-docsite`, run `python scripts/sync_docs.py`.
3. Review synchronized changes under `docs/reference/`.
4. Run `mkdocs build --strict` before committing the docsite update.

`python scripts/sync_docs.py --check` is suitable for verification scripts because it reports drift
without modifying the working tree.

## Add another sibling project

Add one `[[projects]]` entry to `doc-sources.toml`:

```toml
[[projects]]
id = "project-id"
title = "Display title"
repository = "../sibling-project"
source = "docs"
destination = "reference/project-id"
required = false
```

Set `required = true` once documentation is expected to exist in every checkout. Then add the
desired pages to `nav` in `mkdocs.yml`.

