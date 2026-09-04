#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import tomllib


MAX_KWIN_DESKTOP_SHORTCUTS = 25


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(
        description="Generate a zsh script that applies Plasma desktops from an AeroSpace config."
    )
    parser.add_argument(
        "config",
        nargs="?",
        default=script_dir / "aerospace.toml",
        type=Path,
        help="Path to aerospace.toml",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default=script_dir / "generate_plasma_desktops.zsh",
        type=Path,
        help="Path to the generated zsh script",
    )
    return parser.parse_args()


def plasma_shortcut_for_aerospace_binding(binding: str) -> str:
    plasma_parts: list[str] = []

    for part in binding.split("-"):
        if part == "alt":
            plasma_parts.append("Meta")
        elif part == "cmd":
            plasma_parts.append("Alt")
        elif part == "ctrl":
            plasma_parts.append("Ctrl")
        elif part == "shift":
            plasma_parts.append("Shift")
        elif part == "esc":
            plasma_parts.append("Esc")
        elif len(part) == 1 and part.isdigit():
            plasma_parts.append(part)
        elif len(part) == 1 and part.isalpha() and part.islower():
            plasma_parts.append(part.upper())
        elif len(part) > 1 and part[0].lower() == "f" and part[1:].isdigit():
            plasma_parts.append(f"F{part[1:]}")
        else:
            raise ValueError(f"Unsupported AeroSpace workspace binding: {binding}")

    return "+".join(plasma_parts)


def load_main_bindings(config_path: Path) -> dict[str, object]:
    with config_path.open("rb") as handle:
        config = tomllib.load(handle)

    try:
        bindings = config["mode"]["main"]["binding"]
    except KeyError as exc:
        raise ValueError(f"Missing [mode.main.binding] in {config_path}") from exc

    if not isinstance(bindings, dict):
        raise ValueError(f"Expected [mode.main.binding] to be a table in {config_path}")

    return bindings


def extract_workspace_data(bindings: dict[str, object]) -> tuple[list[str], list[str], dict[int, str]]:
    desktops: list[str] = []
    switch_shortcuts: list[str] = []
    seen_workspaces: set[str] = set()
    move_shortcuts_by_workspace: dict[str, str] = {}

    for binding_key, command in bindings.items():
        if not isinstance(command, str):
            continue

        if command.startswith("workspace "):
            workspace_name = command.removeprefix("workspace ")
            if workspace_name in seen_workspaces:
                continue

            desktops.append(workspace_name)
            switch_shortcuts.append(plasma_shortcut_for_aerospace_binding(binding_key))
            seen_workspaces.add(workspace_name)
            continue

        if command.startswith("move-node-to-workspace "):
            workspace_name = command.removeprefix("move-node-to-workspace ")
            move_shortcuts_by_workspace[workspace_name] = plasma_shortcut_for_aerospace_binding(binding_key)

    if not desktops:
        raise ValueError("No workspace bindings found in [mode.main.binding]")

    if len(desktops) > MAX_KWIN_DESKTOP_SHORTCUTS:
        raise ValueError(
            f"KWin only exposes {MAX_KWIN_DESKTOP_SHORTCUTS} direct desktop shortcut actions; got {len(desktops)} workspaces"
        )

    workspace_index_by_name = {workspace_name: index for index, workspace_name in enumerate(desktops, start=1)}
    move_shortcuts_by_index: dict[int, str] = {}

    for workspace_name, shortcut in move_shortcuts_by_workspace.items():
        if workspace_name not in workspace_index_by_name:
            raise ValueError(f"Move binding references unknown workspace: {workspace_name}")

        move_shortcuts_by_index[workspace_index_by_name[workspace_name]] = shortcut

    return desktops, switch_shortcuts, move_shortcuts_by_index


def zsh_quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def render_zsh_array(name: str, values: list[str]) -> str:
    lines = [f"typeset -ra {name}=("]
    for value in values:
        lines.append(f"  {zsh_quote(value)}")
    lines.append(")")
    return "\n".join(lines)


def render_zsh_assoc(name: str, values: dict[int, str]) -> str:
    lines = [f"typeset -A {name}=("]
    for key in sorted(values):
        lines.append(f"  {key} {zsh_quote(values[key])}")
    lines.append(")")
    return "\n".join(lines)


