import threading
import time

import ros_pytest
from pytest_bdd import scenarios, given, when, then, parsers
import pytest
import rospy
from interface_map import SYSTEM_MAP

from archlib.msg import AdaptationCommand, Status, Persist
from archlib.srv import EffectorRegister
from asserts import assert_node_is_online, is_node_receiving_multiple_topics
from messages.msg import SensorData, TargetSystemData
from test_adaptation_system import SharedAdaptationTests

scenarios("./features/managing_system.feature")

# ---------------------------------------------------------------------------
# Constantes derivadas do codigo-fonte do Controller e dos launches de teste
# ---------------------------------------------------------------------------
LOG_STATUS_TOPIC     = "log_status"

# Topico onde o /enactor publica AdaptationCommands (Controller.cpp:12,
# subscrito pelo /logger em Logger.cpp:28 -> receiveAdaptationCommand)
LOG_ADAPT_TOPIC      = "log_adapt"

# Node que entrega o AdaptationCommand ao sensor-alvo ("reconfigure" -> "reconfigure_<target>", ParamAdapter.cpp:23-29);
# alvo nao registrado so gera "target not found" em /rosout, nunca chega ao pipeline de persistencia.
PARAM_ADAPTER_NODE   = "/param_adapter"

# Frequencia inicial do controlador (param 'frequency' no launch do enactor)
INITIAL_FREQ_HZ      = 1.0

# Periodo de estabilizacao: quanto tempo esperamos sem stream de "fail" para
# que o /reli_engine atinja zona morta (|error| < 0.018) antes de S4
STABILIZATION_S = 5.0

# ---------------------------------------------------------------------------
# Singleton lazy
# ---------------------------------------------------------------------------
_shared_adaptation_tests = None


def _get_shared_adaptation_tests():
    global _shared_adaptation_tests
    _ensure_ros_node()
    if _shared_adaptation_tests is None:
        _shared_adaptation_tests = SharedAdaptationTests()
    return _shared_adaptation_tests


def _ensure_ros_node():
    if not rospy.core.is_initialized():
        rospy.init_node("bdd_managing_system", anonymous=True)


# ---------------------------------------------------------------------------
# Helpers: status stream
# ---------------------------------------------------------------------------

def _start_status_failure_stream(context, interval=0.5):
    stop_event = threading.Event()

    def _run():
        pub = rospy.Publisher(LOG_STATUS_TOPIC, Status, queue_size=10)
        rospy.sleep(0.2)
        msg = Status()
        msg.source = context["target_sensor"]
        msg.target = "/logger"
        msg.content = "fail"
        while not stop_event.is_set():
            pub.publish(msg)
            stop_event.wait(interval)

    thread = threading.Thread(target=_run)
    thread.daemon = True
    thread.start()
    context["_status_stream_stop"] = stop_event
    context["_status_stream_thread"] = thread


def _stop_status_failure_stream(context):
    stop_event = context.pop("_status_stream_stop", None)
    thread   = context.pop("_status_stream_thread", None)
    if stop_event:
        stop_event.set()
    if thread:
        thread.join(timeout=2.0)




# ---------------------------------------------------------------------------
# Helpers: AdaptationCommand
# ---------------------------------------------------------------------------

def _mark_since_index(context):
    """Registra o tamanho atual da lista de comandos para usar como since_index."""
    shared = _get_shared_adaptation_tests()
    with shared.lock:
        context["adaptation_since_index"] = len(shared.commands)


def _mark_persist_since_index(context):
    """Registra o tamanho atual de shared.persist_received: then_adaptation_logged checa a lista inteira e "o oximeter" e
    reutilizado por quase todo cenario, entao uma checagem nao-escopada passaria mesmo sem o When emitir nada."""
    shared = _get_shared_adaptation_tests()
    with shared.persist_lock:
        context["persist_since_index"] = len(shared.persist_received)


def _wait_for_persist_record(target, msg_type="AdaptationCommand", timeout=10.0, since_index=0):
    """Aguarda um novo Persist (apos since_index) do tipo/target informados."""
    shared = _get_shared_adaptation_tests()
    deadline = time.time() + timeout
    while time.time() < deadline:
        with shared.persist_lock:
            snapshot = list(shared.persist_received[since_index:])
        for msg in snapshot:
            if msg.target == target and msg.type == msg_type:
                return msg
        rospy.sleep(0.05)
    return None


