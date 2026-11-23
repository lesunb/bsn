#!/usr/bin/env bash

set -e
set -o pipefail

# Executar a partir da raiz deste workspace, inclusive quando chamado de fora.
WORKSPACE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
cd "$WORKSPACE_DIR"
ROS_SETUP=${BSN_ROS1_SETUP:-/opt/ros/melodic/setup.bash}
if [ ! -f "$ROS_SETUP" ]; then
    echo "Ambiente ROS 1 não encontrado: $ROS_SETUP" >&2
    exit 1
fi
source "$ROS_SETUP"
command -v catkin_make >/dev/null
CLANG_C=$(command -v clang)
CLANG_CXX=$(command -v clang++)
# Não resolver symlinks: o nome clang++ seleciona o driver C++.

# Conservar os binários, cache e XML antigos antes de preparar um build novo.
mkdir -p build_preparation
RUN_DIR=$(mktemp -d "$WORKSPACE_DIR/build_preparation/run_$(date -u +%Y%m%dT%H%M%SZ)_XXXXXX")
echo "Registro desta preparação: $RUN_DIR"
for directory in build devel; do
    if [ -e "$directory" ] || [ -L "$directory" ]; then
        mv "$directory" "$RUN_DIR/previous_$directory"
    fi
done

if ! catkin_make \
    -DCMAKE_BUILD_TYPE=Debug \
    -DCMAKE_C_COMPILER="$CLANG_C" \
    -DCMAKE_CXX_COMPILER="$CLANG_CXX" \
    -DCATKIN_DEVEL_PREFIX="$WORKSPACE_DIR/devel" \
    -DCMAKE_INSTALL_PREFIX="$WORKSPACE_DIR/install" \
    -DCATKIN_ENABLE_TESTING=ON \
    -DCMAKE_CXX_FLAGS="-fprofile-instr-generate -fcoverage-mapping -O0 -fno-inline" \
    -DCMAKE_EXE_LINKER_FLAGS="-fprofile-instr-generate -fcoverage-mapping" \
    -DCMAKE_SHARED_LINKER_FLAGS="-fprofile-instr-generate -fcoverage-mapping" \
    2>&1 | tee "$RUN_DIR/build.log"; then
    echo "A preparação falhou. Consulte $RUN_DIR/build.log; os diretórios anteriores foram preservados." >&2
    exit 1
fi
source devel/setup.bash

echo "Build Clang concluído. Para carregar o ambiente no terminal atual:"
printf 'source %q\n' "$WORKSPACE_DIR/devel/setup.bash"
