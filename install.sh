#!/bin/sh
set -eu

REPOSITORY="${PINGFLOW_REPOSITORY:-lostornot/pingflow-tcp}"
VERSION="${PINGFLOW_VERSION:-latest}"
INSTALL_DIR="${PINGFLOW_INSTALL_DIR:-/usr/local/bin}"
PROGRAM_URL_BASE="https://github.com/${REPOSITORY}/releases"
RUN_ONLY=0

if [ "${1:-}" = "--run" ]; then
    RUN_ONLY=1
    shift
fi

if [ -n "${PINGFLOW_DOWNLOAD_BASE:-}" ]; then
    DOWNLOAD_BASE="${PINGFLOW_DOWNLOAD_BASE}"
elif [ "$VERSION" = "latest" ]; then
    DOWNLOAD_BASE="${PROGRAM_URL_BASE}/latest/download"
else
    DOWNLOAD_BASE="${PROGRAM_URL_BASE}/download/${VERSION}"
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
        echo "pingflow installer: curl or wget is required" >&2
        exit 1
    fi
}

download "${DOWNLOAD_BASE}/pingflow" "${temporary_dir}/pingflow"
download "${DOWNLOAD_BASE}/SHA256SUMS" "${temporary_dir}/SHA256SUMS"

expected_checksum="$(awk '$2 == "pingflow" { print $1 }' "${temporary_dir}/SHA256SUMS")"
if [ -z "$expected_checksum" ]; then
    echo "pingflow installer: release checksum is missing" >&2
    exit 1
fi

if command -v sha256sum >/dev/null 2>&1; then
    actual_checksum="$(sha256sum "${temporary_dir}/pingflow" | awk '{ print $1 }')"
elif command -v shasum >/dev/null 2>&1; then
    actual_checksum="$(shasum -a 256 "${temporary_dir}/pingflow" | awk '{ print $1 }')"
else
    echo "pingflow installer: sha256sum or shasum is required" >&2
    exit 1
fi

if [ "$actual_checksum" != "$expected_checksum" ]; then
    echo "pingflow installer: checksum verification failed" >&2
    exit 1
fi

chmod 0755 "${temporary_dir}/pingflow"

if [ "$RUN_ONLY" -eq 1 ]; then
    if ! command -v python3 >/dev/null 2>&1; then
        echo "pingflow installer: python3 is required" >&2
        exit 1
    fi
    python3 "${temporary_dir}/pingflow" "$@"
    exit $?
fi

mkdir -p "$INSTALL_DIR"
install -m 0755 "${temporary_dir}/pingflow" "${INSTALL_DIR}/pingflow"

echo "PingFlow installed to ${INSTALL_DIR}/pingflow"
"${INSTALL_DIR}/pingflow" --version