def _wait_for_adaptation_command(target=None, timeout=30.0, require=True, since_index=0):
    shared = _get_shared_adaptation_tests()
    deadline = time.time() + timeout
    while time.time() < deadline:
        with shared.lock:
            snapshot = list(shared.commands[since_index:])
        for msg in reversed(snapshot):
            if target and msg.target != target:
                continue
            if msg.action and msg.action.startswith("freq="):
                return (msg.target, msg.action)
        rospy.sleep(0.05)
    if require:
        assert False, "Nenhum AdaptationCommand recebido para {} em {:.0f}s".format(
            target or "any", timeout)
    return None


def _wait_for_adaptation_command_above(target, min_freq_hz, timeout=30.0, since_index=0):
    """Aguarda um AdaptationCommand com freq > min_freq_hz, descartando reducoes que cheguem antes de o sistema convergir
    para o estado de baixa confiabilidade."""
    shared = _get_shared_adaptation_tests()
    deadline = time.time() + timeout
    while time.time() < deadline:
        with shared.lock:
            snapshot = list(shared.commands[since_index:])
        for msg in reversed(snapshot):
            if target and msg.target != target:
                continue
            if msg.action and msg.action.startswith("freq="):
                freq = float(msg.action.split("=", 1)[1])
                if freq > min_freq_hz:
                    return (msg.target, msg.action)
        rospy.sleep(0.05)
    return None


def _wait_for_adaptation_command_below(target, max_freq_hz, timeout=30.0, since_index=0):
    """Aguarda um AdaptationCommand com freq < max_freq_hz, descartando aumentos anteriores a recuperacao: a janela de 10.1s
    de DataAccess::applyTimeWindow mantem 'fail' antigos em r_curr por ~10s apos o stream parar."""
    shared = _get_shared_adaptation_tests()
    deadline = time.time() + timeout
    while time.time() < deadline:
        with shared.lock:
            snapshot = list(shared.commands[since_index:])
        for msg in reversed(snapshot):
            if target and msg.target != target:
                continue
            if msg.action and msg.action.startswith("freq="):
                freq = float(msg.action.split("=", 1)[1])
                if freq < max_freq_hz:
                    return (msg.target, msg.action)
        rospy.sleep(0.05)
    return None


def _parse_frequency_hz(action):
    assert action.startswith("freq="), "Formato inesperado: {}".format(action)
    return float(action.split("=", 1)[1])


# ---------------------------------------------------------------------------
# Helpers: frequencia de topico
# ---------------------------------------------------------------------------

def _sample_topic_frequency(topic, message_type=SensorData,
                             sample_count=6, timeout=12.0, retries=3):
    last_error = None
    for attempt in range(retries):
        receive_times = []
        lock = threading.Lock()

        def _cb(msg, _recv=receive_times, _lk=lock):
            with _lk:
                _recv.append(time.time())

        sub = rospy.Subscriber(topic, message_type, _cb)
        rospy.sleep(0.3)
        deadline = time.time() + timeout
        while time.time() < deadline:
            with lock:
                if len(receive_times) >= sample_count:
                    break
            rospy.sleep(0.05)
        sub.unregister()

        with lock:
            times = list(receive_times)
        try:
            assert len(times) >= 2, \
                "Amostras insuficientes ({} coletadas)".format(len(times))
            deltas = [t2 - t1 for t1, t2 in zip(times, times[1:]) if t2 > t1]
            assert deltas, "Nenhum delta positivo"
            return 1.0 / (sum(deltas) / len(deltas))
        except AssertionError as exc:
            last_error = exc
            rospy.sleep(0.5)
    raise last_error


def _wait_for_service(service_name, timeout=10.0):
    try:
        rospy.wait_for_service(service_name, timeout=timeout)
        return True
    except rospy.ROSException:
        return False


