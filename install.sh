#!/bin/sh
# Install or update si.
#   curl -fsSL https://raw.githubusercontent.com/Jonathansl17/si/main/install.sh | sh
# Overrides: SI_REPO, SI_REF, SI_HOME (install dir), SI_BIN_DIR (symlink dir).
set -eu

SI_REPO="${SI_REPO:-Jonathansl17/si}"
SI_REF="${SI_REF:-main}"
SI_HOME="${SI_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/si}"
SI_BIN_DIR="${SI_BIN_DIR:-$HOME/.local/bin}"
ARCHIVE_URL="https://github.com/${SI_REPO}/archive/refs/heads/${SI_REF}.tar.gz"
MIN_PYTHON="3.10"

die() { printf 'si install: %s\n' "$1" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "$1 is required"; }

need python3
need curl
need tar
python3 -c "import sys; sys.exit(sys.version_info < tuple(map(int, '$MIN_PYTHON'.split('.'))))" \
  || die "python3 >= $MIN_PYTHON is required"
command -v fzf >/dev/null 2>&1 \
  || printf 'si install: warning: fzf not found; interactive mode needs it (si -y works without it)\n' >&2

staging=$(mktemp -d)
trap 'rm -rf "$staging"' EXIT INT TERM

printf 'Downloading %s@%s...\n' "$SI_REPO" "$SI_REF"
curl -fsSL "$ARCHIVE_URL" | tar -xz -C "$staging" --strip-components=1
[ -f "$staging/bin/si" ] || die "downloaded archive does not contain bin/si"

# Replace the previous install atomically enough for a single-user tool.
mkdir -p "$(dirname "$SI_HOME")" "$SI_BIN_DIR"
rm -rf "$SI_HOME.old"
[ -d "$SI_HOME" ] && mv "$SI_HOME" "$SI_HOME.old"
mv "$staging" "$SI_HOME"
rm -rf "$SI_HOME.old"
trap - EXIT INT TERM

chmod +x "$SI_HOME/bin/si"
ln -sf "$SI_HOME/bin/si" "$SI_BIN_DIR/si"
printf 'Installed si to %s (command: %s/si)\n' "$SI_HOME" "$SI_BIN_DIR"

case ":$PATH:" in
  *":$SI_BIN_DIR:"*) ;;
  *) printf 'Add %s to your PATH to run si.\n' "$SI_BIN_DIR" ;;
esac
