# Agent Skills

A collection of [Agent Skills](https://agentskills.io) — portable `SKILL.md` files that work across Claude Code, OpenAI Codex, Gemini CLI, Cursor, and other tools that support the open skills standard.

## Skills

| Skill | Description |
|-------|-------------|
| [`cost-aware-image-generation`](skills/cost-aware-image-generation/) | Generate images with a Gemini or OpenAI key at a predictable cost: medium quality and ~1024px on the short edge (any shape) by default, a stated reason for anything bigger, and a local ledger of every prompt, image, token count and cost (USD and VND). |
| [`dummy-commit`](skills/dummy-commit/) | Create and push an empty commit to `main` to force a redeploy (Vercel, Netlify, or any push-triggered CI). |
| [`elegant-everyday-visual-guide`](skills/elegant-everyday-visual-guide/) | Create original Elegant, Everyday fashion infographics from source visuals through a concise copy-selection and image-generation workflow. |
| [`image-upscale-webp`](skills/image-upscale-webp/) | Enlarge images with Upscayl's High Fidelity AI model and make web WebP files with Squoosh's encoder at quality 85, instead of plain resizing or default encoders. Needs the Upscayl app, Node and Python with numpy + Pillow. |
| [`lou-lilou-visual-guide`](skills/lou-lilou-visual-guide/) | Create original Lou & Lilou fashion infographics from source visuals through a concise copy-selection and image-generation workflow, featuring the Lou and Lilou personas. |
| [`project-setup`](skills/project-setup/) | Set up a new AI-assisted project by interviewing the user and generating five foundational files (AGENTS.md, DIARY.md, SOUL.md, INITIAL_CONTEXT.md, PROJECT_STATUS.md). Optionally publishes the project to GitHub. |

## Installation

Each skill is a self-contained folder under `skills/`. To install one, copy its folder into your tool's skills directory:

| Tool | Personal (all projects) | Project-local |
|------|-------------------------|---------------|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Codex / Cursor / Gemini CLI | `~/.agents/skills/` | `.agents/skills/` |

For example, to install `project-setup` for Claude Code:

```bash
cp -R skills/project-setup ~/.claude/skills/
```

The skill is picked up automatically the next time the tool starts. The folder name must stay the same as the skill's `name` in its frontmatter.

## License

See [LICENSE](LICENSE).