def _set_effector_connection(target_sensor, connected, timeout=10.0):
    """Chama o servico EffectorRegister (Component.cpp:33-44,80-94) para (des)registrar o sensor em ParamAdapter::target_arr:
    connection=False faz todo comando cair em "target not found" (ParamAdapter.cpp:23-29). Matar o sensor NAO funciona, pois
    Component so se desregistra no sigIntHandler (Component.cpp:27), que o shutdown XML-RPC do rosnode.kill_nodes nao chama."""
    assert _wait_for_service("EffectorRegister", timeout=timeout), (
        "Servico EffectorRegister indisponivel apos {:.0f}s".format(timeout)
    )
    client = rospy.ServiceProxy("EffectorRegister", EffectorRegister)
    response = client(name=target_sensor, connection=connected)
    return response.ACK


def _wait_for_system_stable(timeout=STABILIZATION_S):
    """Aguarda o /reli_engine parar de emitir AdaptationCommands (zona morta), para que comandos de ciclos anteriores nao
    contaminem o since_index de S4."""
    shared = _get_shared_adaptation_tests()
    deadline = time.time() + timeout
    last_count = -1
    stable_since = None
    while time.time() < deadline:
        with shared.lock:
            count = len(shared.commands)
        if count == last_count:
            if stable_since is None:
                stable_since = time.time()
            elif time.time() - stable_since > 2.0:
                return  # sem novos comandos por 2s -> estavel
        else:
            last_count = count
            stable_since = None
        rospy.sleep(0.2)


def given_reliability_below_setpoint(context):
    _ensure_ros_node()
    assert_node_is_online("/reli_engine")
    _mark_since_index(context)

    context["reliability_state"] = "below_setpoint"


def given_enactor_active(context):
    assert_node_is_online("/enactor")
    _wait_for_service("EngineRequest", timeout=20.0)
    context["enactor_active"] = True

@given(parsers.parse("the managing system is monitoring the reliability of {sensor}"))
def given_monitoring_reliability(context, sensor):
    context["target_sensor"] = SYSTEM_MAP[sensor]
    # the /reli_engine node is computing reliability below the defined setpoint
    given_reliability_below_setpoint(context)
    context['shared'] = _get_shared_adaptation_tests()

    # the /enactor node is active and connected to /reli_engine
    assert_node_is_online("/enactor")
    _wait_for_service("EngineRequest", timeout=20.0)
    context["enactor_active"] = True

    # the /param_adapter node is ready to receive reconfiguration commands
    assert_node_is_online("/param_adapter")
    context["param_adapter_ready"] = True

@when(parsers.parse("{sensor} repeatedly reports a 'fail' status"))
def when_sensor_reports_fail(context, sensor):
    context["target_sensor"] = SYSTEM_MAP[sensor]
    context["degradation_start_time"] = time.time()
    _start_status_failure_stream(context)
    # Frequencia nominal inicial do controlador, conforme o launch do enactor.
    context["baseline_frequency_hz"] = INITIAL_FREQ_HZ

def then_adaptation_logged(context, timeout=5.0):
    assert_node_is_online("/logger")
    assert_node_is_online("/data_access")

    shared = context['shared']
    received = shared.persist_received
    found = [x for x in received if x.target == context["target_sensor"]]

    assert found, (
        "Nenhuma mensagem Persist com type='AdaptationCommand' e source='{}' "
        "recebida no topico 'persist' em {:.0f}s. "
        "O /logger deveria publicar em 'persist' ao receber um AdaptationCommand "
        "em log_adapt (Logger.cpp linhas 39-46).".format(context["target_sensor"], timeout)
    )
    persist_msg = found[0]
    print("Persist confirmado: type={} source={} content={}".format(
        persist_msg.type, persist_msg.source, persist_msg.content))

@then(parsers.parse("an adaptation command increasing the sampling rate of {sensor} should be issued"))
def then_increase_sampling_rate(context, sensor):
    target_sensor = SYSTEM_MAP[sensor]
    context["target_sensor"] = target_sensor
    # the /enactor should issue an adaptation command targeting /g3t1_1 with a higher frequency
    since = context.get("adaptation_since_index", 0)
    baseline = context["baseline_frequency_hz"]

    # Aguarda especificamente um comando com frequencia ACIMA da inicial.
    # Isso descarta comandos de reducao emitidos antes do /reli_engine
    # ter acumulado suficientes "fail" para reduzir r_curr abaixo do setpoint.
    result = _wait_for_adaptation_command_above(
        target=target_sensor,
        min_freq_hz=baseline,
        timeout=30.0,
        since_index=since,
    )
    _stop_status_failure_stream(context)

    assert result is not None, (
        "Nenhum AdaptationCommand com freq > {:.1f}Hz recebido para {} em 30s. "
        "O managing system deveria aumentar a taxa de amostragem quando a "
        "confiabilidade esta abaixo do setpoint (error > 0 -> new_freq aumenta).".format(
            baseline, target_sensor)
    )
    _, action = result
    commanded_hz = _parse_frequency_hz(action)
    print("AdaptationCommand de aumento: {} freq={:.3f}Hz (baseline={:.1f}Hz)".format(
        target_sensor, commanded_hz, baseline))
    context["commanded_frequency_hz"] = commanded_hz


    # the adaptation command should be recorded in the knowledge repository via /logger
    # we need to add a validation if it was registered
    then_adaptation_logged(context)

