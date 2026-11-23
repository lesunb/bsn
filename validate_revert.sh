#!/bin/bash
#
# Roda um grupo de rostests e grava tudo em revert_validation/<label>/ para
# analise posterior (log do rostest, log dos nos, xml de resultado, resumo).
#
# Uso (da raiz do workspace catkin, onde ficam devel/ e build/):
#   ./validate_revert.sh <label> <grupo> [--no-build]
#
#   label : nome desta rodada, ex. R0-baseline, R1-ros-ok, R2-return ...
#   grupo : engine  -> suites que sobem o reli_engine real (injector,
#                      managing_system, target_system, check_bsn)
#           sensor  -> todas as suites do pacote component (unit G3T1/G4T1,
#                      connected, sensor_core e todos os BDD)
#           all     -> tudo que esta registrado com add_rostest
#
# Faz `catkin_make clean` + `catkin_make` no inicio (rebuild completo a cada
# rodada; --no-build pula). As flags de cobertura (clang) continuam no CMakeCache.

WS="$(cd "$(dirname "$0")" && pwd)"
LABEL="$1"
GROUP="$2"
BUILD=1
[ "$3" = "--no-build" ] && BUILD=0

if [ -z "$LABEL" ] || [ -z "$GROUP" ]; then
    sed -n '2,17p' "$0"
    exit 2
fi

cd "$WS" || exit 1
if [ ! -f devel/setup.bash ]; then
    echo "Erro: rode da raiz do workspace catkin (onde fica devel/)."
    exit 1
fi

OUT="$WS/revert_validation/$LABEL"
if [ -e "$OUT" ]; then
    echo "Erro: $OUT ja existe. Use outro label ou apague o diretorio."
    exit 1
fi
mkdir -p "$OUT/results" "$OUT/roslog" "$OUT/profraw"

if pgrep -x rosmaster >/dev/null; then
    echo "Erro: ja existe um rosmaster rodando. Encerre-o antes (o rostest sobe o proprio master)."
    exit 1
fi

# Build limpo antes de carregar o ambiente (pulado com --no-build).
# O CMakeCache nao e' apagado pelo clean, entao as flags de cobertura (clang)
# continuam valendo no catkin_make seguinte.
if [ "$BUILD" -eq 1 ]; then
    echo "==> catkin_make clean"
    catkin_make clean 2>&1 | tee "$OUT/clean.log"
    echo "==> catkin_make"
    catkin_make 2>&1 | tee "$OUT/build_clean.log"
    if [ "${PIPESTATUS[0]}" -ne 0 ]; then
        echo "BUILD FALHOU - veja $OUT/build_clean.log"
        exit 1
    fi
fi

# A ordem importa: o setup do ROS primeiro, o overlay do workspace por ultimo.
# Com `devel/setup.bash` antes, o `/opt/ros/melodic/setup.bash` reescreve o
# ROS_PACKAGE_PATH sem o workspace e o rostest nao acha nenhum pacote do bsn2
# (rospkg.common.ResourceNotFound: repository).
source /opt/ros/melodic/setup.bash && source devel/setup.bash

# Falha rapido se o workspace nao esta no ROS_PACKAGE_PATH, em vez de deixar
# todas as suites morrerem em 1 s.
if ! rospack find repository >/dev/null 2>&1; then
    echo "Erro: 'rospack find repository' falhou - o workspace nao esta no ROS_PACKAGE_PATH."
    echo "ROS_PACKAGE_PATH=$ROS_PACKAGE_PATH"
    exit 1
fi

COMP=src/sa-bsn/target_system/components/component/test
case "$GROUP" in
    engine)
        LAUNCHES="$COMP/test_bdd/test_injector.launch
$COMP/test_bdd/test_managing_system.launch
$COMP/test_bdd/test_target_system.launch
$COMP/test_bdd/test_check_bsn.launch"
        ;;
    sensor)
        LAUNCHES="$(ls $COMP/test_bdd/test_*.launch $COMP/unit/test_*.launch)"
        ;;
    all)
        LAUNCHES="$(ls $COMP/test_bdd/test_*.launch $COMP/unit/test_*.launch \
                    src/sa-bsn/system_manager/enactor/test/unit/test_*.launch \
                    src/sa-bsn/logging_infrastructure/logger/test/unit/test_*.launch \
                    src/sa-bsn/knowledge_repository/data_access/test/unit/test_*.launch \
                    src/sa-bsn/target_system/effectors/param_adapter/test/unit/test_*.launch)"
        ;;
    *)
        echo "Grupo invalido: $GROUP (engine|sensor|all)"
        exit 2
        ;;
esac

{
    echo "label : $LABEL"
    echo "grupo : $GROUP"
    echo "data  : $(date -Is)"
    echo "--- estado dos 3 arquivos de producao (md5) ---"
    md5sum src/sa-bsn/system_manager/adaptation_engine/src/Engine.cpp \
           src/sa-bsn/system_manager/adaptation_engine/src/ReliabilityEngine.cpp \
           src/libbsn/src/configuration/SensorConfiguration.cpp
    echo "--- diff contra a versao corrigida (backup) ---"
    for pair in "src/sa-bsn/system_manager/adaptation_engine/src/Engine.cpp:Engine.cpp.fixed" \
                "src/sa-bsn/system_manager/adaptation_engine/src/ReliabilityEngine.cpp:ReliabilityEngine.cpp.fixed" \
                "src/libbsn/src/configuration/SensorConfiguration.cpp:SensorConfiguration.cpp.fixed"; do
        diff -u "$WS/../bsn2_fixed_backup/${pair#*:}" "${pair%%:*}"
    done
} > "$OUT/state.txt" 2>&1

