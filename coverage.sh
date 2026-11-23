#!/bin/bash

# Guarda o status do comando e do tee separadamente: disco cheio pode impedir
# a gravação do log mesmo quando o comando termina com sucesso.
run_logged() {
    local logfile="$1"
    shift
    "$@" 2>&1 | tee "$logfile"
    local statuses=("${PIPESTATUS[@]}")
    COMMAND_EXIT_CODE=${statuses[0]}
    LOG_EXIT_CODE=${statuses[1]}
    if [ "$LOG_EXIT_CODE" -ne 0 ]; then
        echo "Erro ao gravar $logfile. Coleta interrompida." >&2
        return 1
    fi
    return "$COMMAND_EXIT_CODE"
}

# Vamos definir o binário principal e adicionar os outros como "objetos" extras
BIN_PATH="./devel/lib/component"
TARGET_BINARY="$BIN_PATH/g3t1_1"
OTHER_BINARIES="-object $BIN_PATH/g3t1_2 -object $BIN_PATH/g3t1_3 -object $BIN_PATH/g3t1_4 -object $BIN_PATH/g3t1_5 -object $BIN_PATH/g3t1_6 -object $BIN_PATH/g4t1 -object $BIN_PATH/patient_data_service"

# Binários do subsistema de adaptação/monitoramento, com contraparte no ROS2
# (adaptation.data_access/enactor/reli_engine, system_monitor.logger/param_adapter):
OTHER_BINARIES="$OTHER_BINARIES -object ./devel/lib/enactor/enactor"
OTHER_BINARIES="$OTHER_BINARIES -object ./devel/lib/adaptation_engine/reli_engine"
OTHER_BINARIES="$OTHER_BINARIES -object ./devel/lib/repository/data_access"
OTHER_BINARIES="$OTHER_BINARIES -object ./devel/lib/logging_infrastructure/logger"
OTHER_BINARIES="$OTHER_BINARIES -object ./devel/lib/effector/param_adapter"

# Demais nós: collector (contraparte ROS1 de system_monitor.node_monitor),
# cost_engine (irmão do reli_engine, sem port em adaptation ainda) e patient
# (simulador de paciente, separado de patient_data_service acima):
OTHER_BINARIES="$OTHER_BINARIES -object ./devel/lib/probe/collector"
OTHER_BINARIES="$OTHER_BINARIES -object ./devel/lib/adaptation_engine/cost_engine"
OTHER_BINARIES="$OTHER_BINARIES -object ./devel/lib/patient/patient"

# Verifica se estamos na raiz do workspace
if [ ! -f "devel/setup.bash" ]; then
    echo "❌ Erro: Execute este script da raiz do seu workspace catkin (onde fica a pasta devel)."
    exit 1
fi

# 1. Preparação do ambiente
# Cada tentativa conserva seus próprios artefatos, inclusive se falhar.
COVERAGE_ROOT="${BSN_COVERAGE_ROOT:-coverage_llm}"
mkdir -p "$COVERAGE_ROOT" || exit 1
BASE_DIR=$(mktemp -d "$COVERAGE_ROOT/run_$(date -u +%Y%m%dT%H%M%SZ)_XXXXXX") || exit 1
BASE_DIR=$(cd "$BASE_DIR" && pwd) || exit 1
DATA_DIR="$BASE_DIR/data"
HTML_DIR="$BASE_DIR/html"
PRODUCTION_HTML_DIR="$BASE_DIR/html_production"
PROFDATA_FILE="$BASE_DIR/merged.profdata"
LOG_DIR="$BASE_DIR/logs"
echo "📁 Diretório desta tentativa: $BASE_DIR"
mkdir -p "$DATA_DIR" "$LOG_DIR" || exit 1
source devel/setup.bash || exit 1

# Um marcador vazio pode restar de uma gravação interrompida. Não o corrige
# automaticamente: o estado da VM precisa ser examinado após liberar espaço.
if [ -f build/.built_by ] && [ ! -s build/.built_by ]; then
    echo "Erro: build/.built_by está vazio. Verifique o espaço e o estado do build antes de repetir." >&2
    exit 1
