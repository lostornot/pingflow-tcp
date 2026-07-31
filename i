#!/bin/sh
set -eu

DOWNLOAD_BASE="${PINGFLOW_CDN_BASE:-https://cdn.jsdelivr.net/gh/lostornot/pingflow-tcp@v0.2.0}"
EXPECTED_SHA256="0391b3168ff0ca0dd07861e1b095d669578bf151515e99caaecab3d6c7a28bc3"

if [ "${1:-}" = "--run" ]; then
    shift
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "pingflow CDN runner: python3 is required" >&2
    exit 1
fi

temporary_dir="$(mktemp -d)"
trap 'rm -rf "$temporary_dir"' EXIT HUP INT TERM

download() {
    source_url="$1"
    destination="$2"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$source_url" -o "$destination"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "$destination" "$source_url"
    else
        echo "pingflow CDN runner: curl or wget is required" >&2
        exit 1
    fi
}

download "${DOWNLOAD_BASE}/pingflow" "${temporary_dir}/pingflow"

if command -v sha256sum >/dev/null 2>&1; then
    actual_checksum="$(sha256sum "${temporary_dir}/pingflow" | awk '{ print $1 }')"
elif command -v shasum >/dev/null 2>&1; then
    actual_checksum="$(shasum -a 256 "${temporary_dir}/pingflow" | awk '{ print $1 }')"
else
    echo "pingflow CDN runner: sha256sum or shasum is required" >&2
    exit 1
fi

if [ "$actual_checksum" != "$EXPECTED_SHA256" ]; then
    echo "pingflow CDN runner: checksum verification failed" >&2
    exit 1
fi

exec 3<"${temporary_dir}/pingflow"
rm -rf "$temporary_dir"
trap - EXIT HUP INT TERM
exec python3 - "$@" <&3