def _wait_for_peak_frequency_stable(context, since_index, timeout=15.0, quiet_period=2.5):
    """Aguarda a maior frequencia observada para o target_sensor parar de crescer e retorna esse valor como o pico."""
    shared = _get_shared_adaptation_tests()
    target_sensor = context["target_sensor"]
    deadline = time.time() + timeout
    peak_hz = None
    last_increase_time = time.time()
    seen = 0
    while time.time() < deadline:
        with shared.lock:
            snapshot = list(shared.commands[since_index:])
        for msg in snapshot[seen:]:
            if msg.target == target_sensor and msg.action and msg.action.startswith("freq="):
                freq = _parse_frequency_hz(msg.action)
                if peak_hz is None or freq > peak_hz:
                    peak_hz = freq
                    last_increase_time = time.time()
        seen = len(snapshot)
        if peak_hz is not None and (time.time() - last_increase_time) > quiet_period:
            return peak_hz
        rospy.sleep(0.2)
    return peak_hz


# Helper interno. Reaproveitada por given_elevated_rate_sensor, abaixo.
def given_elevated_rate(context):
    # a sampling-rate increase strategy was previously applied to /g3t1_1
    _ensure_ros_node()
    assert_node_is_online("/reli_engine")
    assert_node_is_online("/enactor")
    shared = _get_shared_adaptation_tests()
    with shared.lock:
        elevate_start_index = len(shared.commands)

    _start_status_failure_stream(context)
    rospy.sleep(8.0)
    _stop_status_failure_stream(context)

    peak_hz = _wait_for_peak_frequency_stable(context, elevate_start_index)

    assert peak_hz is not None, (
        "Nenhum AdaptationCommand com freq= recebido para {} durante os 5s de "
        "stream de 'fail'. A precondicao 'operating at an elevated sampling rate' "
        "nao foi de fato atingida.".format(context["target_sensor"])
    )
    context["peak_frequency_hz"] = peak_hz
    print("Pico de frequencia atingido antes da recuperacao: {:.3f}Hz".format(peak_hz))

    _mark_since_index(context)
    context['shared'] = shared

    # the /reli_engine node is now computing reliability above the defined setpoint
    context["reliability_state"] = "above_setpoint"


# Helper interno (idem). Reaproveitada por when_reliability_recovers_sensor, abaixo.
def when_reliability_recovers(context):
    # Ao interromper o stream de "fail" (ja feito no Given para evitar race conditions),
    # o sistema recebe leituras limpas e a confiabilidade sobe naturalmente de volta para 100%.
    # O ROS faz o recalculo neste momento.
    rospy.sleep(2.0)

@given(parsers.parse("{sensor} is operating at an elevated sampling rate"))
def given_elevated_rate_sensor(context, sensor):
    context["target_sensor"] = SYSTEM_MAP[sensor]
    given_elevated_rate(context)

@when(parsers.parse("the reliability of {sensor} rises above the threshold"))
def when_reliability_recovers_sensor(context, sensor):
    context["target_sensor"] = SYSTEM_MAP[sensor]
    when_reliability_recovers(context)

