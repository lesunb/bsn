#!/usr/bin/env bash
# Examina perfis existentes. Não recompila, não executa testes e não altera o HTML.
set -euo pipefail
if [ "$#" -ne 1 ]; then
    echo "Uso: bash $0 CAMINHO_DA_COLETA" >&2
    exit 2
fi
RUN_DIR=$(cd -- "$1" && pwd)
WORKSPACE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
LLVM_COV=${LLVM_COV:-llvm-cov}
LLVM_PROFDATA=${LLVM_PROFDATA:-llvm-profdata}
command -v "$LLVM_COV" >/dev/null
command -v "$LLVM_PROFDATA" >/dev/null
PROFILE="$RUN_DIR/merged.profdata"
test -f "$PROFILE"
cd "$WORKSPACE"
OBJECTS=(
    devel/lib/component/g3t1_1 devel/lib/component/g3t1_2
    devel/lib/component/g3t1_3 devel/lib/component/g3t1_4
    devel/lib/component/g3t1_5 devel/lib/component/g3t1_6
    devel/lib/component/g4t1 devel/lib/component/patient_data_service
    devel/lib/enactor/enactor devel/lib/adaptation_engine/reli_engine
    devel/lib/repository/data_access devel/lib/logging_infrastructure/logger
    devel/lib/effector/param_adapter devel/lib/probe/collector
    devel/lib/adaptation_engine/cost_engine devel/lib/patient/patient
    devel/lib/liblibbsn.so devel/lib/libarchlib.so
)
for object in "${OBJECTS[@]}"; do
    if [ ! -f "$object" ]; then
        echo "Objeto ausente: $object. Use o ambiente e os binários da coleta." >&2
        exit 1
    fi
done
DIAG=$(mktemp -d "$RUN_DIR/diagnostic_XXXXXX")
echo "Diagnóstico: $DIAG"
echo "Os objetos atuais precisam corresponder aos usados na coleta. Não recompile antes do diagnóstico."
{
    "$LLVM_COV" --version || true
    # LLVM 6 exige um subcomando antes das opções de llvm-profdata.
    # A consulta de metadados não deve interromper o diagnóstico dos objetos.
    if ! "$LLVM_PROFDATA" --version; then
        "$LLVM_PROFDATA" show --version || true
    fi
    if command -v clang++ >/dev/null; then clang++ --version || true; fi
} > "$DIAG/versions.txt" 2>&1
sha256sum "$PROFILE" "${OBJECTS[@]}" > "$DIAG/artifacts.sha256"
printf 'object\texit_code\n' > "$DIAG/status.tsv"
EXTRA_OBJECTS=()
for object in "${OBJECTS[@]:1}"; do EXTRA_OBJECTS+=(-object "$object"); done
failed=0
# -dump expõe os diagnósticos de incompatibilidade sem suprimir o aviso.
code=0
echo "Analisando o conjunto de objetos..."
"$LLVM_COV" report -dump "${OBJECTS[0]}" "${EXTRA_OBJECTS[@]}" \
    -instr-profile="$PROFILE" > "$DIAG/combined.txt" 2> "$DIAG/combined_errors.log" || code=$?
printf 'combined\t%s\n' "$code" >> "$DIAG/status.tsv"
if [ "$code" -ne 0 ]; then failed=1; fi
for index in "${!OBJECTS[@]}"; do
    object=${OBJECTS[$index]}
    name="${index}_$(basename -- "$object")"
    echo "Analisando $object..."
    code=0
    "$LLVM_COV" report -dump "$object" -instr-profile="$PROFILE" \
        > "$DIAG/$name.txt" 2> "$DIAG/${name}_errors.log" || code=$?
    printf '%s\t%s\n' "$object" "$code" >> "$DIAG/status.tsv"
    if [ "$code" -ne 0 ]; then failed=1; fi
done
echo "Confira combined_errors.log, os logs por objeto, versions.txt e artifacts.sha256."
echo "Código zero significa comando concluído; avisos de mismatch ainda exigem análise."
exit "$failed"
