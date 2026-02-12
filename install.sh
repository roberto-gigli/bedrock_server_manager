#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="$(pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir)
      INSTALL_DIR="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--dir <path>]"
      exit 1
      ;;
  esac
done

ensure_repo() {
  local use_zip=0

  is_empty_dir() {
    [[ -d "$1" ]] && [[ -z "$(ls -A "$1")" ]]
  }

  looks_like_repo() {
    [[ -f "$1/bedrock_server_manager.py" ]] && [[ -f "$1/README.md" ]]
  }

  if [[ -d "$INSTALL_DIR" ]]; then
    if [[ -d "$INSTALL_DIR/.git" ]]; then
      echo "Updating existing repo in $INSTALL_DIR..."
      git -C "$INSTALL_DIR" pull --ff-only
      return
    fi
    if ! is_empty_dir "$INSTALL_DIR"; then
      use_zip=1
    fi
  fi

  if [[ $use_zip -eq 0 ]] && command -v git >/dev/null 2>&1; then
    echo "Cloning repo into $INSTALL_DIR..."
    git clone "https://github.com/roberto-gigli/bedrock_server_manager.git" "$INSTALL_DIR"
    return
  fi

  echo "Git not found, downloading ZIP..."
  ZIP_URL="https://github.com/roberto-gigli/bedrock_server_manager/archive/refs/heads/main.zip"
  TMP_ZIP="$(mktemp -t bedrock_server_manager.XXXXXX).zip"

  if command -v curl >/dev/null 2>&1; then
    curl -L "$ZIP_URL" -o "$TMP_ZIP"
  elif command -v wget >/dev/null 2>&1; then
    wget -O "$TMP_ZIP" "$ZIP_URL"
  else
    echo "Need curl or wget to download the ZIP."
    exit 1
  fi

  TMP_DIR="$(mktemp -d -t bedrock_server_manager.XXXXXX)"
  unzip -q "$TMP_ZIP" -d "$TMP_DIR"
  if [[ -d "$INSTALL_DIR" ]]; then
    shopt -s dotglob
    mv "$TMP_DIR/bedrock_server_manager-main/"* "$INSTALL_DIR/"
    shopt -u dotglob
    rmdir "$TMP_DIR/bedrock_server_manager-main"
  else
    mv "$TMP_DIR/bedrock_server_manager-main" "$INSTALL_DIR"
  fi
  rm -f "$TMP_ZIP"
  rmdir "$TMP_DIR"
}

add_to_path() {
  local line="export PATH=\"$INSTALL_DIR:\$PATH\""
  local updated=0

  for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [[ -f "$rc" ]]; then
      if ! grep -Fq "$line" "$rc"; then
        echo "$line" >> "$rc"
        updated=1
      fi
    fi
  done

  if [[ $updated -eq 1 ]]; then
    echo "Added $INSTALL_DIR to PATH in shell rc files."
    echo "Restart your terminal or run: $line"
  else
    echo "PATH already configured or no rc files found."
  fi
}

make_executable() {
  local files=("$INSTALL_DIR/bedrock_server_manager.sh")
  for file in "${files[@]}"; do
    if [[ -f "$file" ]]; then
      chmod +x "$file"
    fi
  done
}

ensure_repo
make_executable
add_to_path

echo "Done. You can run: bedrock_server_manager"
