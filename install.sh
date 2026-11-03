#!/usr/bin/env bash
# pysuwi installer.
#   PYSUWI_REF=<reviewed-commit-sha> bash install.sh
#   bash install.sh --uninstall            # keeps your plugins
#   bash install.sh --uninstall --purge    # removes everything
#   PYSUWI_REF must be the full SHA of a reviewed commit.
set -euo pipefail

REPO_URL="${PYSUWI_REPO:-https://github.com/shamekhing/pysuwi.git}"
REF="${PYSUWI_REF:-}"
HOME_DIR="$HOME/.pysuwi"
SRC_DIR="$HOME_DIR/src"
BIN_LINK="$HOME/.local/bin/pysuwi"
COMP_FILE="$HOME/.local/share/bash-completion/completions/pysuwi"

die() { echo "pysuwi install: $*" >&2; exit 4; }

if [[ "${1:-}" == "--uninstall" ]]; then
    rm -f "$BIN_LINK" "$COMP_FILE"
    rm -rf "$SRC_DIR"
    if [[ "${2:-}" == "--purge" ]]; then
        rm -rf "$HOME_DIR"
        echo "pysuwi removed, including your plugins in $HOME_DIR/commands."
    else
        rmdir "$HOME_DIR" 2>/dev/null || true
        echo "pysuwi removed. Your plugins in $HOME_DIR/commands were kept (use --purge to delete)."
    fi
    exit 0
fi

command -v git >/dev/null || die "git is required (sudo apt install git)"
command -v python3 >/dev/null || die "python3 is required"
python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))' || die "Python 3.9+ required"

[[ -n "$REPO_URL" ]] || die "PYSUWI_REPO must not be empty"
[[ "$REF" =~ ^[[:xdigit:]]{40}$ ]] \
    || die "set PYSUWI_REF to the full 40-character SHA of a reviewed commit"
if [[ -e "$SRC_DIR" || -L "$SRC_DIR" ]]; then
    die "$SRC_DIR already exists; use 'pysuwi update' or uninstall before reinstalling (existing files were not changed)"
fi

mkdir -p "$HOME_DIR/commands" "$HOME/.local/bin" "$(dirname "$COMP_FILE")"

git init --quiet "$SRC_DIR"
git -C "$SRC_DIR" remote add origin "$REPO_URL"
git -C "$SRC_DIR" fetch --quiet origin main \
    || die "could not fetch the main branch from $REPO_URL"
git -C "$SRC_DIR" cat-file -e "${REF}^{commit}" \
    || die "reviewed commit $REF is not available on the fetched main branch"
git -C "$SRC_DIR" merge-base --is-ancestor "$REF" origin/main \
    || die "reviewed commit must be on the main branch"
git -C "$SRC_DIR" checkout --quiet -b pysuwi "$REF"
ACTUAL_REF="$(git -C "$SRC_DIR" rev-parse HEAD)"
[[ "${ACTUAL_REF,,}" == "${REF,,}" ]] || die "fetched commit did not match $REF"
git -C "$SRC_DIR" branch --quiet --set-upstream-to=origin/main pysuwi

chmod 755 "$SRC_DIR/pysuwi.py"
ln -sfn "$SRC_DIR/pysuwi.py" "$BIN_LINK"
cp "$SRC_DIR/completion/pysuwi.bash" "$COMP_FILE"

echo "pysuwi installed ($REF) to $SRC_DIR"
echo
case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) echo "note: ~/.local/bin is not on PATH. Open a new login shell." ;;
esac
if command -v dpkg >/dev/null; then
    for pkg in python3-markdown python3-weasyprint; do
        dpkg -s "$pkg" >/dev/null 2>&1 || echo "note: md2pdf needs: sudo apt install $pkg"
    done
else
    echo "note: md2pdf needs markdown and weasyprint in the active Python environment"
fi
echo "bash: open a new shell, or run: source $COMP_FILE"
echo "zsh:  add to ~/.zshrc:"
echo "        autoload -Uz compinit bashcompinit && compinit && bashcompinit"
echo "        source $COMP_FILE"
echo
echo "Run 'pysuwi doctor' after installation to check the setup."