fi

# Sanity check: confirma que os 4 pacotes com testes novos (logger,
# param_adapter, data_access, enactor) estão no índice do rospack depois do
# `source devel/setup.bash` acima - se um deles não aparecer aqui, o
# catkin_make abaixo não vai nem tentar compilar/rodar o rostest dele,
# silenciosamente. Log salvo, não só no terminal, para conferir depois.
{
    echo "=== rospack find (pacotes com testes novos) ==="
    for pkg in logging_infrastructure effector repository enactor; do
        echo -n "$pkg: "
        rospack find "$pkg" 2>&1 || echo "NAO ENCONTRADO"
    done
} | tee "$LOG_DIR/rospack_check.log"
CHECK_STATUS=("${PIPESTATUS[@]}")
if [ "${CHECK_STATUS[1]}" -ne 0 ]; then
    echo "Erro ao gravar a checagem de pacotes; verifique o espaço disponível." >&2
    exit 1
fi

WORKSPACE_DIR=$(pwd -P)

# 2. Compilação com Clang e Flags de Cobertura
# Não trocar o compilador dentro de um cache configurado com outro compilador:
# o CMake pode reiniciar a configuração e perder o prefixo devel e as flags.
CLANG_C=$(command -v clang) || exit 1
CLANG_CXX=$(command -v clang++) || exit 1
# Preservar o nome do driver: clang++ pode ser um symlink para clang.
# Resolver esse symlink perde o modo C++ e a ligação automática de libstdc++.
BUILD_CMAKE_ARGS=(
    "-DCMAKE_C_COMPILER=$CLANG_C"
    "-DCMAKE_CXX_COMPILER=$CLANG_CXX"
    "-DCATKIN_DEVEL_PREFIX=$WORKSPACE_DIR/devel"
    "-DCMAKE_INSTALL_PREFIX=$WORKSPACE_DIR/install"
    "-DCATKIN_ENABLE_TESTING=ON"
    "-DCMAKE_CXX_FLAGS=-fprofile-instr-generate -fcoverage-mapping -O0 -fno-inline"
    "-DCMAKE_EXE_LINKER_FLAGS=-fprofile-instr-generate -fcoverage-mapping"
    "-DCMAKE_SHARED_LINKER_FLAGS=-fprofile-instr-generate -fcoverage-mapping"
)
CACHE_FILE=build/CMakeCache.txt
RESET_BUILD=0
if [ -f "$CACHE_FILE" ]; then
    OLD_C=$(sed -n 's/^CMAKE_C_COMPILER:FILEPATH=//p' "$CACHE_FILE")
    OLD_CXX=$(sed -n 's/^CMAKE_CXX_COMPILER:FILEPATH=//p' "$CACHE_FILE")
    OLD_DEVEL=$(sed -n 's/^CATKIN_DEVEL_PREFIX:PATH=//p' "$CACHE_FILE")
    if [ "$OLD_C" != "$CLANG_C" ] || \
       [ "$OLD_CXX" != "$CLANG_CXX" ] || \
       [ "$OLD_DEVEL" != "$WORKSPACE_DIR/devel" ]; then
        RESET_BUILD=1
    fi
fi
if [ "$RESET_BUILD" -eq 1 ]; then
    echo "Cache de compilador/prefixo incompatível. Preservando build e devel anteriores nesta tentativa."
    mv build "$BASE_DIR/previous_build" || exit 1
    if [ -e devel ]; then
        mv devel "$BASE_DIR/previous_devel" || exit 1
    fi
fi

echo "🛠️  Compilando com Clang e Instrumentation..."
# Sem cache, clean configuraria primeiro com o compilador padrão do sistema.
if [ -f build/CMakeCache.txt ]; then
    if ! run_logged "$LOG_DIR/clean.log" catkin_make clean "${BUILD_CMAKE_ARGS[@]}"; then
        echo "❌ Falha na preparação do build. Nenhum teste foi iniciado." >&2
        exit 1
    fi
