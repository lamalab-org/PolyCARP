# Archive a PolyCARP release on Zenodo

## Prepare

1. Merge the release preparation PR and check that GitHub's tests and paper
   reproduction check pass for the commit to be released.
2. Keep the version in `pyproject.toml`, `src/copolpredictor/__init__.py`,
   `uv.lock`, `CITATION.cff`, and `.zenodo.json` consistent.
3. Check the title, authors, ORCIDs, license, and paper link. Zenodo uses
   `.zenodo.json` when both metadata files exist; GitHub uses `CITATION.cff`.
   Add `date-released` to the citation file only when the release date is known.
4. Prepare release notes and identify the exact commit. If that commit changes,
   rebuild the archive and checksum before publishing.

## Publish once

Choose one route for a version:

- **GitHub integration:** enable `lamalab-org/PolyCARP` in Zenodo's GitHub
  settings, then publish the GitHub release. Zenodo archives it automatically.
- **Manual deposit:** upload the ZIP from the approved commit as Software,
  enter the metadata from `.zenodo.json`, and publish the Zenodo draft. If a
  record already exists, create a new version of that record.

Do not also use the other route for the same version: that creates duplicate
records. A GitHub draft release does not create a published Zenodo record.

## After publication

Verify the archived files and version, then add the version-specific DOI to the
manuscript's code-availability statement and GitHub release notes. Add the DOI
and actual release date to `CITATION.cff` in a follow-up commit. Use the DOI for
this exact version when citing the software used in the paper.

[Zenodo's GitHub guide](https://help.zenodo.org/docs/github/archive-software/github-upload/)
· [Metadata guidance](https://help.zenodo.org/docs/github/describe-software/)
