#!/usr/bin/env bash
set -euo pipefail

# ————————————————————————————————————————————————
# Configurable via env vars:
#   VERSION      -> which mediapipe version to fetch (default: latest)
#   DOWNLOAD_DIR -> where to stash original wheels
#   OUTPUT_DIR   -> where to put patched wheels
#   TMP_DIR      -> temp space for unpacking
#————————————————————————————————————————————————
VERSION="${VERSION:-latest}"
DOWNLOAD_DIR="${DOWNLOAD_DIR:-./downloaded_wheels}"
OUTPUT_DIR="${OUTPUT_DIR:-./patched_wheels}"
TMP_DIR="${TMP_DIR:-./_tmp_wheel_unpack}"

# Ensure we have wheel tooling
ensure_deps() {
  if ! python3 -c "import wheel, setuptools, requests, rich" &>/dev/null; then
    echo "Installing wheel, setuptools, requests and rich..."
    pip install wheel setuptools requests rich
  fi
  if ! command -v unzip &>/dev/null; then
    echo "Error: unzip is required but not found in PATH." >&2
    exit 1
  fi
}

# Fetch all .whl for mediapipe@$VERSION (all platforms)
download_wheels() {
  mkdir -p "$DOWNLOAD_DIR"
  echo "Downloading all wheels for mediapipe==${VERSION} into $DOWNLOAD_DIR..."
  python3 download_wheels.py "$VERSION" "$DOWNLOAD_DIR"
}

# Given one wheel file, unpack, patch metadata, and repack
process_wheel() {
  local wheel="$1"
  echo "-> Processing $(basename "$wheel")"

  # clean temp
  rm -rf "$TMP_DIR"
  mkdir -p "$TMP_DIR"

  # derive original suffix from wheel filename, e.g.
  # mediapipe-0.10.21-cp310-cp310-macosx_11_0_universal2 → 0.10.21-cp310-cp310-macosx_11_0_universal2
  local base="$(basename "$wheel" .whl)"
  local suffix="${base#mediapipe-}"

  # unpack
  local unpack_dir="$TMP_DIR/$base"
  mkdir -p "$unpack_dir"
  unzip -qq "$wheel" -d "$unpack_dir"

  # locate & rename the .dist-info directory
  local distinfo
  distinfo=$(find "$unpack_dir" -maxdepth 1 -type d -name "mediapipe-*.dist-info" | head -1)
  if [[ -z "$distinfo" ]]; then
    echo "ERROR: cannot find .dist-info for $wheel" >&2
    return 1
  fi
  # extract version and rename dist-info folder
  local ver="${distinfo##*/mediapipe-}"
  ver="${ver%.dist-info}"
  local new_distinfo="$unpack_dir/mediapipe_numpy2-${ver}.dist-info"
  mv "$distinfo" "$new_distinfo"
  local meta="$new_distinfo/METADATA"

  # remove numpy<2, ensure plain numpy, patch Name and Home-page
  sed '/^Requires-Dist: numpy<2$/d' "$meta" > "$meta.tmp" && mv "$meta.tmp" "$meta"
  if ! grep -q '^Requires-Dist: numpy$' "$meta"; then
    echo "Requires-Dist: numpy" >> "$meta"
  fi
  sed -i.bak \
    -e 's/^Name: mediapipe$/Name: mediapipe-numpy2/' \
    -e 's|^Home-page: .*|Home-page: https://github.com/cansik/mediapipe-numpy2|' \
    "$meta"
  rm -f "$meta.bak"

  # repack into a dedicated temp directory
  local pack_dir="$TMP_DIR/pack"
  rm -rf "$pack_dir"
  mkdir -p "$pack_dir"
  python3 -m wheel pack "$unpack_dir" -d "$pack_dir"

  # move the rebuilt wheel into OUTPUT_DIR, using the original suffix
  local built=("$pack_dir"/*.whl)
  if [[ ${#built[@]} -ne 1 ]]; then
    echo "ERROR: expected exactly one rebuilt wheel in $pack_dir but found ${#built[@]}" >&2
    return 1
  fi

  mkdir -p "$OUTPUT_DIR"
  mv "${built[0]}" "$OUTPUT_DIR/mediapipe_numpy2-${suffix}.whl"
}

main() {
  ensure_deps
  download_wheels

  mkdir -p "$OUTPUT_DIR"
  for whl in "$DOWNLOAD_DIR"/*.whl; do
    process_wheel "$whl"
  done

  echo ""
  echo "Done. Patched wheels are in $OUTPUT_DIR/"
}

main "$@"
