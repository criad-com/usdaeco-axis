#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TOOLCHAIN_DIR="${TOOLCHAIN_DIR:-$HERE/../usdaeco-toolchain}"
CORE_DIR="${CORE_DIR:-$HERE/../usdaeco-core}"
bash "$TOOLCHAIN_DIR/build.sh" usdAecoAxis "$HERE" \
    --dep "${CORE_PLUGIN_DIR:-$CORE_DIR/out/plugins/usdAeco/resources}" "$@"
while (( $# )); do
    if [[ "$1" == "--install-root" ]]; then
        mkdir -p "$2/python"
        cp -RL "$HERE/tools/usdaeco_axis" "$2/python/"
        break
    fi
    shift
done