fi
if ! run_logged "$LOG_DIR/build.log" catkin_make "${BUILD_CMAKE_ARGS[@]}"; then
    echo "❌ Construção ou registro do build falhou (comando=$COMMAND_EXIT_CODE, log=$LOG_EXIT_CODE)." >&2
    echo "   Nenhum teste foi iniciado. Veja $LOG_DIR/build.log." >&2
    exit 1
fi
# 2b. Validação do build (também usada ao reutilizar binários por feature).
# Confere os destinos antes de iniciar qualquer suíte.
ACTUAL_DEVEL=$(sed -n 's/^CATKIN_DEVEL_PREFIX:PATH=//p' build/CMakeCache.txt)
if [ "$ACTUAL_DEVEL" != "$WORKSPACE_DIR/devel" ]; then
    echo "❌ Prefixo inesperado no cache: $ACTUAL_DEVEL. Nenhum teste foi iniciado." >&2
    exit 1
fi
for setting in CMAKE_CXX_FLAGS CMAKE_EXE_LINKER_FLAGS; do
    if ! sed -n "s/^$setting:STRING=//p" build/CMakeCache.txt | grep -q -- '-fprofile-instr-generate'; then
        echo "❌ Flag de instrumentação ausente: $setting. Nenhum teste foi iniciado." >&2
        exit 1
    fi
