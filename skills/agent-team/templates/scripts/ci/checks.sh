#!/usr/bin/env bash
# The `checks` CI job: everything that needs no services. Run from the repo root after the install
# step, by .github/workflows/ci.yml and by scripts/local-ci. Replace the commands with your project's.
set -euo pipefail

npm run typecheck
npm run lint -- --max-warnings 0
npm run format:check
npm test