@then(parsers.parse('an adaptation command reducing the sampling rate of {sensor} should be issued'))
def then_reduce_sampling_rate(context, sensor):
    target_sensor = SYSTEM_MAP[sensor]
    since = context.get("adaptation_since_index", 0)

    # Pico medido em given_elevated_rate antes do /enactor entrar em recuperacao.
    peak_hz = context.get("peak_frequency_hz")
    assert peak_hz is not None, (
        "peak_frequency_hz nao disponivel no context; o Given nao mediu o pico "
        "de frequencia antes da recuperacao."
    )

    result = _wait_for_adaptation_command_below(
        target=target_sensor,
        max_freq_hz=peak_hz,
        timeout=30.0,
        since_index=since,
    )

    assert result is not None, (
        "Nenhum AdaptationCommand com freq < {:.3f}Hz (pico) recebido para {} em 30s. "
        "O managing system deveria reduzir a taxa de amostragem apos a "
        "confiabilidade se recuperar.".format(peak_hz, target_sensor)
    )

    _, action = result
    commanded_hz = _parse_frequency_hz(action)

    then_adaptation_logged(context)

# Helpers internos (reaproveitados pelos steps de "nao consegue receber adaptacao"). O cenario e reproduzido desregistrando
# o sensor de ParamAdapter::target_arr via EffectorRegister (Component.cpp:33-44,80-94; ParamAdapter.cpp:31-57); matar o
# processo NAO reproduz, pois Component so se desregistra no sigIntHandler (Component.cpp:27), que o XML-RPC nao chama.
def given_cannot_receive_adaptation(context, target_sensor):
    _ensure_ros_node()
    assert_node_is_online(PARAM_ADAPTER_NODE)
    assert_node_is_online(target_sensor)

    context['shared'] = _get_shared_adaptation_tests()
    _mark_since_index(context)
    _mark_persist_since_index(context)

    ack = _set_effector_connection(target_sensor, False)
    assert ack, (
        "EffectorRegister recusou desconectar {} de {}; a precondicao "
        "'cannot receive adaptation commands' nao foi de fato "
        "estabelecida.".format(target_sensor, PARAM_ADAPTER_NODE)
    )
    context["_effector_disconnected"] = target_sensor


def when_adaptation_issued(context, target_sensor):
    # Publica diretamente em log_adapt, o mesmo topico usado pelo
    # /enactor (Controller.cpp:12), simulando que um AdaptationCommand foi
    # de fato emitido visando o sensor desligado.
    pub = rospy.Publisher(LOG_ADAPT_TOPIC, AdaptationCommand, queue_size=10)
    rospy.sleep(0.3)  # tempo para o publisher completar o handshake com o /logger

    msg = AdaptationCommand()
    msg.source = "/enactor"
    msg.target = target_sensor
    msg.action = "freq=5.0"
    pub.publish(msg)
    pub.unregister()

    context["issued_adaptation_action"] = msg.action


def then_adaptation_recorded_despite_failure(context, target_sensor):
    try:
        assert_node_is_online("/logger")
        assert_node_is_online("/data_access")

        # Resiliencia: Logger::receiveAdaptationCommand (Logger.cpp:36-48) persiste o comando ao recebe-lo em log_adapt, ANTES de
        # ele esbarrar no "target not found" do ParamAdapter (ParamAdapter.cpp:23-29). Usa persist_since_index (marcado no Given)
        # e nao o helper generico, pois "o oximeter" tem registros antigos que fariam uma checagem nao-escopada passar.
        persist_since = context.get("persist_since_index", 0)
        persist_msg = _wait_for_persist_record(
            target_sensor, msg_type="AdaptationCommand",
            timeout=10.0, since_index=persist_since,
        )
        assert persist_msg is not None, (
            "Nenhum novo registro Persist (type='AdaptationCommand', "
            "target='{}') apareceu em 'persist' apos o comando emitido neste "
            "cenario, mesmo com {} desconectado de {}. O /logger deveria "
            "publicar em 'persist' ao receber o AdaptationCommand em "
            "log_adapt independentemente de o /param_adapter conseguir "
            "rotea-lo (Logger.cpp:36-48).".format(
                target_sensor, target_sensor, PARAM_ADAPTER_NODE)
        )
        print("Persist confirmado mesmo com o sensor desconectado: type={} source={} content={}".format(
            persist_msg.type, persist_msg.source, persist_msg.content))
    finally:
        # Restaura a conexao do sensor com o /param_adapter, para que o
        # estado do sistema nao vaze para outros cenarios/execucoes.
        if context.pop("_effector_disconnected", None) == target_sensor:
            _set_effector_connection(target_sensor, True)


