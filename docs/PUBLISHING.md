# Publishing the field guide

The public site is https://guruswami-ai.github.io/flockinator-public/.
GitHub Pages publishes the `docs` directory of `main`. `docs/.nojekyll`
keeps the already-generated HTML, SVG and PNG files unchanged; the root
`index.html` forwards visitors to `scenarios/quadcopter-survey/`.

To update the guide, edit its source files and regenerate from the repository root:

```sh
uv run --no-project docs/scenarios/quadcopter-survey/build-guide.py --repo .
```

Review the resulting files, check the page on desktop and mobile, and refresh
`SHA256SUMS` in the guide directory when its contents change. Commit the guide
changes and merge them into `main`; GitHub Pages then deploys automatically.
Check the Pages deployment in GitHub Actions and verify the public URL.

The website serves static documentation. It has no controller connection,
credentials, live node journals, or inference service. The render manifest
records source hashes and illustrative fixture inputs.

To roll back a guide update, revert its commit on `main` and verify the resulting
Pages deployment. The hardware fleet and HERDR are independent of this site.
