# Especificações do Projeto (SA-BSN)

## Visão geral
O **Self-Adaptive Body Sensor Network (SA-BSN)** é um sistema auto-adaptativo baseado em **ROS (Robot Operating System)** para coleta e processamento de sinais fisiológicos. O projeto é organizado como um workspace Catkin com múltiplos pacotes, incluindo o pacote `sa-bsn`, que concentra a maior parte do domínio do sistema.

## Stack e componentes principais
- **ROS Melodic + Catkin** como base de execução, build e testes.
- **C++11** para nós ROS e componentes de sensores.
- **Python** para testes, utilitários e integrações.
- **Launch files** (`*.launch`) para orquestrar nós e cenários.
- **Configurações** em `src/sa-bsn/configurations/*` para cenários de execução e testes.

## Estrutura de testes (como estão implementados)
Os testes combinam **rostest**, **pytest**, **pytest-bdd**, **behave** e testes C++ (onde aplicável). Abaixo está o mapeamento de onde estão e como funcionam.

### 1) Testes ROS + Pytest (via `ros_pytest`)
- Integração entre **pytest** e **Catkin** está em `src/ros_pytest/cmake/pytest.cmake`.
- O helper `add_pytests(...)` registra testes Python para execução via `catkin_make run_tests`, gerando XML de resultados e suporte opcional a cobertura.
- Exemplo de testes de utilidade do `ros_pytest` em `src/ros_pytest/src/ros_pytest/tests/test_ros_pytest.py`.

### 2) Testes BDD com `pytest-bdd`
- Os testes BDD de integração do sistema estão em:
  - `src/sa-bsn/target_system/components/component/test/test_bdd/*.py`
- Exemplo de cenário: `test_check_bsn.py`, que carrega features e valida publicação/assinatura de tópicos ROS.
- As **steps compartilhadas** ficam em:
  - `src/sa-bsn/target_system/components/component/test/conftest.py`
- As features (Gherkin) usadas nesses testes estão em:
  - `features/*.feature` (na raiz do workspace)
- As steps utilizam ROS (`rospy`, `rosnode`) para verificar nós online, tópicos publicados/assinados e payloads em tempo real.

### 3) Testes BDD com `behave`
- Existe suporte adicional a BDD com **behave** (Python 2) em:
  - `src/sa-bsn/target_system/components/component/test/bdd/steps/test_steps.py`
  - `features/environment.py` (hooks de setup/teardown)
- Esses testes inicializam nós ROS e publicam mensagens em tópicos para validar comunicação end-to-end.

### 4) Testes unitários com `rostest` + launch
- Os cenários de teste unitário são definidos em arquivos `*.launch`:
  - `src/sa-bsn/target_system/components/component/test/unit/*.launch`
- No `CMakeLists.txt` do pacote `component`, alguns testes estão registrados via `add_rostest(...)`. Atualmente o teste ativo (não comentado) é:
  - `test/unit/test_G3T1_2.launch`

### 5) Testes de integração Python
- Há testes de integração específicos para nós C++ em:
  - `src/sa-bsn/target_system/components/component/test/integration/test_my_cpp_node.py`

### 6) Testes C++ / executáveis auxiliares
- Alguns testes/execs C++ estão em:
  - `src/sa-bsn/target_system/components/component/test/features/*.cpp`
  - `src/sa-bsn/target_system/components/component/test/test_g4t1.cpp`
- Estes podem ser orquestrados por launch files de testes, dependendo da configuração.

### 7) Cobertura de código
- Em **build Debug**, o pacote `component` habilita flags de cobertura (GCOV):
  - `-fprofile-arcs -ftest-coverage -O0`
- Há artefatos de cobertura em `coverage/` (HTML e `.info`).

## Como executar os testes (fluxo atual)
A execução recomendada descrita no `README.md` é:
- `catkin_make run_tests`
- `catkin_test_results`

Observações importantes:
- Os testes dependem de **ROS Core** e tópicos ativos. Alguns cenários esperam nós específicos do SA-BSN em execução.
- Alguns `add_rostest(...)` estão comentados no `CMakeLists.txt` do pacote `component`, indicando que há testes desativados.

## Requisitos implícitos de execução
- ROS Melodic instalado e ambiente `setup.bash` carregado.
- Dependências `ros_pytest`, `pytest`, `pytest-bdd` e `behave` instaladas no ambiente Python.
- Launch files e nós necessários disponíveis (ex.: `g3t1_*`, `g4t1`, `TargetSystemData`).

## Convenções de teste
- **BDD** (Gherkin) descreve comportamento do sistema com foco em tópicos ROS e fluxo de dados.
- **Testes unitários/integração** são orquestrados via `rostest` + `.launch` para subir nós e validar comunicação.
- Resultados são exportados em XML para integração com `catkin_test_results`.
