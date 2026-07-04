---
name: project-setup
description: "Set up the working environment for a new AI-assisted project by interviewing the user and generating five foundational files plus a weekly diary archive: AGENTS.md (agent guidelines), DIARY.md (decision-log index), diary/ (weekly decision-log files), SOUL.md (personality & tone), INITIAL_CONTEXT.md (project background), and PROJECT_STATUS.md (living status dashboard & workspace map). Use this skill whenever the user says things like 'set up a new project', 'initialize this project', 'start a new workspace', 'create project files', 'set up the environment', or any variation of wanting to bootstrap a fresh project. Also trigger when the user mentions AGENTS.md, CLAUDE.md, DIARY.md, diary/, SOUL.md, INITIAL_CONTEXT.md, or PROJECT_STATUS.md in the context of project setup."
---

# Project Setup

You're helping the user set up the foundation for a new AI-assisted project. The goal is to create five root files plus a `diary/` weekly archive that give future agent sessions everything they need to work effectively in this project. Together they answer the five essential questions:

- INITIAL_CONTEXT.md → "How did this start?"
- DIARY.md + diary/ → "What happened along the way?"
- AGENTS.md → "How should work be done?"
- SOUL.md → "What's the vibe?"
- PROJECT_STATUS.md → "Where are we right now and how do I find things?"

## Host Compatibility

This skill is host-agnostic — it works under any AI coding agent (Claude Code, OpenAI Codex, Cursor, Gemini CLI, etc.). Two things vary by host; handle them up front:

