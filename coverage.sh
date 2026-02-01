#!/bin/bash

# --- Configurações ---
OUTPUT_DIR="coverage"
# Agora os arquivos intermediários ficarão DENTRO da pasta de output
INFO_FILE="$OUTPUT_DIR/coverage.info"
INFO_FILE_CLEAN="$OUTPUT_DIR/coverage_cleaned.info"

# Verifica se estamos na raiz do workspace
if [ ! -f "devel/setup.bash" ]; then
    echo "❌ Erro: Execute este script da raiz do seu workspace catkin."
    exit 1
fi

# Carrega o ambiente
source devel/setup.bash

# Cria a pasta de destino imediatamente para guardar a bagunça lá
mkdir -p "$OUTPUT_DIR"

echo "========================================="
echo "🧹 1. Zerando contadores anteriores..."
echo "========================================="
lcov --directory . --zerocounters --quiet

echo "========================================="
echo "🚀 2. Rodando os testes..."
echo "========================================="

if [ $# -eq 0 ]; then
    echo "⚠️  Nenhum comando passado. Rodando 'catkin_make run_tests'..."
    catkin_make run_tests
else
    echo "Executando: $@"
    "$@"
fi

# Captura erro do teste mas não para o script
TEST_EXIT_CODE=$?
if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo "⚠️  Os testes falharam. Gerando relatório para diagnóstico..."
fi

echo "========================================="
echo "📸 3. Capturando dados (Salvando em $OUTPUT_DIR)..."
echo "========================================="
# Gera o arquivo bruto JÁ dentro da pasta output
lcov --directory . --capture --output-file "$INFO_FILE" --rc lcov_branch_coverage=1

echo "========================================="
echo "🗑️  4. Filtrando arquivos..."
echo "========================================="
lcov --remove "$INFO_FILE" \
    '/usr/*' \
    '/opt/*' \
    '*/test/*' \
    '*/tests/*' \
    '*/build/*' \
    '*/devel/*' \
    '*/CMakeCCompilerId.c' \
    '*/CMakeCXXCompilerId.cpp' \
    --output-file "$INFO_FILE_CLEAN" \
    --rc lcov_branch_coverage=1

echo "========================================="
echo "📊 5. Gerando HTML..."
echo "========================================="
genhtml "$INFO_FILE_CLEAN" --output-directory "$OUTPUT_DIR" --rc lcov_branch_coverage=1 --legend

# --- LIMPEZA FINAL ---
# Remove os arquivos .info para deixar apenas o site HTML.
# Se quiser guardar os dados brutos para usar no Codecov/Sonar, comente as linhas abaixo.
echo "✨ Limpando arquivos temporários..."
rm "$INFO_FILE"
rm "$INFO_FILE_CLEAN"

echo ""
echo "✅ Concluído!"
echo "📄 Abra: $(pwd)/$OUTPUT_DIR/index.html"