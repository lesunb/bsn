#!/bin/bash

# --- Configurações de Caminhos ---
# --- Configurações de Caminhos ---
BASE_DIR="coverage"
DATA_DIR="$BASE_DIR/data"
HTML_DIR="$BASE_DIR/html"
PROFDATA_FILE="$BASE_DIR/merged.profdata"

# Vamos definir o binário principal e adicionar os outros como "objetos" extras
BIN_PATH="./devel/lib/component"
TARGET_BINARY="$BIN_PATH/g3t1_1"
OTHER_BINARIES="-object $BIN_PATH/g3t1_2 -object $BIN_PATH/g3t1_3 -object $BIN_PATH/g3t1_4 -object $BIN_PATH/g3t1_5 -object $BIN_PATH/g3t1_6 -object $BIN_PATH/g4t1 -object $BIN_PATH/patient_data_service"

# Verifica se estamos na raiz do workspace
if [ ! -f "devel/setup.bash" ]; then
    echo "❌ Erro: Execute este script da raiz do seu workspace catkin (onde fica a pasta devel)."
    exit 1
fi

# 1. Preparação do ambiente
echo "🧹 Limpando dados antigos e criando diretórios..."
rm -rf "$BASE_DIR"
mkdir -p "$DATA_DIR"
source devel/setup.bash

# 2. Compilação com Clang e Flags de Cobertura
# Passamos as flags diretamente no comando para não precisar alterar o CMakeLists.txt permanentemente
echo "🛠️  Compilando com Clang e Instrumentation..."
catkin_make clean
catkin_make -DCMAKE_CXX_COMPILER=clang++ \
            -DCMAKE_C_COMPILER=clang \
            -DCMAKE_CXX_FLAGS="-fprofile-instr-generate -fcoverage-mapping -O0 -fno-inline" \
            -DCMAKE_EXE_LINKER_FLAGS="-fprofile-instr-generate -fcoverage-mapping"

# 3. Configuração da variável de ambiente para os dados brutos
# O %p garante que cada processo (nó ROS) gere seu próprio arquivo sem sobrescrever
export LLVM_PROFILE_FILE="$(pwd)/$DATA_DIR/coverage_%p.profraw"

# 4. Execução dos testes
echo "🚀 Executando testes..."
catkin_make run_tests
TEST_EXIT_CODE=$?

# 5. Processamento dos dados (Merge)
echo "🧬 Mesclando arquivos .profraw..."
if ls $DATA_DIR/*.profraw 1> /dev/null 2>&1; then
    llvm-profdata merge -sparse $DATA_DIR/coverage_*.profraw -o "$PROFDATA_FILE"
else
    echo "❌ Erro: Nenhum arquivo .profraw foi gerado. Verifique se os testes rodaram corretamente."
    exit 1
fi

# 6. Geração do Relatório HTML
echo "📊 Gerando relatório de cobertura limpo..."

# O ignore-filename-regex bane tudo o que estiver em /opt/, /usr/ e pastas devel
llvm-cov show "$TARGET_BINARY" $OTHER_BINARIES \
    -instr-profile="$PROFDATA_FILE" \
    -format=html \
    -output-dir="$HTML_DIR" \
    -show-line-counts-or-regions \

# 7. Resumo no terminal
echo "------------------------------------------------"
echo "✅ Processo concluído!"
echo "📂 Dados brutos: $DATA_DIR"
echo "📈 Relatório consolidado: $PROFDATA_FILE"
echo "🌐 Relatório HTML: $(pwd)/$HTML_DIR/index.html"
echo "------------------------------------------------"

if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo "⚠️  Nota: Alguns testes falharam (Exit Code: $TEST_EXIT_CODE), mas o relatório foi gerado com os dados coletados."
fi