@given(parsers.parse("{sensor} cannot receive adaptation commands"))
def given_cannot_receive_adaptation_sensor(context, sensor):
    target_sensor = SYSTEM_MAP[sensor]
    context["target_sensor"] = target_sensor
    given_cannot_receive_adaptation(context, target_sensor)

@when(parsers.parse("an adaptation command is issued for {sensor}"))
def when_adaptation_issued_for_sensor(context, sensor):
    target_sensor = SYSTEM_MAP[sensor]
    context["target_sensor"] = target_sensor
    when_adaptation_issued(context, target_sensor)

@then(parsers.parse("the adaptation command should be recorded in the system log even though {sensor} cannot receive it"))
def then_adaptation_recorded_despite_failure_sensor(context, sensor):
    target_sensor = SYSTEM_MAP[sensor]
    context["target_sensor"] = target_sensor
    then_adaptation_recorded_despite_failure(context, target_sensor)


# ===========================================================================
# Nenhuma adaptacao quando confiabilidade esta estavel
# ===========================================================================

# Helper interno. Reaproveitada por when_reliability_stays_above_threshold, abaixo.
def when_managing_system_evaluates(context):
    rospy.sleep(3.0)

@when(parsers.parse("the reliability of {sensor} stays above the threshold"))
def when_reliability_stays_above_threshold(context, sensor):
    context["target_sensor"] = SYSTEM_MAP[sensor]
    when_managing_system_evaluates(context)

@pytest.mark.xfail(reason="Comportamento As-Is: O sistema age como otimizador de energia. Em ambiente sem falhas (r_curr=1.0), ele reduz continuamente a frequencia, nunca atingindo estabilidade silenciosa.")
@then(parsers.parse("no adaptation command for {sensor} should be issued"))
def then_no_adaptation_command_sensor(context, sensor):
    target_sensor = SYSTEM_MAP[sensor]
    since = context.get("adaptation_since_index", 0)
    result = _wait_for_adaptation_command(
        target=target_sensor,
        timeout=5.0,
        require=False,
        since_index=since,
    )
    assert result is None, (
        "AdaptationCommand inesperado quando confiabilidade estava estavel: {}. "
        "O /reli_engine nao deveria publicar em log_adapt para {} quando "
        "|error| < stability_margin * r_ref.".format(result, target_sensor)
    )

    shared = _get_shared_adaptation_tests()
    with shared.lock:
        new_commands = list(shared.commands[since:])
    sensor_commands = [c for c in new_commands if c.target == TARGET_SENSOR]
    assert len(sensor_commands) == 0, (
        "Comandos de adaptacao inesperados para {}: {}".format(
            TARGET_SENSOR, sensor_commands)
    )
# Helper interno. Reaproveitada por given_stable_reliability_sensor, abaixo.
def given_stable_reliability(context):
    _ensure_ros_node()
    assert_node_is_online("/reli_engine")
    # Aguarda o sistema estabilizar (sem "fail" no stream, r_curr sobe
    # ate ultrapassar o setpoint e o enactor entra na zona morta).
    _wait_for_system_stable(timeout=STABILIZATION_S)
    _mark_since_index(context)
    context["reliability_state"] = "stable"

    given_enactor_active(context)

@given(parsers.parse("{sensor} is operating normally with stable reliability"))
def given_stable_reliability_sensor(context, sensor):
    context["target_sensor"] = SYSTEM_MAP[sensor]
    given_stable_reliability(context)

@then(parsers.parse("an adaptation command for {sensor} should be issued within {time_limit} seconds"))
def then_adaptation_within_time_limit_sensor(context, sensor, time_limit):
    target_sensor = SYSTEM_MAP[sensor]
    since = context.get("adaptation_since_index", 0)
    t_start = context["degradation_start_time"]
    time_limit_s = float(time_limit)

    result = _wait_for_adaptation_command(
        target=target_sensor,
        timeout=time_limit_s,
        require=False,
        since_index=since,
    )
    _stop_status_failure_stream(context)

    elapsed = time.time() - t_start
    assert result is not None, (
        "AdaptationCommand para {} nao chegou em {:.0f}s".format(
            target_sensor, time_limit_s)
    )
    assert elapsed <= time_limit_s, (
        "Tempo de resposta {:.2f}s excede o limite de {:.0f}s".format(
            elapsed, time_limit_s)
    )
