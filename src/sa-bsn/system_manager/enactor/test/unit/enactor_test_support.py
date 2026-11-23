# -*- coding: utf-8 -*-
"""Shared harness for the `enactor` rostest suites (test_enactor.py cost path, test_enactor_reliability.py reliability path):
they drive the C++ node black-box with a real `data_access`. The readiness gate waits for the enactor to be subscribed to
`event`/`strategy`, not for /log_adapt to be advertised: Controller::setUp() advertises first and is deaf for up to 10s."""
import time

import rospy
from archlib.msg import AdaptationCommand, Event, Exception as BSNException, Persist, Strategy
from archlib.srv import EngineRequest, EngineRequestResponse

# The enactor's receiveStatus() cycle, i.e. the "frequency" param both
# launches set (5 Hz -> one cycle every 0.2s).
CYCLE = 0.2

# Timeouts, not sleeps: every helper below returns as soon as what it waits
# for shows up.
CONNECTION_WAIT = 10.0
CYCLE_WAIT = 5.0

# Controller::setUp() still burns its full 10s waitForService timeout if the
# EngineRequest stub is not up in time, so the readiness gate tolerates that.
NODE_READY_WAIT = 30.0

# Spacing between EnergyStatus retries: comfortably larger than one enactor
# cycle, so two readings can never be consumed by the same cycle - see
# energy_until_command().
ENERGY_RETRY_SPACING = 0.5

# 5 consecutive in/out-of-tolerance cycles are needed before Controller
# publishes an Exception (|exception_buffer| > 4), i.e. ~1s at 5 Hz.
EXCEPTION_WAIT = 6.0


def wait_for(condition_function, timeout=CYCLE_WAIT):
    start_time = time.time()
    while time.time() < start_time + timeout:
        if condition_function():
            return True
        time.sleep(0.02)
    return False


