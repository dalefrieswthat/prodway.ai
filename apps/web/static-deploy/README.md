# Static deploy (fallback for GitHub Pages)

This folder is deployed to prodway.ai when the Next.js build is broken.

- **To switch back to Next.js:** Fix `npm run build` (e.g. resolve generateBuildId/config), then in `.github/workflows/pages.yml` change `path` from `apps/web/static-deploy` to `apps/web/out` and restore the Node install + build steps.
