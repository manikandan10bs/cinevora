# CHANGELOG

All meaningful changes to this project are recorded here.
Incomplete work must not be logged as finished.

Most recent entry goes at the top.

---

## Entries

## 2026-04-28 20:36 WIB - infra deploy - deploy to Vercel production

### Summary
Configured Vercel SPA routing, deployed `streamXie-ui` to production, verified the deployment and a deep-link route, and recorded the production demo URL in project docs.

### Type
infra

### Area
infra / docs / config

### Severity
medium

### Changes
- Added `vercel.json` with a fallback rewrite to `index.html` for React Router deep links.
- Added `.vercel` to `.gitignore` and cleaned duplicate local Vercel ignore entries.
- Deployed production to `https://streamxie-ui.vercel.app`.
- Updated `README.md` with a live demo badge, live demo section, and deployment URL.
- Updated `package.json` homepage to the production demo URL.
- Updated `CODER.md` with Vercel deployment notes.
- Updated `TODO.md` with completed deployment and a follow-up for Vercel/GitHub auto-deploy integration.

### Files
- `vercel.json` - Vercel SPA fallback rewrite.
- `.gitignore` - local Vercel metadata ignored.
- `README.md` - live demo and deployment URL.
- `package.json` - homepage URL.
- `CODER.md` - deployment notes.
- `TODO.md` - deployment follow-up tracking.
- `PLAN.md` - archived deployment plan.
- `CHANGELOG.md` - recorded deployment.

### Verification
- Ran `npm run build`; Vite production build completed successfully.
- Ran `vercel deploy --prod --yes`; deployment completed and aliased to `https://streamxie-ui.vercel.app`.
- Ran `curl -I https://streamxie-ui.vercel.app`; returned HTTP 200.
- Ran `curl -I https://streamxie-ui.vercel.app/browse`; returned HTTP 200, verifying SPA fallback routing.
- Ran `vercel inspect https://streamxie-ui.vercel.app --wait --timeout 90s`; deployment status was Ready.

### Migration / Deploy
- Migration: none.
- Env vars: none.
- Deploy steps: Vercel CLI production deploy.
- Rollback: redeploy a previous Vercel deployment or revert the deployment config commit and redeploy.

### Residual Risk
- Vercel GitHub repository integration failed because the Vercel account needs a GitHub Login Connection; manual CLI deployment is working, but automatic deploys from GitHub pushes are not connected yet.
- Build still reports the known non-blocking Vite chunk-size warning for the main JS bundle.

## 2026-04-28 20:07 WIB - docs license - add MIT license

### Summary
Added an MIT License so `streamXie-ui` has clear permissive public reuse terms, then synchronized README, npm metadata, project memory, TODO, and lockfile metadata.

### Type
docs

### Area
docs / config

### Severity
medium

### Changes
- Added `LICENSE` with MIT License text.
- Updated `README.md` with an MIT license badge and license section.
- Added `"license": "MIT"` to `package.json`.
- Refreshed root package metadata in `package-lock.json`.
- Updated `CODER.md` to record the license.
- Moved the license task from active TODO to Done.

### Files
- `LICENSE` - MIT License terms.
- `README.md` - public license badge and license section.
- `package.json` - npm license metadata.
- `package-lock.json` - lockfile license metadata.
- `CODER.md` - durable project license note.
- `TODO.md` - completed license follow-up.
- `PLAN.md` - archived completed license task.

### Verification
- Ran `npm install --package-lock-only --ignore-scripts`; npm audit reported 0 vulnerabilities.
- Verified `package.json` and root `package-lock.json` both report `MIT`.
- Ran `npm run build`; Vite production build completed successfully.

### Migration / Deploy
- Migration: none.
- Env vars: none.
- Deploy steps: none.
- Rollback: revert the license commit if a different license is chosen later.

### Residual Risk
- License choice was made as MIT based on the stated public reuse goal; a different legal strategy would require replacing the license in a follow-up commit.
- Build still reports the known non-blocking Vite chunk-size warning for the main JS bundle.

## 2026-04-28 20:02 WIB - chore git - publish initial repository

### Summary
Initialized the local workspace as a git repository, created the initial project commit, pushed `main` to the public GitHub repository, and updated project tracking docs to reflect the published state.

### Type
chore

### Area
config / docs

### Severity
low

### Changes
- Initialized the local repository and set the default branch to `main`.
- Added `origin` as `https://github.com/Matsumiko/streamXie-ui.git`.
- Created initial commit `57eee86` with the prepared project files.
- Pushed `main` to GitHub and set upstream tracking.
- Updated project status notes in `CODER.md`, `TODO.md`, and `PLAN.md`.

### Files
- `CODER.md` - updated repository status note.
- `TODO.md` - moved git initialization/push item to Done.
- `PLAN.md` - archived the completed push plan.
- `CHANGELOG.md` - recorded repository publication.

### Verification
- Ran `git push -u origin main`; push completed successfully.
- Ran `git ls-remote origin refs/heads/main`; remote branch exists.
- Confirmed generated output and runtime session JSON were not staged for the initial commit.

### Migration / Deploy
- Migration: none.
- Env vars: none.
- Deploy steps: none.
- Rollback: remove or revert the pushed commits from GitHub if publication needs to be undone.

### Residual Risk
- License risk was resolved by the later `2026-04-28 20:07 WIB` MIT license entry.
- The app has not been deployed to a hosted demo URL yet.

## 2026-04-28 19:50 WIB - docs project-docs - prepare public streamXie-ui documentation

### Summary
Prepared the project for public repository presentation by replacing placeholder docs with accurate streamXie-specific documentation, public setup guidance, visual DNA, and release backlog items.

### Type
docs

### Area
docs / config

### Severity
low

### Changes
- Created a polished public `README.md` with overview, feature list, installation, scripts, project structure, customization guide, deployment notes, exclusions, release checklist, contribution notes, and license status.
- Replaced `CODER.md` template content with durable project memory covering architecture, commands, conventions, environment variables, and gotchas.
- Replaced `FRONTEND-DNA.md` template content with streamXie-specific visual and interaction rules.
- Updated package metadata from `streamxie` to `streamxie-ui`, added repository metadata, keywords, and a `preview` script.
- Refreshed `package-lock.json` after package metadata changes.
- Replaced empty `TODO.md` sections with public-release follow-up items.

### Files
- `README.md` - public repository documentation.
- `CODER.md` - project-specific agent/developer memory.
- `FRONTEND-DNA.md` - visual system and UI rules.
- `TODO.md` - ranked public-release backlog.
- `PLAN.md` - active plan and execution status.
- `package.json` - public package metadata and scripts.
- `package-lock.json` - lockfile metadata refresh.
- `.runbook/sessions/SESSION-20260428-1946.json` - runtime checkpoint.

### Verification
- Completed project audit across docs, package metadata, routes, source structure, and visual tokens.
- Ran `npm install --package-lock-only --ignore-scripts`; npm audit reported 0 vulnerabilities.
- Searched updated documentation for leftover placeholder markers.
- Ran `npm run build`; Vite production build completed successfully.

### Migration / Deploy
- Migration: none.
- Env vars: none.
- Deploy steps: none required beyond the existing static build flow.
- Rollback: restore the edited docs and package metadata from source control once the workspace is initialized as a git repository.

### Residual Risk
- Repository publication risk was resolved by the later `2026-04-28 20:02 WIB` GitHub push entry.
- Build completed with a Vite bundle-size warning for `dist/assets/index-*.js` above 500 kB; code splitting is recommended before scaling the app.
- License risk was resolved by the later `2026-04-28 20:07 WIB` MIT license entry.