# 1. Build incremental (com as flags de cobertura ja configuradas)
if [ "$BUILD" -eq 1 ]; then
    echo "==> catkin_make (incremental)"
    catkin_make 2>&1 | tee "$OUT/build.log"
    if [ "${PIPESTATUS[0]}" -ne 0 ]; then
        echo "BUILD FALHOU - veja $OUT/build.log"
        exit 1
    fi
    catkin_make tests 2>&1 | tee "$OUT/build_tests.log" >/dev/null
fi

# Perfil de cobertura fora do coverage_llm/ para nao contaminar aquele relatorio
export LLVM_PROFILE_FILE="$OUT/profraw/%p.profraw"

# 2. Um rostest por launch, sequencial
: > "$OUT/summary.txt"
for f in $LAUNCHES; do
    name="$(basename "$f" .launch)"
    pkgdir="$(dirname "$f")"
    while [ ! -f "$pkgdir/package.xml" ] && [ "$pkgdir" != "." ] && [ "$pkgdir" != "/" ]; do
        pkgdir="$(dirname "$pkgdir")"
    done
    pkg="$(sed -n 's:.*<name>\(.*\)</name>.*:\1:p' "$pkgdir/package.xml" | head -1)"

    mkdir -p "$OUT/roslog/$name"
    echo "==> $name (pkg=$pkg)"
    start=$(date +%s)
    ROS_LOG_DIR="$OUT/roslog/$name" timeout 900 rostest \
        --pkgdir="$WS/$pkgdir" --package="$pkg" \
        --results-filename "$name.xml" --results-base-dir "$OUT/results" \
        "$WS/$f" > "$OUT/$name.log" 2>&1
    rc=$?
    dur=$(( $(date +%s) - start ))

    passed=$(grep -c '\]\[passed\]' "$OUT/$name.log")
    # o pytest imprime [FAILURE] (e nao [FAILED]); conta os dois
    failed=$(grep -c '\]\[\(FAILED\|FAILURE\)\]' "$OUT/$name.log")
    # nos que sobreviveram ao encerramento do roslaunch (diagnostico do
    # laco `while (ros::ok)` do Engine) - depois mata para nao contaminar a proxima
    # (ancorado no inicio da linha de comando: sem o "^" o pgrep casava com o
    # proprio sed, que carrega o caminho do workspace, e acusava falso positivo)
    leftover="$(pgrep -af "^$WS/devel/lib/" | sed "s:$WS/devel/lib/::")"
    if [ -n "$leftover" ]; then
        pkill -9 -f "^$WS/devel/lib/"
    fi
    # nos que o roslaunch teve que escalar para SIGTERM/SIGKILL no encerramento
    escalated="$(grep -rh "escalating" "$OUT/roslog/$name" 2>/dev/null | sed 's/.*\] *//' | sort | uniq | tr '\n' ';')"
    line="$(printf '%-34s rc=%-3s %4ss  passed=%-3s FAILED=%-3s' "$name" "$rc" "$dur" "$passed" "$failed")"
    [ -n "$leftover" ] && line="$line  LEFTOVER-PROCS"
    [ -n "$escalated" ] && line="$line  ESCALATED: $escalated"
    echo "$line" | tee -a "$OUT/summary.txt"
    [ -n "$leftover" ] && echo "$leftover" > "$OUT/$name.leftover.txt"

    # Motivo da falha: sem isso o resumo so mostra "rc=1 passed=0 FAILED=0" e
    # nao diz se foi timeout, cenario reprovado, no que morreu ou rostest que
    # nem subiu. Tudo abaixo vem dos logs e e' impresso no terminal e no summary.
    if [ "$rc" -ne 0 ] || [ "$failed" -gt 0 ]; then
        {
            grep -a -o 'max time \[[^]]*\] allotted for test \[[^]]*\]' "$OUT/$name.log" | head -1 \
                | sed 's/^/      TIMEOUT do rostest: /'
            grep -a 'ResourceNotFound' "$OUT/$name.log" | head -1 | sed 's/^/      ROSTEST NAO SUBIU: /'
            # nos que morreram durante o teste (exit code negativo = sinal; -4 = SIGILL, -11 = SIGSEGV)
            grep -rha 'process has died' "$OUT/roslog/$name" 2>/dev/null  \
                | grep -av '\[test_' \
                | sed 's/.*\(\[[^]]*\] process has died \[pid [0-9]*, exit code [-0-9]*\).*/      NO MORREU: \1]/' | sort -u
            sed 's/\x1b\[[0-9;]*m//g' "$OUT/$name.log" | sed -n 's/^\[\(.*\)\]\[FAILURE\]$/      CENARIO REPROVADO: \1/p'
            sed 's/\x1b\[[0-9;]*m//g' "$OUT/$name.log" | grep -a 'AssertionError' | sed 's/^E *//' \
                | cut -c1-220 | sort -u | head -6 | sed 's/^/      /'
            sed 's/\x1b\[[0-9;]*m//g' "$OUT/$name.log" | grep -a '^\[ERROR\]' \
                | grep -v 'Failed to disconnect from effector' | head -4 | sed 's/^/      /'
        } | tee -a "$OUT/summary.txt"
    fi
    # o rostest as vezes deixa um master orfao se morreu no timeout
    pkill -9 -x rosmaster 2>/dev/null
    pkill -9 -x roscore 2>/dev/null
done

echo
echo "Resumo:  $OUT/summary.txt"
echo "Logs:    $OUT/<launch>.log   (rostest)   $OUT/roslog/<launch>/   (nos)"