def render_zsh_script(desktops: list[str], switch_shortcuts: list[str], move_shortcuts_by_index: dict[int, str]) -> str:
    desktop_names_block = render_zsh_array("DESKTOP_NAMES", desktops)
    switch_shortcuts_block = render_zsh_array("SWITCH_SHORTCUTS", switch_shortcuts)
    move_shortcuts_block = render_zsh_assoc("MOVE_SHORTCUTS_BY_DESKTOP", move_shortcuts_by_index)

    template = r"""#!/usr/bin/env zsh

# Generated by generate_plasma_desktops.py from aerospace.toml.
# Do not edit this file by hand.

set -euo pipefail

typeset -r KWIN_SERVICE='org.kde.KWin'
typeset -r KWIN_VDM_PATH='/VirtualDesktopManager'
typeset -r KWIN_VDM_IFACE='org.kde.KWin.VirtualDesktopManager'
typeset -r KGLOBALSHORTCUTS_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/kglobalshortcutsrc"
typeset -r MAX_KWIN_DESKTOP_SHORTCUTS=25

__DESKTOP_NAMES_BLOCK__

__SWITCH_SHORTCUTS_BLOCK__

__MOVE_SHORTCUTS_BLOCK__

usage() {
  print -u2 -- "Usage: ${0:t} [--apply]"
}

apply=0
case "${1:-}" in
  --apply)
    apply=1
    shift
    ;;
  -h|--help)
    usage
    exit 0
    ;;
esac

if (( $# > 0 )); then
  usage
  exit 1
fi

if ! command -v qdbus6 >/dev/null 2>&1; then
  print -u2 -- "Missing required command: qdbus6"
  exit 1
fi

if ! command -v kwriteconfig6 >/dev/null 2>&1; then
  print -u2 -- "Missing required command: kwriteconfig6"
  exit 1
fi

emit_or_run() {
  local quoted_command
  quoted_command="${(j: :)${(@q)@}}"

  if (( apply )); then
    print -u2 -- "$quoted_command"
    "$@"
  else
    print -r -- "$quoted_command"
  fi
}

build_group_args() {
  local group

  typeset -ga current_group_args
  current_group_args=()

  for group in "${current_groups[@]}"; do
    current_group_args+=(--group "$group")
  done
}

parse_config_groups() {
  local group_line="$1"
  local remainder="$group_line"

  typeset -ga current_groups
  current_groups=()

  while [[ "$remainder" == \[* ]]; do
    remainder="${remainder#\[}"
    current_groups+=("${remainder%%]*}")
    remainder="${remainder#*]}"
  done
}

clear_conflicting_shortcuts() {
  local action
  local active_shortcuts
  local default_shortcuts
  local description
  local line
  local new_active_shortcuts
  local remainder
  local shortcut
  local removed_any
  local tab=$'\t'
  local top_group
  local value
  local -a active_parts filtered_parts

  current_groups=()

  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" == \[* ]]; then
      parse_config_groups "$line"
      continue
    fi

    if [[ "$line" != *=* || ${#current_groups} == 0 ]]; then
      continue
    fi

    action="${line%%=*}"
    value="${line#*=}"
    remainder="${value#*,}"
    if [[ "$remainder" == "$value" ]]; then
      continue
    fi

    top_group="${current_groups[1]}"
    if [[ "$top_group" == 'kwin' && ( "$action" == 'Switch to Desktop '* || "$action" == 'Window to Desktop '* ) ]]; then
      continue
    fi

    active_shortcuts="${value%%,*}"
    default_shortcuts="${remainder%%,*}"
    description="${remainder#*,}"

    if [[ -z "$active_shortcuts" || "$active_shortcuts" == 'none' ]]; then
      continue
    fi

    active_parts=()
    filtered_parts=()
    removed_any=0

    if [[ "$active_shortcuts" == *$'\t'* ]]; then
      active_parts=("${(@s:$tab:)active_shortcuts}")
    else
      active_parts=("$active_shortcuts")
    fi

    for shortcut in "${active_parts[@]}"; do
      if (( ${+desired_shortcut_lookup[$shortcut]} )); then
        removed_any=1
      else
        filtered_parts+=("$shortcut")
      fi
    done

    if (( ! removed_any )); then
      continue
    fi

    if (( ${#filtered_parts} > 0 )); then
      new_active_shortcuts="${(j:$tab:)filtered_parts}"
    elif [[ -n "$default_shortcuts" ]]; then
      new_active_shortcuts='none'
    else
      new_active_shortcuts=''
    fi

    build_group_args
    emit_or_run kwriteconfig6 --file "$KGLOBALSHORTCUTS_FILE" "${current_group_args[@]}" --key "$action" "${new_active_shortcuts},${default_shortcuts},${description}"
  done < "$KGLOBALSHORTCUTS_FILE"
}

read_current_desktop_ids() {
  local desktops_literal
  local double_quote='"'
  local field
  local i
  local remainder

  desktops_literal="$(qdbus6 --literal "$KWIN_SERVICE" "$KWIN_VDM_PATH" desktops)"

  typeset -ga current_desktop_ids
  typeset -a quoted_fields
  current_desktop_ids=()
  quoted_fields=()

  while [[ "$desktops_literal" == *$double_quote* ]]; do
    remainder="${desktops_literal#*$double_quote}"
    field="${remainder%%$double_quote*}"
    quoted_fields+=("$field")
    desktops_literal="${remainder#*$double_quote}"
  done

  for (( i = 1; i <= ${#quoted_fields}; i += 2 )); do
    current_desktop_ids+=("${quoted_fields[i]}")
  done
}

typeset -gA desired_shortcut_lookup
desired_shortcut_lookup=()

for shortcut in "${SWITCH_SHORTCUTS[@]}" "${(@v)MOVE_SHORTCUTS_BY_DESKTOP}"; do
  if [[ -n "$shortcut" ]]; then
    desired_shortcut_lookup[$shortcut]=1
  fi
done

desired_count=${#DESKTOP_NAMES}

if (( desired_count > MAX_KWIN_DESKTOP_SHORTCUTS )); then
  print -u2 -- "KWin only exposes $MAX_KWIN_DESKTOP_SHORTCUTS direct desktop shortcut actions; got $desired_count workspaces"
  exit 1
fi

read_current_desktop_ids
current_count=${#current_desktop_ids}

if (( current_count < 1 )); then
  print -u2 -- 'KWin did not report any existing virtual desktops'
  exit 1
fi

for (( i = current_count; i >= 2; --i )); do
  emit_or_run qdbus6 "$KWIN_SERVICE" "$KWIN_VDM_PATH" "$KWIN_VDM_IFACE.removeDesktop" "${current_desktop_ids[i]}"
done

emit_or_run qdbus6 "$KWIN_SERVICE" "$KWIN_VDM_PATH" "$KWIN_VDM_IFACE.setDesktopName" "${current_desktop_ids[1]}" "${DESKTOP_NAMES[1]}"

for (( i = 2; i <= desired_count; ++i )); do
  emit_or_run qdbus6 "$KWIN_SERVICE" "$KWIN_VDM_PATH" "$KWIN_VDM_IFACE.createDesktop" "$(( i - 1 ))" "${DESKTOP_NAMES[i]}"
done

clear_conflicting_shortcuts

for (( i = 1; i <= MAX_KWIN_DESKTOP_SHORTCUTS; ++i )); do
  emit_or_run kwriteconfig6 --file "$KGLOBALSHORTCUTS_FILE" --group kwin --key "Switch to Desktop $i" ",,Switch to Desktop $i"
done

for (( i = 1; i <= desired_count; ++i )); do
  emit_or_run kwriteconfig6 --file "$KGLOBALSHORTCUTS_FILE" --group kwin --key "Switch to Desktop $i" "${SWITCH_SHORTCUTS[i]},,Switch to Desktop $i"
done

for (( i = 1; i <= MAX_KWIN_DESKTOP_SHORTCUTS; ++i )); do
  emit_or_run kwriteconfig6 --file "$KGLOBALSHORTCUTS_FILE" --group kwin --key "Window to Desktop $i" ",,Window to Desktop $i"
done

for (( i = 1; i <= desired_count; ++i )); do
  if [[ -n "${MOVE_SHORTCUTS_BY_DESKTOP[$i]-}" ]]; then
    emit_or_run kwriteconfig6 --file "$KGLOBALSHORTCUTS_FILE" --group kwin --key "Window to Desktop $i" "${MOVE_SHORTCUTS_BY_DESKTOP[$i]},,Window to Desktop $i"
  fi
done

emit_or_run qdbus6 "$KWIN_SERVICE" /KWin org.kde.KWin.reconfigure
"""

    return (
        template.replace("__DESKTOP_NAMES_BLOCK__", desktop_names_block)
        .replace("__SWITCH_SHORTCUTS_BLOCK__", switch_shortcuts_block)
        .replace("__MOVE_SHORTCUTS_BLOCK__", move_shortcuts_block)
    )


def main() -> int:
    args = parse_args()
    desktops, switch_shortcuts, move_shortcuts_by_index = extract_workspace_data(load_main_bindings(args.config))
    script = render_zsh_script(desktops, switch_shortcuts, move_shortcuts_by_index)

    args.output.write_text(script, encoding="utf-8")
    args.output.chmod(0o755)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
