# Escopo dos relatórios de cobertura ROS 1

Execute `bash coverage.sh` na raiz deste workspace catkin, no ambiente ROS 1.
Cada nova coleta em `coverage_llm/run_*` gera dois relatórios com os mesmos
perfis e objetos:

- `html/index.html`: cobertura bruta, incluindo dependências e arquivos gerados
  presentes nos mapeamentos dos objetos fornecidos ao LLVM.
- `html_production/index.html`: cobertura das fontes próprias C/C++ de
  `src/sa-bsn`, `src/libbsn` e `src/archlib`, excluindo diretórios `test` e `tests`.
  Cabeçalhos próprios permanecem incluídos. Dependências externas, código
  gerado de `build`/`devel` e auxiliares dentro das pastas de teste ficam fora.

`production_sources.txt` registra a seleção de fontes em cada coleta. O LLVM
exibe as fontes selecionadas que possuem mapeamento nos objetos fornecidos;
essa lista não garante que todo arquivo selecionado tenha sido instrumentado.
Arquivos sem execução, mas com mapeamento de cobertura, continuam no relatório.
Não há exclusão por baixa cobertura: `CostEngine.cpp` permanece selecionado.

O script fornece também `liblibbsn.so` e `libarchlib.so` ao LLVM, para incluir
os mapeamentos das bibliotecas próprias antes ausentes. Isso altera o denominador
inclusive do relatório bruto em relação às coletas anteriores. Não interpretar
uma mudança percentual como melhora ou piora dos testes sem considerar esse escopo.

A seleção usa os argumentos `SOURCES` de `llvm-cov show`, documentados no
[LLVM 6](https://releases.llvm.org/6.0.0/docs/CommandGuide/llvm-cov.html#show-command).
O filtro atua na apresentação e no total do relatório selecionado; não remove
testes nem modifica a instrumentação ou os perfis brutos.

Os relatórios históricos permanecem inalterados. O novo percentual exige gerar
o relatório com ferramentas, fontes, perfis e objetos correspondentes à coleta.
Avisos como `functions have mismatched data` permanecem nos logs `report.log`
e `report_production.log` e precisam ser investigados independentemente do filtro.
O relatório de produção não constitui, por si só, prova de ausência de regressões.

## Diagnóstico de funções com dados incompatíveis

No ambiente ROS 1, com os binários da coleta ainda presentes, execute a partir
da raiz deste workspace catkin:

```bash
bash diagnose_coverage.sh coverage_llm/run_20260928T015653Z_iY2pcY
```

O script cria `diagnostic_*` dentro da coleta, registra versões e hashes e
executa `llvm-cov report -dump` para o conjunto e para cada objeto. Não recompila
nem repete os testes. Os arquivos `*_errors.log` permitem identificar nomes e
hashes envolvidos conforme os diagnósticos da versão LLVM utilizada. Se os
binários já foram recompilados, use cópias preservadas da campanha ou faça uma
nova coleta identificada; misturar objetos atuais e perfis antigos prejudica o
diagnóstico. Os hashes registrados agora não provam identidade histórica.

O aviso não indica 36 testes reprovados nem 36 regressões. Entre as hipóteses a
investigar estão divergência entre binários e perfis e variantes de funções
compartilhadas entre objetos. Não foi confirmada a causa deste caso. O modo de
diagnóstico é ilustrado em um [registro do projeto LLVM](https://github.com/llvm/llvm-project/issues/32849).

Na coleta de 28/09, o diagnóstico `diagnostic_e1VWBH` de 01/10 identificou
18 funções de metadados de serviços gerados, uma função de serialização ROS e
17 funções de Lepton. Todas estão fora da seleção de produção; as métricas dos
46 arquivos selecionados coincidem com as do HTML anterior. Ver o
[parecer do diagnóstico](../tg/revisoes/diagnostico_mismatch_ros1_2026-10-01.md).
Essa localização delimita o alcance das entradas reportadas, sem confirmar a
causa raiz ou garantir a completude de todos os perfis.
