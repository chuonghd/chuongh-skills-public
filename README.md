# Agent Skills

A collection of [Agent Skills](https://agentskills.io) — portable `SKILL.md` files that work across Claude Code, OpenAI Codex, Gemini CLI, Cursor, and other tools that support the open skills standard.

## Skills

| Skill | Description |
|-------|-------------|
| [`cost-aware-image-generation`](skills/cost-aware-image-generation/) | Generate images with a Gemini or OpenAI key at a predictable cost: medium quality and ~1024px on the short edge (any shape) by default, a stated reason for anything bigger, and a local ledger of every prompt, image, token count and cost (USD and VND). |
| [`dummy-commit`](skills/dummy-commit/) | Create and push an empty commit to `main` to force a redeploy (Vercel, Netlify, or any push-triggered CI). |
| [`elegant-everyday-visual-guide`](skills/elegant-everyday-visual-guide/) | Create original Elegant, Everyday fashion infographics from source visuals through a concise copy-selection and image-generation workflow. |
| [`htmlgen`](skills/htmlgen/) | Turn the topic being discussed into one standalone, Notion-like HTML page: summary first, type-specific structure, inline SVG diagrams, no external resources, then open it. |
| [`image-upscale-webp`](skills/image-upscale-webp/) | Enlarge images with Upscayl's High Fidelity AI model and make web WebP files with Squoosh's encoder at quality 85, instead of plain resizing or default encoders. Needs the Upscayl app, Node and Python with numpy + Pillow. |
| [`lou-lilou-visual-guide`](skills/lou-lilou-visual-guide/) | Create original Lou & Lilou fashion infographics from source visuals through a concise copy-selection and image-generation workflow, featuring the Lou and Lilou personas. |
| [`project-setup`](skills/project-setup/) | Set up a new AI-assisted project by interviewing the user and generating five foundational files (AGENTS.md, DIARY.md, SOUL.md, INITIAL_CONTEXT.md, PROJECT_STATUS.md). Optionally publishes the project to GitHub. |

## Installation

Clone the repo and run `install.sh`. It links each skill you pick into the shared skills folder, so every tool uses the same copy and a `git pull` updates them all:

```bash
git clone https://github.com/chuonghd/chuongh-skills-public.git
cd chuongh-skills-public

./install.sh                         # pick from a numbered list
./install.sh htmlgen dummy-commit    # install one or more by name
./install.sh --all                   # install every skill
./install.sh --list                  # show what's installed
./install.sh -u htmlgen              # uninstall
```

Each picked skill gets two links, both pointing at `skills/<name>` in this repo:

| Link | Read by |
|------|---------|
| `~/.agents/skills/<name>` | Codex, Gemini CLI, Cursor and other tools that follow the open skills standard |
| `~/.claude/skills/<name>` | Claude Code, which doesn't read `~/.agents/skills/` (pass `--no-claude` to skip) |

Notes:

- The script makes one link per skill. It doesn't replace the whole `skills/` folder, so other skills already in there are kept. It never overwrites a real folder: if one with the same name exists, it skips it and tells you.
- Don't also link `~/.gemini/skills/`. Gemini CLI already reads `~/.agents/skills/`, so the skills would show up twice.
- Restart the tool after installing. Claude Code updates have been reported to remove symlinks from `~/.claude/skills/`, and the Claude Desktop app skips them. If a skill goes missing, re-run `./install.sh`. For Desktop, copy the folder instead.
- Set `AGENTS_SKILLS_DIR` / `CLAUDE_SKILLS_DIR` to link somewhere else, e.g. a project's `.agents/skills/` and `.claude/skills/`.

To install by hand instead, copy the folder (e.g. `cp -R skills/project-setup ~/.claude/skills/`). The folder name must stay the same as the skill's `name` in its frontmatter.

## License

See [LICENSE](LICENSE).
