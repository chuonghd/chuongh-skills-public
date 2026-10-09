---
name: dummy-commit
description: "Create and push an empty commit to main to force a redeploy (e.g. Vercel, Netlify, or any CI that deploys on push). Use when the user explicitly asks to 'trigger a redeploy', 'force a redeploy', 'push an empty commit', 'dummy commit', or 'kick the deploy'. Do not trigger for ordinary commit or push requests."
---

# Dummy Commit

Push an empty commit to `main` so the hosting platform picks up a new push and redeploys. No file changes are made.

**IMPORTANT:** No prompts, no questions — just run. Report status after each step.

## Workflow

1. Make sure nothing is staged, so the "empty" commit doesn't pick up real changes:
   ```bash
   git diff --cached --quiet
   ```
   If this exits non-zero, stop and tell the user there are staged changes.
2. Switch to `main` and pull latest:
   ```bash
   git checkout main && git pull
   ```
3. Empty commit and push:
   ```bash
   git commit --allow-empty -m "chore: trigger redeploy" && git push origin main
   ```
4. Report success/failure status.