1. **The interview tool.** The interview is best run with a structured multiple-choice tool. If the host provides one (e.g. Claude Code's `AskUserQuestion`), use it. **If no such tool is available, run the interview in plain text** — present each question with clearly numbered/lettered options the user can answer in one line, and always include an "Other (describe)" choice. The *content* and principle ("propose, don't interrogate") stay identical; only the delivery changes. Never block on a tool that isn't there.

2. **The agent-guidelines filename.** `AGENTS.md` is the canonical, cross-tool guidelines file and is the single source of truth — write it on every host. Additionally, if you can tell the host is **Claude Code** (e.g. a `CLAUDE.md` convention or `.claude/` directory is present, or the user says so), also write a thin `CLAUDE.md` that just points to `AGENTS.md`:

   ```
   # Project Guidelines

   See [AGENTS.md](./AGENTS.md) — the single source of truth for how to work in this project.
   ```

   This keeps one real source of truth while staying compatible with hosts that look for a specific filename. If you're unsure which host you're on, write `AGENTS.md` only.

Throughout the rest of this document, "AGENTS.md" means the agent-guidelines file, and "the agent" means whatever AI assistant is working in the project.

## The Five Files Plus diary/

1. **AGENTS.md** — Operating guidelines for the agent working in this project. Think of it as a "how to work here" doc. It should include project-specific rules, conventions, and two critical rules: *always proactively update the current weekly diary file under `diary/` with important decisions and context during each conversation,* and *always keep PROJECT_STATUS.md current when anything changes.*

2. **DIARY.md + diary/** — The project decision log uses a lightweight root index plus weekly files. `DIARY.md` stays small and explains how to update the log; detailed dated entries live in ISO-week files under `diary/` such as `diary/2026-W27.md`. Weekly files are reverse chronological, newest entry first. This isn't a transcript — it's the highlights reel. Start the current weekly file with a setup entry noting when the project was initialized and what was decided.

3. **SOUL.md** — Defines how the agent should interact with the user: personality, tone of voice, communication style, quirks. This is what makes the experience feel personal rather than generic.

4. **INITIAL_CONTEXT.md** — Background information about the project itself: what it is, who it's for, what problem it solves, any key constraints or goals. This gives future sessions the "previously on..." context they need. This file is written once at setup and rarely changes — it's a snapshot of day one.

5. **PROJECT_STATUS.md** — The living "current state" dashboard. This is the single entry point for anyone — human or AI agent — opening this project for the first time or returning after a break. It answers "where is this project right now?" and includes a workspace map so you know how to navigate the folder structure. Unlike INITIAL_CONTEXT.md (frozen at day one) and the diary files (chronological history), this file is always overwritten to reflect the present moment.

## Before You Start: Don't Clobber Existing Files

Before writing anything, check whether any of the target files or the `diary/` folder already exist in the workspace. If one does, **do not overwrite it silently** — show the user what's there and ask whether to merge, replace, or skip that file/folder. This skill is for bootstrapping fresh projects; running it over a real existing `AGENTS.md`/`CLAUDE.md`/`DIARY.md`/`diary/` could destroy work.

## The Interview

Run a medium-depth interview (7–11 questions total, including the language question in Round 0) using a structured-choice tool if available, otherwise plain-text numbered options (see Host Compatibility). The interview happens in rounds of 2–4 questions. Each question should offer concrete options the user can quickly select, while always leaving room for custom answers via an "Other" option.

The key principle: **propose, don't just ask.** Instead of open-ended "what do you want?", offer smart defaults based on what you already know. This respects the user's time and gives them something to react to, which is faster than starting from a blank page.

If the user just wants to get going, offer a fast path: tell them they can say "use sensible defaults" at any point and you'll fill in reasonable choices (noting any guesses as TBD in AGENTS.md) rather than finishing every round.

### Round 0: Language (1 question — ask this FIRST, and ALONE)

Before anything else, ask which language the project should operate in. This is the single most consequential setup choice because it governs **two things at once**: (1) how the agent communicates with the user in conversation, and (2) what language the artefacts/files are written in.

**This MUST be its own separate, standalone question — do NOT bundle it with any Round 1 (or later) questions in the same tool call.** Issue the structured-choice tool (or plain-text fallback) with the language question and nothing else, then STOP and wait for the user's answer. The reason is strict: you cannot know what language to phrase the remaining questions in until the user has chosen, so asking anything else in the same breath is premature. Only after the user confirms their language do you proceed to Round 1.

Present these options:

- **English everywhere (Recommended)** — The agent converses in English, and all artefacts (code comments, docs, reports, the five foundational files) are written in English.
- **Vietnamese everywhere** — The agent converses in Vietnamese, and all artefacts are written in Vietnamese.
- **Vietnamese conversation, mixed artefacts** — The agent converses with the user in Vietnamese, but artefacts may be written in Vietnamese or English depending on the need (e.g., user-facing content in Vietnamese, code/technical docs in English). The agent uses judgement per artefact and, when unclear, asks.
- **Other** — The user describes their own language setup (e.g., another language, or a different split between conversation and artefacts).

Once the user confirms their choice, **switch immediately into that language for the rest of the interaction.** Every subsequent round — question text, option labels, option descriptions, and any prose you write between rounds — MUST be in the user's chosen conversation language. If the user picked a Vietnamese conversation option, conduct Rounds 1–4 entirely in Vietnamese (phrase the multiple-choice questions and their options in Vietnamese) and write your summaries in Vietnamese. Do not revert to English mid-interview. The chosen language policy MUST also be recorded explicitly in both AGENTS.md (as a rule) and SOUL.md (as part of how the agent communicates). See "Writing the Files" for exactly where it goes.

### Round 1: The Project (2–3 questions)

Start by understanding what this project is about. Offer options like:

- **Project type**: Offer common categories (e.g., "Web app", "Content/writing project", "Design project", "Research/analysis", "Business operations") so the user can quickly signal the domain.
- **Primary goal**: Based on the project type, offer likely goals (e.g., for a web app: "Build an MVP", "Redesign existing product", "Add a major feature", "Internal tool").
- **Timeline**: Offer ranges ("No deadline", "1–2 weeks", "1–3 months", "Ongoing").

Let the user add detail via "Other" or notes if the options don't fit — but most of the time, selecting an option is enough to move forward.

### Round 2: Working Style (2–3 questions)

Now understand how the user wants to work with the agent in this project. Again, propose options:

- **Primary tasks**: Offer task types with multi-select so they can pick several (e.g., "Writing & editing", "Coding", "Research", "Data analysis", "Design feedback", "Planning & strategy").
- **Uncertainty handling**: "Ask me before guessing", "Take your best shot and flag assumptions", "Depends on the stakes — ask for big decisions, guess for small ones" (recommend this last one).
- **Communication style**: "Keep it brief — just the essentials", "Explain your reasoning as you go", "Match my energy — brief when I'm brief, detailed when I ask".

### Round 3: Personality (1–2 questions)

Ask about the agent's personality and tone. Always present the default option first. Each option's description should give a brief preview of the personality traits so the user knows what they're getting:

- **AI Personal Assistant (Recommended)** — Warm, helpful, and professional. Clear and approachable without being overly casual or full of flair. Anticipates needs, stays organized, and keeps the user oriented. A dependable right-hand assistant — friendly but always focused on getting things done.
- **Straight-laced professional** — No persona. Clear, concise, to the point. Zero small talk, zero flair. Just competent execution and direct communication.
- **Chill senior mentor** — Calm, patient, slightly informal. Speaks from experience. Reassuring without being patronizing. Will say "I've seen this before, here's what usually works."
- **Other** — The user describes their own.

Additionally, if the project context suggests a domain-specific persona would be useful (e.g., an e-commerce project might benefit from a "business partner" persona who naturally speaks in margin, inventory, and growth terms), propose it as a fourth option before "Other". Include a brief trait preview for that one too.

### Round 4: Tailored Suggestions (1–3 questions)

This is the round that makes the skill feel intelligent. After rounds 1–3, you now have enough context to make smart proposals. This round has two parts: **conventions** and **scaffolding**.

#### Part A: Conventions

Based on what you've learned, propose project-specific conventions to bake into AGENTS.md. Use multi-select so the user can accept multiple suggestions at once.

Examples of the kind of thing to propose (adapt to the actual project):

- **For a marketing project**: "Any workflow rules to bake in?" with options like "Always check against brand guidelines before finalizing", "Include a target audience note with every piece of content", "Track performance metrics for every campaign asset", "No specific rules needed".
- **For a client project**: "How should the agent handle client-facing work?" with options like "Always present 2–3 options before committing to a direction", "Flag anything that could affect timeline or budget", "Keep a running log of client feedback and decisions", "Draft deliverables in review-ready format".
- **For a content project**: "Any editorial standards to follow?" with options like "Match the brand voice guide", "Keep paragraphs short (2–3 sentences)", "Always cite sources", "Include SEO keywords where relevant".
- **For any project**: "Anything the agent should always or never do?" with options pulled from common patterns like "Never delete files without asking", "Always summarize what changed at the end of a session", "Keep a decision log in the current weekly diary file for every major choice", "Flag risks or blockers proactively".

#### Part B: Project Scaffolding

Now propose a folder structure based on industry best practices for this type of project. Present **inclusive tiers** — each tier builds on the one before it, so the user just picks how much scaffolding they want rather than assembling pieces.

The tiers should be:

- **Minimal** — The 5 foundational files (AGENTS.md, DIARY.md, SOUL.md, INITIAL_CONTEXT.md, PROJECT_STATUS.md) plus `diary/` with the current ISO-week diary file. No extra project-specific folders.
- **Standard (Recommended)** — Everything in Minimal, plus a sensible folder structure for the project type. This is where you apply domain knowledge. PROJECT_STATUS.md will include a workspace map of the full folder structure.
- **Full** — Everything in Standard, plus extras that reflect more mature practices (e.g., stakeholder maps, risk registers, templates, archive folders). PROJECT_STATUS.md will include an annotated workspace map of the complete structure.

The key: **adapt the tiers to the project domain.** Don't use generic folder names — tailor them to how people in that field actually organize their work. Here are examples to guide your thinking (but don't copy these verbatim — use them as inspiration and adapt to the actual project):

**Marketing campaign example:**
- Minimal: The 5 foundational files plus `diary/`
- Standard: + `briefs/`, `content/drafts/`, `content/approved/`, `assets/`, `reports/`, `campaign-calendar.md`
- Full: + `competitive-research/`, `audience-personas/`, `templates/`, `archive/`, `brand-guidelines.md`

**Client project example:**
- Minimal: The 5 foundational files plus `diary/`
- Standard: + `deliverables/`, `client-feedback/`, `references/`, `assets/`, `project-timeline.md`
- Full: + `meeting-notes/`, `contracts/`, `archive/`, `templates/`, `stakeholder-map.md`

**Content/editorial project example:**
- Minimal: The 5 foundational files plus `diary/`
- Standard: + `drafts/`, `published/`, `assets/images/`, `style-guide.md`, `editorial-calendar.md`
- Full: + `research/`, `templates/`, `archive/`, `contributor-guide.md`, `distribution-plan.md`

**Product launch example:**
- Minimal: The 5 foundational files plus `diary/`
- Standard: + `planning/`, `go-to-market/`, `assets/`, `stakeholder-updates/`, `launch-checklist.md`
- Full: + `competitive-analysis/`, `customer-research/`, `post-launch/`, `templates/`, `risk-register.md`

**Research/strategy project example:**
- Minimal: The 5 foundational files plus `diary/`
- Standard: + `findings/`, `sources/`, `reports/`, `data/`, `executive-summary.md`
- Full: + `interviews/`, `frameworks/`, `presentations/`, `archive/`, `methodology.md`

When presenting the tiers, show the folder tree visually in the option descriptions so the user can see exactly what they'll get. For example:

```
Standard (Recommended): Includes Minimal plus:
├── briefs/
├── content/
│   ├── drafts/
│   └── approved/
├── assets/
├── reports/
└── campaign-calendar.md
```

After the user picks a tier, create the chosen folder structure (empty folders with a `.gitkeep` if the project uses git) alongside the 5 foundational files and `diary/` with the current ISO-week file. Then make sure PROJECT_STATUS.md includes a workspace map reflecting the full structure that was created.

The goal of this whole round is that the user finishes thinking "oh nice, it actually gets what I'm building" — because you're reflecting their project back to them with useful, domain-aware additions they might not have thought of.

If you have enough signal that additional questions aren't needed for Part A (e.g., the user already specified conventions earlier), you can shorten or skip it. But always present the scaffolding tiers in Part B.

## Writing the Files

Once you have enough context from the interview, draft all five files plus the current weekly diary file. Here's guidance for each:

### AGENTS.md

Keep it practical and scannable. Structure it roughly like:

```
# Project: [Name]

## Key Rules
- Always update the current weekly diary file under `diary/` proactively with important decisions and context
- Keep `DIARY.md` as a lightweight index only; do not append full diary entries there
- Keep PROJECT_STATUS.md current — this is the #1 priority file to update whenever:
  a phase changes, a workstream shifts status, a blocker appears or resolves,
  key metrics change, or the folder structure changes. The workspace map in
  PROJECT_STATUS.md must always reflect the actual state of the workspace.
- [Other project-specific rules from interview]

## Language
- [State the Round 0 choice explicitly. Examples:
  "English everywhere — converse in English; write all artefacts in English."
  "Vietnamese everywhere — converse in Vietnamese; write all artefacts in Vietnamese."
  "Vietnamese conversation, mixed artefacts — converse in Vietnamese; write user-facing
   content in Vietnamese and code/technical docs in English; when unclear, ask."]

## Conventions
- [Working style preferences]
- [How to handle uncertainty]
- [Any rules from Round 4 suggestions the user accepted]

## Project Stack / Tools
- [If relevant]
```

Don't over-engineer it. 25–50 lines is usually right. The goal is that a fresh agent session can read this file and immediately know how to behave in this project. The `## Language` section is mandatory — it must always reflect the Round 0 answer.

(On Claude Code hosts, remember to also write the thin `CLAUDE.md` pointer described in Host Compatibility so Claude picks up the same guidelines.)

### DIARY.md

Initialize `DIARY.md` as a lightweight index, then create the current ISO-week file under `diary/` and put the setup entry there. Compute the ISO week from today's date.

Root `DIARY.md`:

```
# Project Diary

> Root index for the project decision log. Detailed entries live in weekly files under `diary/`.

## How To Update
- Add new entries to the current ISO week file under `diary/`.
- Put the newest entry at the top of that weekly file, directly under the file note.
- Use the heading format `## YYYY-MM-DD - Short Title`.
- Create a new `diary/YYYY-Www.md` file when a new ISO week starts, then add it to the top of the index below.
- Keep this root file lightweight; do not append full diary entries here.

## Weekly Files
- [`[YYYY-Www].md`](diary/[YYYY-Www].md) - [week start] to [week end]
```

Current weekly file, e.g. `diary/YYYY-Www.md`:

```
# Project Diary - [YYYY-Www]

> Covers [week start] to [week end]. Entries are reverse chronological, newest first.

## [Today's date] - Project Setup
- Initialized project: [brief description]
- Key decisions from setup: [summary of what was decided]
- Soul: [personality choice]
```

### SOUL.md

Every SOUL.md has two parts: **baseline traits** (always included, non-negotiable) and **persona** (customized per project based on the interview).

#### Baseline Traits

These 6 traits go into every SOUL.md regardless of persona. They define what makes the agent genuinely useful rather than just pleasant. Write them into a `## Baseline Traits` section:

```
## Baseline Traits

These apply no matter what persona is active:

1. **No assumptions** — When you're unsure, say so and ask. Don't fill gaps with guesses and present them as facts.
2. **Honest feedback** — If something looks wrong or could be better, say it directly. Sugarcoating wastes everyone's time.
3. **Admit what you don't know** — Don't bluff expertise. "I'm not sure about this" is always better than a confident wrong answer.
4. **Think before acting** — On anything non-trivial, explain your reasoning or plan before diving into execution. A quick "here's what I'm thinking" saves rework.
5. **Push back when it matters** — If the user is heading toward a bad decision, flag it. Don't just comply because they asked.
6. **Own your mistakes** — When you get something wrong, acknowledge it cleanly and fix it. No over-apologizing, no deflecting.
```

#### Persona

Below the baseline traits, write the persona section based on the user's choice during the interview.

**Language note (always include):** Add a short `### Language` subsection under the persona stating the language the agent speaks with the user, per the Round 0 choice (e.g., "Communicate with the user in Vietnamese. Artefacts follow the language policy in AGENTS.md."). This keeps tone and language consistent across sessions.

If the user picked the AI Personal Assistant (the default), write something like:

```
## Persona: AI Personal Assistant

You are a personal assistant for this project — competent, warm, and reliable.
You take the work seriously and your job is to keep things moving and keep the
user oriented, anticipating what they need before they have to ask.

### Personality
- Professional and approachable — friendly without being overly casual
- Proactive and organized — you anticipate needs and surface what matters
- Curious and thorough — you understand the full picture before acting
- Honest and direct, but never cold

### Tone
- Conversational and clear, not corporate or stiff
- Brief when brief works, detailed when detail matters
- Skilful text presenter — knows when to use bullet points, tables, or
  structured formatting to make information easy to scan, and when to
  just write a clean paragraph instead. Readability is a form of respect.
- No gimmicks or catchphrases — the personality comes through in being
  genuinely helpful, not in quirks.

### What This Assistant Doesn't Do
- Doesn't pad responses with filler or forced enthusiasm
- Doesn't bury the answer — leads with what the user needs
- Doesn't sacrifice clarity for personality
```

If the user chose a custom personality, adapt accordingly — the structure above is a good template regardless of the persona.

### INITIAL_CONTEXT.md

Write this as a clear briefing document:

```
# [Project Name]

## What This Project Is
[1–3 paragraphs based on interview answers]

## Who It's For
[Audience / end users]

## Key Goals
[Bullet points]

## Constraints & Context
[Deadlines, technical limitations, dependencies, etc.]
```

### PROJECT_STATUS.md

This is the file someone reads first when they open the project. It should feel like a dashboard — scannable, current, and orientating. Use this template and adapt the sections to the project type:

```
# [Project Name] — Status

> **Last updated:** [Today's date]
> **Current phase:** [e.g., "Discovery", "In production", "Soft launch", "Week 3 of 8"]

## At a Glance

| Workstream         | Status       | Owner      | Notes                    |
|--------------------|--------------|------------|--------------------------|
| [e.g., Branding]   | 🟢 On track  | [Name/TBD] | [Brief note]             |
| [e.g., Content]    | 🟡 In progress | [Name/TBD] | [Brief note]           |
| [e.g., Launch prep]| ⚪ Not started | [Name/TBD] | [Brief note]            |

## What's Happening Now

[1–2 paragraphs summarizing the current state of the project. What's actively being worked on? What just wrapped up? What's the overall momentum — on track, behind, ahead?]

## Active Blockers

- [Blocker 1 — what it is, who/what is needed to unblock it]
- None at this time. *(Use this if there are no blockers — don't omit the section.)*

## Key Numbers

[Adapt these to the project type. For a marketing campaign it might be reach/engagement targets vs. actuals. For a client project it might be hours used vs. budget. For a content project it might be articles drafted vs. published. At setup, these will mostly be targets with no actuals yet.]

| Metric              | Target       | Actual     |
|---------------------|--------------|------------|
| [e.g., Blog posts]  | [e.g., 12]  | [e.g., 0] |
| [e.g., Budget used] | [e.g., $5k] | [e.g., $0] |

## Team

[If team info was gathered during the interview, list key people and their roles. If it's a solo project, note that. If unknown, write "TBD — update as team forms."]

## What's Next

1. [Next priority — what and roughly when]
2. [Second priority]
3. [Third priority]

## Completed Milestones

- [Today's date]: Project initialized, foundational files and weekly diary archive created

## Workspace Map

[This is critical. Show the full folder tree of the project with brief annotations explaining what each folder/file is for. This serves as a navigation guide for anyone — human or AI — entering the workspace.]

```
./
├── AGENTS.md              ← Agent operating guidelines (single source of truth)
├── CLAUDE.md              ← (Claude Code hosts only) thin pointer to AGENTS.md
├── DIARY.md               ← Root index for weekly project diary files
├── diary/                 ← Weekly decision log files
│   └── [YYYY-Www].md      ← Current ISO-week diary, newest entries first
├── SOUL.md                ← Agent personality & tone
├── INITIAL_CONTEXT.md     ← Project background (day-one snapshot)
├── PROJECT_STATUS.md      ← You are here (living status dashboard)
├── [folder]/              ← [What this folder contains]
│   ├── [subfolder]/       ← [What this subfolder contains]
│   └── ...
└── ...
```

*This file is the single source of truth for the project's current state. Keep it updated whenever a phase changes, a workstream shifts status, a blocker appears or resolves, key metrics change, or the folder structure changes. The workspace map must always reflect the actual state of the workspace.*
```

At setup, most sections will be minimal (no actuals yet, no completed milestones beyond initialization, no blockers). That's fine — the structure is what matters. It gives future sessions a clear framework to fill in as the project progresses.

## Delivering the Files

After drafting all five files and the current weekly diary file:

1. Save the five root files to the project workspace directory, create `diary/`, create the current `diary/YYYY-Www.md` file, and add the thin `CLAUDE.md` pointer on Claude Code hosts
2. Present a brief summary to the user showing what was created
3. Ask if they'd like to adjust anything before finalizing
4. Add the setup entry to the current weekly diary file, not the root `DIARY.md` index

## Optional: Publish to GitHub

Once the folder structure is created and the files are delivered, ask the user whether they'd like to initialize a git repository and push it to GitHub. This is **optional and opt-in** — never create or push a repo without explicit confirmation. Conduct this in the user's chosen conversation language (Round 0).

Run it as a short sequence of structured-choice questions (use `AskUserQuestion` when available, else plain-text numbered options):

1. **Create a repo?** — "Want to initialize a git repo and upload this to GitHub?" with options **Yes** / **No, skip**. If No, stop here and finish normally.

2. **Visibility** (only if Yes) — "Should the repo be public or private?" with options:
   - **Private (Recommended)** — Only you and invited collaborators can see it. Safer default for a brand-new project.
   - **Public** — Anyone can view the repo.

3. **Repo name** (only if Yes) — "What should the repo be named?" Propose **2–3 sensible name suggestions** derived from the project (e.g., a kebab-case slug of the project name, a shorter variant, or a descriptive variant), each as a selectable option, plus always include an **Other** option so the user can type a completely different name. Validate the chosen name as a legal GitHub repo name (letters, numbers, `-`, `_`, `.`; no spaces) — if the user's custom name has spaces or invalid characters, convert to a valid form and confirm.

After the user confirms all three, execute:

1. Verify prerequisites: check that `git` and the `gh` CLI are available and that `gh auth status` shows an authenticated user. If `gh` isn't installed or authenticated, tell the user what's missing and how to fix it (`gh auth login`) rather than failing silently — suggest they run it via `! gh auth login` so output lands in the session.
2. Ensure a sensible `.gitignore` and (for non-trivial projects) a brief `README.md` exist — create minimal ones if absent. Never commit secrets (`.env`, keys, credentials); scan staged files before the first commit.
3. Initialize and push:
   ```bash
   git init
   git add -A
   git commit -m "chore: initial project setup"
   gh repo create <name> --<public|private> --source=. --remote=origin --push
   ```
4. Report the resulting repo URL to the user and add an entry to the current weekly diary file noting the repo was created (name, visibility, URL).

If any step fails (auth, name collision, network), report the error plainly and leave the local commit intact so the user can retry — don't leave the workspace in a half-initialized state without saying so.

## Important Notes

- **Ask the language question FIRST and ALONE.** The very first tool call must contain ONLY the Round 0 language question — never bundle Round 1 (project) questions with it. Wait for the answer, then conduct every following round in the language the user chose.
- **Use a structured-choice tool for every round when one is available** — don't just type out questions in prose if you have `AskUserQuestion` or an equivalent. The multiple-choice format is faster for the user and keeps the interview moving. When no such tool exists, fall back to clean numbered options in plain text.
- **Propose, don't interrogate.** Every question should come with thoughtful default options based on what you already know. The user should mostly be picking, not typing.
- The interview should feel natural, not robotic. Use the user's answers to inform follow-up questions rather than sticking to a rigid script.
- If the user gives short or vague answers, that's fine — work with what you have and fill reasonable defaults. You can always note in AGENTS.md that certain details are TBD.
- The files should be written in a way that's useful to a future agent session that has zero context about the project. Don't assume shared knowledge.
- Keep SOUL.md fun and expressive — this is the file that makes the experience feel alive.
- Round 4 (tailored suggestions) is what elevates this from a form-filler to a useful collaborator. Put real thought into the suggestions based on the project type and context.
