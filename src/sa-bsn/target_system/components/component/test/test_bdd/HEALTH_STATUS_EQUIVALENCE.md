# Revisão local do oráculo de health_status — 26/10/2026

Estado: alinhamento das asserções, ainda sem validação integrada pareada.
Nada desta revisão foi enviado ao remoto. Os resultados históricos permanecem
associados aos testes anteriores, sem alteração retroativa.

## Preservação

Cenários anteriores salvos nos commits ROS 1 `5b2406f8` e ROS 2 `0f8813e`.
Demais alterações locais de fontes e relatórios versionados preservadas na
branch `backup/antes-equivalencia-2026-10-26`: ROS 1 `5e660d54`, ROS 2 `fbef219`.
O executor aninhado ros_pytest tem backup local `201c4ad` na mesma branch.
Campanhas e diretórios de preparação não versionados permanecem no disco;
não foram apagados, movidos nem incluídos nesses commits de código.
A branch de trabalho é `testes/equivalencia-health-status-2026-10-26`.

## Mudança

Antes, ROS 1 exigia mais de um valor textual de patient_status, sem validar
sua faixa; ROS 2 exigia percentuais válidos, sem variação. Agora ambos usam
cópias idênticas de health_status_oracle.py. O positivo exige uma leitura
numérica finita do termômetro e estados numéricos entre 0 e 100, com pelo
menos dois valores numericamente distintos. O negativo exige leituras
válidas do termômetro e ausência de estado de saúde.

O mapeamento da leitura é `data` no ROS 1 e `sensor_datapoint` no ROS 2.
Não houve mudança de produção nesta revisão. A condição de variação foi
preservada da caracterização legada; não constitui requisito universal para
entradas constantes. A redação do Then explicita a observação, sem afirmar
que já se identificou a resposta causada por uma leitura específica.

## Validação e pendências

O teste local `src/ferramentas_traces/test_health_status_equivalence.py`
verificou 26 combinações (13 em cada versão) e identidade dos dois arquivos:
27 aprovações. Entre os contraexemplos estão ausência de estímulo, ausência
de resposta, saída indevida no caso negativo, NaN, valores fora da faixa e
variação apenas de formatação textual. Isso testa o oráculo, não o sistema ROS.

A tentativa integrada ROS 2 `ros2_20261026T132146Z_bhlt9626` terminou pelo
limite externo de 300 segundos (`timed_out=true`, exit_code=-9), antes de
qualquer início de cenário ou passo. Não gerou JUnit interno nem coverage
combinável. O log e o manifesto foram preservados em `src/campanhas_traces`.
Não contabilizar como aprovação nem como reprovação de comportamento.
Este contêiner só tem Jazzy; ROS 1 requer execução no ambiente Melodic.

Ainda não há equivalência experimental demonstrada: as preparações, janelas
de captura e trajetórias do simulador continuam diferentes. O ROS 1 usa
captura compartilhada com limite de linhas e espera de segurança; o ROS 2
usa janelas de tempo. O cenário negativo também utiliza passos de captura
diferentes. A próxima etapa é estabelecer estímulos controlados comuns,
observar prontidão antes de interromper o hub e relacionar as leituras à
saída, além de uniformizar a janela. Só então novas campanhas poderão
sustentar uma afirmação de equivalência para esse recorte de P10.