class EnactorHarness(object):
    """Owns the ROS plumbing shared by every test in a suite: publishers/subscribers are created once, only after
    the enactor is provably listening; reset() clears the collected messages between tests."""

    def __init__(self, adaptation_parameter):
        self.adaptation_parameter = adaptation_parameter
        self.engine_requests = 0
        self.log_adapt_messages = []
        self.exception_messages = []

    # ------------------------------------------------------------------
    # setup / teardown
    # ------------------------------------------------------------------
    def start(self, node_name):
        rospy.init_node(node_name, anonymous=True)

        # Stands in for reli_engine/cost_engine's EngineRequest service (see
        # Engine::sendAdaptationParameter, which answers with its
        # "qos_attribute" param the same way).
        self.engine_service = rospy.Service(
            "EngineRequest", EngineRequest, self._send_adaptation_parameter
        )

        assert wait_for(
            lambda: "/log_adapt" in [n for n, _ in rospy.get_published_topics()],
            timeout=NODE_READY_WAIT,
        ), "enactor node never advertised /log_adapt (Controller::setUp did not run)"

        self.event_pub = rospy.Publisher("event", Event, queue_size=10)
        self.strategy_pub = rospy.Publisher("strategy", Strategy, queue_size=10)
        self.persist_pub = rospy.Publisher("persist", Persist, queue_size=10)
        self.log_adapt_sub = rospy.Subscriber(
            "log_adapt", AdaptationCommand, self._on_adaptation_command
        )
        self.exception_sub = rospy.Subscriber(
            "exception", BSNException, self._on_exception
        )

        # The real gate: `event` and `strategy` are subscribed inside
        # Enactor::body(), so a connection on them proves setUp() is over and
        # the receiveStatus() cycle is running. See the module docstring.
        assert wait_for(
            lambda: self.event_pub.get_num_connections() > 0
            and self.strategy_pub.get_num_connections() > 0,
            timeout=NODE_READY_WAIT,
        ), "enactor never subscribed to event/strategy (Enactor::body never started)"

        assert wait_for(
            lambda: self.persist_pub.get_num_connections() > 0,
            timeout=CONNECTION_WAIT,
        ), "data_access never subscribed to persist"

        assert wait_for(
            lambda: self.log_adapt_sub.get_num_connections() > 0
            and self.exception_sub.get_num_connections() > 0,
            timeout=CONNECTION_WAIT,
        ), "never connected to the enactor's log_adapt/exception publishers"

    def stop(self):
        for endpoint in (
            self.event_pub,
            self.strategy_pub,
            self.persist_pub,
            self.log_adapt_sub,
            self.exception_sub,
        ):
            endpoint.unregister()
        self.engine_service.shutdown()

    def reset(self):
        # Cleared in place: the subscriber callbacks hold a reference to
        # these very lists.
        del self.log_adapt_messages[:]
        del self.exception_messages[:]

    # ------------------------------------------------------------------
    # callbacks
    # ------------------------------------------------------------------
    def _send_adaptation_parameter(self, _req):
        self.engine_requests += 1
        return EngineRequestResponse(self.adaptation_parameter)

    def _on_adaptation_command(self, msg):
        self.log_adapt_messages.append(msg)

    def _on_exception(self, msg):
        self.exception_messages.append(msg)

    # ------------------------------------------------------------------
    # stimuli
    # ------------------------------------------------------------------
    def activate(self, component, freq):
        """Controller::receiveEvent's "activate" branch is the only place that initializes freq/kp/r_ref/c_ref, so every
        test starts here; one publish is enough because start() already waited for the connection."""
        msg = Event()
        msg.source = component
        msg.content = "activate"
        msg.freq = freq
        self.event_pub.publish(msg)
        # receiveEvent runs in body()'s ros::spinOnce(), i.e. at most one
        # cycle after delivery - give it three before anything depends on it.
        time.sleep(3 * CYCLE)

    def deactivate(self, component):
        msg = Event()
        msg.source = component
        msg.content = "deactivate"
        self.event_pub.publish(msg)
        time.sleep(3 * CYCLE)

    def set_reference(self, component, value):
        """Feeds Enactor::receiveStrategy, which is what the adaptation
        engine normally uses to move r_ref/c_ref away from the defaults that
        receiveEvent set."""
        msg = Strategy()
        msg.source = "/engine"
        msg.target = "/enactor"
        msg.content = "{}:{};".format(component, value)
        self.strategy_pub.publish(msg)
        time.sleep(3 * CYCLE)

    def publish_status(self, component, content="success"):
        """A Status is what puts the component in data_access's `status` map,
        and processQuery only ever answers for components in that map - so
        without it the enactor never even looks at the component."""
        msg = Persist()
        msg.source = component
        msg.target = "system"
        msg.type = "Status"
        msg.content = content
        self.persist_pub.publish(msg)

    def publish_energy(self, component, cost):
        msg = Persist()
        msg.source = component
        msg.target = "system"
        msg.type = "EnergyStatus"
        msg.content = str(cost)
        self.persist_pub.publish(msg)

    def energy_until_command(self, component, cost, timeout=CYCLE_WAIT):
        """Publish one EnergyStatus at a time until an AdaptationCommand for `component` shows up (or `timeout`).
        Readings are spaced by more than one enactor cycle because calculateComponentCost zeroes the accumulated cost
        on every "/enactor" query; retrying covers a first reading consumed before the activate was processed."""
        deadline = time.time() + timeout
        while time.time() < deadline and not self.commands_for(component):
            self.publish_energy(component, cost)
            time.sleep(ENERGY_RETRY_SPACING)
        return self.commands_for(component)

    def flood_energy(self, component, cost, duration, condition=None):
        """Keep republishing EnergyStatus faster than the enactor's cycle so the error stays out of tolerance every
        cycle (unlike energy_until_command, this wants the accumulation, else exception_buffer resets each cycle)."""
        deadline = time.time() + duration
        while time.time() < deadline:
            self.publish_energy(component, cost)
            if condition is not None and condition():
                return True
            time.sleep(0.05)
        return condition() if condition is not None else False

    # ------------------------------------------------------------------
    # observations
    # ------------------------------------------------------------------
    def commands_for(self, component):
        return [m.action for m in self.log_adapt_messages if m.target == component]

    def freqs_for(self, component):
        return [
            float(action.split("=")[1])
            for action in self.commands_for(component)
            if action.startswith("freq=")
        ]

    def wait_for_command(self, component, timeout=CYCLE_WAIT):
        return wait_for(lambda: bool(self.commands_for(component)), timeout)

    def wait_for_freq(self, component, expected, timeout=CYCLE_WAIT, tolerance=0.01):
        return wait_for(
            lambda: any(abs(f - expected) < tolerance for f in self.freqs_for(component)),
            timeout,
        )

    def wait_for_exception(self, content, timeout=EXCEPTION_WAIT):
        return wait_for(
            lambda: content in [m.content for m in self.exception_messages], timeout
        )
