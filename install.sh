#!/usr/bin/env bash
# pysuwi installer.
#   curl -fsSL https://raw.githubusercontent.com/shamekhing/pysuwi/main/install.sh | bash
#   bash install.sh --uninstall            # keeps your plugins
#   bash install.sh --uninstall --purge    # removes everything
# Pin a release with: PYSUWI_REF=v1.1.0 bash install.sh
set -euo pipefail

REPO_URL="${PYSUWI_REPO:-https://github.com/shamekhing/pysuwi.git}"
REF="${PYSUWI_REF:-main}"
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
if [[ -e "$SRC_DIR" || -L "$SRC_DIR" ]]; then
    die "$SRC_DIR already exists; use 'pysuwi update' or uninstall before reinstalling (existing files were not changed)"
fi

mkdir -p "$HOME_DIR/commands" "$HOME/.local/bin" "$(dirname "$COMP_FILE")"

git clone --quiet --depth 1 --branch "$REF" "$REPO_URL" "$SRC_DIR" \
    || die "could not clone $REPO_URL at $REF"

chmod 755 "$SRC_DIR/pysuwi.py"
ln -sfn "$SRC_DIR/pysuwi.py" "$BIN_LINK"
cp "$SRC_DIR/completion/pysuwi.bash" "$COMP_FILE"

echo "pysuwi installed ($REF) to $SRC_DIR"
echo
case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) echo "note: ~/.local/bin is not on PATH. Open a new login shell." ;;
esac
for pkg in python3-markdown python3-weasyprint; do
    dpkg -s "$pkg" >/dev/null 2>&1 || echo "note: md2pdf needs: sudo apt install $pkg"
done
echo "bash: open a new shell, or run: source $COMP_FILE"
echo "zsh:  add to ~/.zshrc:"
echo "        autoload -Uz compinit bashcompinit && compinit && bashcompinit"
echo "        source $COMP_FILE"
echo
"$BIN_LINK" doctor || true