done
COVERAGE_EXECUTABLES=("$TARGET_BINARY")
read -r -a EXTRA_OBJECTS <<< "$OTHER_BINARIES"
for ((i=1; i<${#EXTRA_OBJECTS[@]}; i+=2)); do
    COVERAGE_EXECUTABLES+=("${EXTRA_OBJECTS[i]}")
done
for binary in "${COVERAGE_EXECUTABLES[@]}"; do
    if [ ! -x "$binary" ]; then
        echo "❌ Executável ausente em devel: $binary. Nenhum teste foi iniciado." >&2
        exit 1
    fi
done
source devel/setup.bash || exit 1

# O runner fonte usa /usr/bin/env python. Disponibiliza explicitamente o
# pacote local e valida também o interpretador selecionado pelo catkin.
ROS_PYTEST_SOURCE="$WORKSPACE_DIR/src/ros_pytest/src"
if [ ! -f "$ROS_PYTEST_SOURCE/ros_pytest/__init__.py" ]; then
    echo "❌ Módulo ros_pytest ausente em $ROS_PYTEST_SOURCE." >&2
    exit 1
fi
export PYTHONPATH="$ROS_PYTEST_SOURCE${PYTHONPATH:+:$PYTHONPATH}"
RUNNER_PYTHON=$(command -v python) || exit 1
CATKIN_PYTHON=$(sed -n 's/^PYTHON_EXECUTABLE:FILEPATH=//p' build/CMakeCache.txt)
if [ -z "$CATKIN_PYTHON" ]; then
    echo "❌ PYTHON_EXECUTABLE não encontrado no cache CMake." >&2
    exit 1
fi
for interpreter in "$RUNNER_PYTHON" "$CATKIN_PYTHON"; do
    if ! run_logged "$LOG_DIR/python_import_$(basename "$interpreter").log" \
        "$interpreter" -c 'import sys; print("Python: " + sys.executable); from ros_pytest import run_pytest; import ros_pytest, pytest, rospy, pytest_bdd; print("ros_pytest: " + ros_pytest.__file__)'; then
        echo "❌ Importação das dependências de teste falhou em $interpreter. Nenhum teste foi iniciado." >&2
        exit 1
    fi
done

# 3. Configuração da variável de ambiente para os dados brutos
# O %p garante que cada processo (nó ROS) gere seu próprio arquivo sem sobrescrever
export LLVM_PROFILE_FILE="$DATA_DIR/coverage_%p.profraw"
export ROS_TEST_RESULTS_DIR="$WORKSPACE_DIR/build/test_results"

# XML de uma execução anterior não pode entrar no resumo da nova tentativa.
if [ -e build/test_results ]; then
    mv build/test_results "$BASE_DIR/previous_test_results" || exit 1
fi
mkdir -p build/test_results || exit 1

# 4. Execução dos testes
# Saída completa salva em log (o terminal trunca/rola e é fácil perder a
# parte que diz quais rostest efetivamente rodaram) - manda pra cá qualquer
# arquivo de $LOG_DIR se algo não bater com o esperado.
echo "🚀 Executando testes..."
run_logged "$LOG_DIR/test_output.log" catkin_make run_tests "${BUILD_CMAKE_ARGS[@]}"
TEST_EXIT_CODE=$COMMAND_EXIT_CODE
if [ "$LOG_EXIT_CODE" -ne 0 ]; then
    exit 1
fi
# Conserva resultados parciais quando houver falhas, mas nunca resume XML antigo.
cp -a build/test_results "$BASE_DIR/test_results" || exit 1
if ! find build/test_results -type f -name '*.xml' -print -quit | grep -q .; then
    echo "❌ Nenhum XML novo foi produzido. A tentativa não fornece resultados de testes." >&2
    exit 1
fi

# Resumo por pacote (inclui logger/param_adapter/data_access/enactor se os
# .xml de resultado desses rostest novos foram gerados em build/test_results).
# Também serve para confirmar rapidamente se os 4 suites novos aparecem aqui
# ou não - se um pacote não aparece nessa lista, o teste dele não rodou.
echo "📋 Resumo por pacote..."
if command -v catkin_test_results >/dev/null 2>&1; then
    run_logged "$LOG_DIR/test_results_summary.log" catkin_test_results build
    RESULTS_EXIT_CODE=$COMMAND_EXIT_CODE
    if [ "$LOG_EXIT_CODE" -ne 0 ]; then
        exit 1
    fi
else
    RESULTS_EXIT_CODE=0
    echo "catkin_test_results não encontrado - listando os XML novos."
    if ! run_logged "$LOG_DIR/test_results_summary.log" find build/test_results -name '*.xml'; then
        exit 1
    fi
fi

# Resumo alternativo, lendo todo *.xml em build/test_results/ diretamente
# (não depende do catkin_test_results, que só reconhece o padrão de nome
# "rosunit-*.xml" e ignora "rostest-*.xml" - alguns rostest de node só geram
# esse segundo padrão, e catkin_test_results acima simplesmente omite o
# pacote inteiro do resumo dele nesse caso, sem erro nenhum). Este aqui lê
# qualquer nome de arquivo, então nada passa despercebido.
#
# Cuidado: quando um rostest lança um script rosunit/pytest (test_*.launch
# rodando test/unit/test_X.py ou test/test_bdd/test_X.py), o rostest GERA OS
# DOIS arquivos para a mesma execução: "rostest-*.xml" (um wrapper com um
# unico testcase classname="rostest.runner.RosTest", so' confirma que o
# processo do roslaunch terminou, sem refletir falhas internas do pytest -
# confirmado comparando enactor: rosunit diz failures="1", o rostest
# equivalente diz failures="0" pro mesmo run) e "rosunit-*.xml" (o detalhe
# real, um testcase por teste). Somar os dois contaria a mesma execucao duas
# vezes. Quando o rostest roda um unittest.TestCase direto (sem pytest por
# baixo, ex: os antigos test_G3T1_*.launch), so' existe o wrapper mesmo - af
# ele e' o unico registro e deve ser contado.
#
# A deteccao abaixo: um arquivo "rostest-*.xml" com testsuite de 1 unico
# testcase classname="rostest.runner.RosTest" e' tratado como wrapper; seu
# nome (sem o prefixo "rostest-" e sem prefixos tipo "test_unit_test_"/
# "test_test_bdd_test_") e' comparado (case-insensitive, sem "_"/"-") com o
# nome de cada "rosunit-*.xml" no mesmo diretorio (sem o prefixo "rosunit-"
# e sem um "test_" inicial). Se bater, o wrapper e' um duplicado do rosunit
# e e' pulado na soma; se nao bater (G3T1_*), o wrapper e' contado normal.
{
    echo "=== Resumo bruto de todo build/test_results/**/*.xml ==="
    python3 - <<'PYEOF'
import glob
import os
import xml.etree.ElementTree as ET

ROSTEST_PREFIXES = (
    "test_unit_test_",
    "test_test_bdd_test_",
    "test_bdd_test_",
    "unit_test_",
    "test_",
)
ROSUNIT_PREFIXES = ("test_",)


def core_name(basename, prefixes):
    for prefix in prefixes:
        if basename.startswith(prefix):
            basename = basename[len(prefix):]
            break
    return basename.lower().replace("_", "").replace("-", "")


def parse_counts(path):
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        return None, f"{path}: ERRO AO LER XML ({e})"
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    total = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    testcases = []
    for suite in suites:
        for k in total:
            total[k] += int(suite.get(k, 0))
        testcases.extend(suite.findall("testcase"))
    return (total, testcases), None


all_paths = sorted(glob.glob("build/test_results/**/*.xml", recursive=True))
by_dir = {}
for path in all_paths:
    by_dir.setdefault(os.path.dirname(path), []).append(path)

grand_total = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
xml_read_errors = 0

for dirpath in sorted(by_dir):
    rosunit_cores = set()
    for path in by_dir[dirpath]:
        base = os.path.basename(path)
        if base.startswith("rosunit-"):
            name = base[len("rosunit-"):-len(".xml")]
            rosunit_cores.add(core_name(name, ROSUNIT_PREFIXES))

    for path in by_dir[dirpath]:
        result, err = parse_counts(path)
        if err:
            print(err)
            xml_read_errors += 1
            continue
        counts, testcases = result
        base = os.path.basename(path)

        is_wrapper = (
            base.startswith("rostest-")
            and len(testcases) == 1
            and testcases[0].get("classname") == "rostest.runner.RosTest"
        )
        if is_wrapper:
            name = base[len("rostest-"):-len(".xml")]
            # test_target_system.launch names its internal runner sensor_test.
            wrapper_core = core_name(name, ROSTEST_PREFIXES)
            internal_core = {"targetsystem": "sensortest"}.get(wrapper_core, wrapper_core)
            if internal_core in rosunit_cores:
                print(f"{path}: PULADO (wrapper duplicado de um rosunit-*.xml no mesmo diretorio)")
                continue

        for k in grand_total:
            grand_total[k] += counts[k]
        print(f"{path}: {counts['tests']} tests, {counts['errors']} errors, "
              f"{counts['failures']} failures, {counts['skipped']} skipped")

print(f"\nTOTAL: {grand_total['tests']} tests, {grand_total['errors']} errors, "
      f"{grand_total['failures']} failures, {grand_total['skipped']} skipped")
if xml_read_errors or not grand_total['tests']:
    raise SystemExit(2)
if grand_total['failures'] or grand_total['errors']:
    raise SystemExit(1)
PYEOF
} | tee "$LOG_DIR/test_results_summary_raw.log"
SUMMARY_STATUS=("${PIPESTATUS[@]}")
if [ "${SUMMARY_STATUS[0]}" -gt 1 ] || [ "${SUMMARY_STATUS[1]}" -ne 0 ]; then
    echo "Erro ao gerar ou gravar o resumo dos testes." >&2
    exit 1
fi
if [ "${SUMMARY_STATUS[0]}" -ne 0 ]; then
    RESULTS_EXIT_CODE=${SUMMARY_STATUS[0]}
fi

# 5. Processamento dos dados (Merge)
echo "🧬 Mesclando arquivos .profraw..."
shopt -s nullglob
PROFILE_FILES=("$DATA_DIR"/coverage_*.profraw)
shopt -u nullglob
if [ "${#PROFILE_FILES[@]}" -gt 0 ]; then
    if ! run_logged "$LOG_DIR/merge.log" llvm-profdata merge -sparse "${PROFILE_FILES[@]}" -o "$PROFDATA_FILE"; then
        echo "❌ Falha na mesclagem dos perfis de cobertura." >&2
        exit 1
    fi
else
    echo "❌ Erro: Nenhum arquivo .profraw foi gerado. Verifique se os testes rodaram corretamente."
    exit 1
fi

# 6. Relatórios bruto e de produção (mesmos perfis e objetos).
# Bibliotecas próprias também contêm mapeamentos de cobertura; passar somente
# executáveis omitia suas implementações do relatório.
PROJECT_LIBRARIES=(./devel/lib/liblibbsn.so ./devel/lib/libarchlib.so)
LIBRARY_OBJECTS=()
for library in "${PROJECT_LIBRARIES[@]}"; do
    if [ ! -f "$library" ]; then
        echo "❌ Biblioteca própria ausente da cobertura: $library" >&2
        exit 1
    fi
    LIBRARY_OBJECTS+=(-object "$library")
done

# Seleção positiva de fontes, compatível com llvm-cov 6 (argumentos SOURCES).
# Dependências externas, build/devel e auxiliares de teste ficam fora por regra
# de escopo, nunca pelo percentual obtido. CostEngine permanece incluído.
PRODUCTION_SOURCE_LIST="$BASE_DIR/production_sources.txt"
if ! find "$(pwd)/src/sa-bsn" "$(pwd)/src/libbsn" "$(pwd)/src/archlib" \
    -type d \( -name test -o -name tests \) -prune -o \
    -type f \( -name '*.cpp' -o -name '*.cc' -o -name '*.cxx' \
               -o -name '*.c' -o -name '*.h' -o -name '*.hpp' \
               -o -name '*.hh' -o -name '*.hxx' -o -name '*.inl' \) \
    -print > "$PRODUCTION_SOURCE_LIST"; then
    echo "❌ Falha ao selecionar fontes de produção." >&2
    exit 1
fi
LC_ALL=C sort -o "$PRODUCTION_SOURCE_LIST" "$PRODUCTION_SOURCE_LIST" || exit 1
mapfile -t PRODUCTION_SOURCES < "$PRODUCTION_SOURCE_LIST"
if [ "${#PRODUCTION_SOURCES[@]}" -eq 0 ]; then
    echo "❌ Nenhuma fonte selecionada; relatório sem filtro não será usado como produção." >&2
    exit 1
fi

echo "📊 Gerando relatório bruto de cobertura..."

if ! run_logged "$LOG_DIR/report.log" llvm-cov show "$TARGET_BINARY" $OTHER_BINARIES \
    "${LIBRARY_OBJECTS[@]}" \
    -instr-profile="$PROFDATA_FILE" \
    -format=html \
    -output-dir="$HTML_DIR" \
    -show-line-counts-or-regions; then
    echo "❌ Falha na geração do relatório HTML." >&2
    exit 1
fi

echo "📊 Gerando relatório de cobertura do código de produção..."
if ! run_logged "$LOG_DIR/report_production.log" llvm-cov show "$TARGET_BINARY" $OTHER_BINARIES \
    "${LIBRARY_OBJECTS[@]}" \
    -instr-profile="$PROFDATA_FILE" \
    -format=html \
    -output-dir="$PRODUCTION_HTML_DIR" \
    -show-line-counts-or-regions "${PRODUCTION_SOURCES[@]}"; then
    echo "❌ Falha na geração do relatório de produção." >&2
    exit 1
fi

# 7. Resumo no terminal
echo "------------------------------------------------"
echo "✅ Relatório de cobertura gerado; confira os resultados dos testes."
echo "📂 Dados brutos: $DATA_DIR"
echo "📈 Relatório consolidado: $PROFDATA_FILE"
echo "🌐 Relatório HTML bruto: $HTML_DIR/index.html"
echo "🌐 Relatório HTML de produção: $PRODUCTION_HTML_DIR/index.html"
echo "📄 Fontes selecionadas para produção: $PRODUCTION_SOURCE_LIST"
echo "📝 Logs completos (incluindo avisos LLVM): $LOG_DIR/"
echo "------------------------------------------------"

if [ "$TEST_EXIT_CODE" -ne 0 ] || [ "$RESULTS_EXIT_CODE" -ne 0 ]; then
    echo "⚠️  Execução ou resultados indicam falha (execução=$TEST_EXIT_CODE, resultados=$RESULTS_EXIT_CODE). Cobertura pode ser parcial."
    echo "   Para ver quais pacotes/suites rodaram: $LOG_DIR/test_results_summary.log"
    echo "   Para a saída completa (inclui rostest): $LOG_DIR/test_output.log"
    exit 1
fi
