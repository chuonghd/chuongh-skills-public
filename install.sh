#!/usr/bin/env bash
# Install skills from this repo by symlinking them into the shared skills folder.
#
#   ~/.agents/skills/<skill>  -> <repo>/skills/<skill>   (read by Codex, Gemini CLI, ...)
#   ~/.claude/skills/<skill>  -> <repo>/skills/<skill>   (read by Claude Code)
#
# Each skill gets its own link, so other skills already in those folders are left alone,
# and a `git pull` in this repo updates every tool at once.

set -euo pipefail

REPO_SKILLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/skills"
AGENTS_DIR="${AGENTS_SKILLS_DIR:-$HOME/.agents/skills}"
CLAUDE_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

usage() {
  cat <<EOF
Usage: ./install.sh [options] [skill ...]

With no skill names, shows a numbered list to pick from.

Options:
  -a, --all         install every skill in this repo
  -l, --list        list the skills in this repo and whether each is installed
  -u, --uninstall   remove the links for the named (or picked) skills
      --no-claude   skip ~/.claude/skills (only link into ~/.agents/skills)
  -h, --help        show this help

Examples:
  ./install.sh                         # pick from a list
  ./install.sh htmlgen dummy-commit    # install two skills
  ./install.sh --all                   # install everything
  ./install.sh -u htmlgen              # uninstall one skill

Folders (override with env vars):
  AGENTS_SKILLS_DIR  default: ~/.agents/skills
  CLAUDE_SKILLS_DIR  default: ~/.claude/skills
EOF
}

# All skill folder names in the repo (folders that contain a SKILL.md).
ALL_SKILLS=()
for d in "$REPO_SKILLS"/*/; do
  [ -f "$d/SKILL.md" ] && ALL_SKILLS+=("$(basename "$d")")
done
if [ ${#ALL_SKILLS[@]} -eq 0 ]; then
  echo "No skills found in $REPO_SKILLS" >&2
  exit 1
fi

is_skill() {
  local s
  for s in "${ALL_SKILLS[@]}"; do [ "$s" = "$1" ] && return 0; done
  return 1
}

# Prints "yes" when <dir>/<skill> is a link pointing at this repo's copy.
installed_in() {
  local link="$1/$2"
  if [ -L "$link" ] && [ "$(readlink "$link")" = "$REPO_SKILLS/$2" ]; then
    echo "yes"
  else
    echo "no"
  fi
}

list_skills() {
  local i=1 s line
  for s in "${ALL_SKILLS[@]}"; do
    line="$(printf '%2d) %-32s agents:%-3s' "$i" "$s" "$(installed_in "$AGENTS_DIR" "$s")")"
    [ "$USE_CLAUDE" = 1 ] && line="$line  claude:$(installed_in "$CLAUDE_DIR" "$s")"
    echo "$line"
    i=$((i + 1))
  done
}

# Make <dir>/<skill> a link to the repo copy. Never touches a real folder or file.
link_one() {
  local dir="$1" skill="$2" target="$REPO_SKILLS/$2" link="$1/$2"
  mkdir -p "$dir"
  if [ -L "$link" ]; then
    if [ "$(readlink "$link")" = "$target" ]; then
      echo "  = $link (already linked)"
      return 0
    fi
    echo "  ~ $link (replacing link to $(readlink "$link"))"
    rm "$link"
  elif [ -e "$link" ]; then
    echo "  ! $link exists and is not a link, skipped (move it away and re-run)" >&2
    FAILED=1
    return 0
  fi
  ln -s "$target" "$link"
  echo "  + $link"
}

# Remove <dir>/<skill> only when it is a link to this repo's copy.
unlink_one() {
  local dir="$1" skill="$2" link="$1/$2"
  if [ "$(installed_in "$dir" "$skill")" = "yes" ]; then
    rm "$link"
    echo "  - $link"
  elif [ -e "$link" ] || [ -L "$link" ]; then
    echo "  ! $link is not a link to this repo, left alone" >&2
  else
    echo "  = $link (not installed)"
  fi
}

# Let the user pick by number or name; "a" picks all.
pick_skills() {
  if [ ! -t 0 ]; then
    echo "No skills named and no terminal to ask. Pass skill names or --all." >&2
    exit 1
  fi
  echo "Skills in this repo:"
  list_skills
  echo
  printf 'Pick skills (numbers or names, separated by spaces or commas; a = all): '
  local answer tok
  read -r answer
  answer="$(echo "$answer" | tr ',' ' ')"
  for tok in $answer; do
    if [ "$tok" = "a" ] || [ "$tok" = "all" ]; then
      SELECTED=("${ALL_SKILLS[@]}")
      return 0
    elif [[ "$tok" =~ ^[0-9]+$ ]] && [ "$tok" -ge 1 ] && [ "$tok" -le ${#ALL_SKILLS[@]} ]; then
      SELECTED+=("${ALL_SKILLS[$((tok - 1))]}")
    elif is_skill "$tok"; then
      SELECTED+=("$tok")
    else
      echo "Unknown choice: $tok" >&2
      exit 1
    fi
  done
}

ACTION=install
USE_CLAUDE=1
PICK_ALL=0
SELECTED=()
FAILED=0

while [ $# -gt 0 ]; do
  case "$1" in
    -a|--all) PICK_ALL=1 ;;
    -l|--list) ACTION=list ;;
    -u|--uninstall) ACTION=uninstall ;;
    --no-claude) USE_CLAUDE=0 ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
    *)
      if ! is_skill "$1"; then
        echo "Unknown skill: $1 (run ./install.sh --list)" >&2
        exit 1
      fi
      SELECTED+=("$1")
      ;;
  esac
  shift
done

if [ "$ACTION" = list ]; then
  list_skills
  exit 0
fi

if [ "$PICK_ALL" = 1 ]; then
  SELECTED=("${ALL_SKILLS[@]}")
elif [ ${#SELECTED[@]} -eq 0 ]; then
  pick_skills
fi
if [ ${#SELECTED[@]} -eq 0 ]; then
  echo "Nothing picked."
  exit 0
fi

# Drop duplicates while keeping order.
UNIQUE=()
for s in "${SELECTED[@]}"; do
  dup=0
  for u in ${UNIQUE[@]+"${UNIQUE[@]}"}; do [ "$u" = "$s" ] && dup=1; done
  [ "$dup" = 0 ] && UNIQUE+=("$s")
done

for s in "${UNIQUE[@]}"; do
  echo "$s"
  if [ "$ACTION" = uninstall ]; then
    unlink_one "$AGENTS_DIR" "$s"
    [ "$USE_CLAUDE" = 1 ] && unlink_one "$CLAUDE_DIR" "$s"
  else
    link_one "$AGENTS_DIR" "$s"
    [ "$USE_CLAUDE" = 1 ] && link_one "$CLAUDE_DIR" "$s"
  fi
done

if [ "$ACTION" = install ]; then
  echo
  echo "Done. Restart your agent tools to pick up new skills."
fi
exit "$FAILED"
