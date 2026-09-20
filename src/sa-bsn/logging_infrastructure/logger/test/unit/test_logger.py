# -*- coding: utf-8 -*-
"""Unit tests for the `logger` node (Logger.cpp); equivalent to bsn_ros2/system_monitor/test/test_logger.py.
The node is a separate C++ process (test_logger.launch), so it is tested through its topics: publish on "log_*",
subscribe to "persist" and check the resulting Persist message."""
import threading
import time

import rospy
from archlib.msg import (
    AdaptationCommand,
    EnergyStatus,
    Event,
    Persist,
    Status,
    Uncertainty,
)

CONNECTION_WAIT = 0.5
PUBLISH_SETTLE = 0.1


def wait_for(condition_function, timeout=5.0):
    """Wait for a condition function to become true or timeout."""
    start_time = time.time()
    while time.time() < start_time + timeout:
        if condition_function():
            return True
        time.sleep(0.05)
    return False


class TestLogger:
    """Tests for the `logger` node, driven through its real topic interface."""

    @classmethod
    def setup_class(cls):
        rospy.init_node("test_logger_node", anonymous=True)

    def setup_method(self):
        self.received = []
        self.lock = threading.Lock()

        self.persist_sub = rospy.Subscriber(
            "persist", Persist, self._on_persist
        )

        self.status_pub = rospy.Publisher("log_status", Status, queue_size=10)
        self.event_pub = rospy.Publisher("log_event", Event, queue_size=10)
        self.energy_pub = rospy.Publisher(
            "log_energy_status", EnergyStatus, queue_size=10
        )
        self.uncertainty_pub = rospy.Publisher(
            "log_uncertainty", Uncertainty, queue_size=10
        )
        self.adapt_pub = rospy.Publisher(
            "log_adapt", AdaptationCommand, queue_size=10
        )

        time.sleep(CONNECTION_WAIT)

    def teardown_method(self):
        self.persist_sub.unregister()
        self.status_pub.unregister()
        self.event_pub.unregister()
        self.energy_pub.unregister()
        self.uncertainty_pub.unregister()
        self.adapt_pub.unregister()
        with self.lock:
            self.received = []

    def _on_persist(self, msg):
        with self.lock:
            self.received.append(msg)

    def _wait_for_persist(self, timeout=3.0):
        with self.lock:
            self.received = []
        start = time.time()
        while time.time() - start < timeout:
            with self.lock:
                if self.received:
                    return self.received[-1]
            time.sleep(0.02)
        return None

    def test_receive_status(self):
        """Status on log_status -> Persist with type=Status, same fields."""
        msg = Status()
        msg.source = "test_source"
        msg.target = "test_target"
        msg.content = "test_status"
        self.status_pub.publish(msg)

        persisted = self._wait_for_persist()
        assert persisted is not None, "No persist message received"
        assert persisted.source == "test_source"
        assert persisted.target == "test_target"
        assert persisted.type == "Status"
        assert persisted.content == "test_status"

    def test_receive_event(self):
        """Event on log_event -> Persist with type=Event, same fields."""
        msg = Event()
        msg.source = "test_source"
        msg.target = "test_target"
        msg.content = "test_event"
        self.event_pub.publish(msg)

        persisted = self._wait_for_persist()
        assert persisted is not None, "No persist message received"
        assert persisted.source == "test_source"
        assert persisted.target == "test_target"
        assert persisted.type == "Event"
        assert persisted.content == "test_event"

    def test_receive_energy_status(self):
        """EnergyStatus on log_energy_status -> Persist with type=EnergyStatus."""
        msg = EnergyStatus()
        msg.source = "test_source"
        msg.target = "test_target"
        msg.content = "energy:50.0:cost:0.1"
        self.energy_pub.publish(msg)

        persisted = self._wait_for_persist()
        assert persisted is not None, "No persist message received"
        assert persisted.source == "test_source"
        assert persisted.target == "test_target"
        assert persisted.type == "EnergyStatus"
        assert persisted.content == "energy:50.0:cost:0.1"

    def test_receive_uncertainty(self):
        """Uncertainty on log_uncertainty -> Persist with type=Uncertainty."""
        msg = Uncertainty()
        msg.source = "test_source"
        msg.target = "test_target"
        msg.content = "test_uncertainty"
        self.uncertainty_pub.publish(msg)

        persisted = self._wait_for_persist()
        assert persisted is not None, "No persist message received"
        assert persisted.source == "test_source"
        assert persisted.target == "test_target"
        assert persisted.type == "Uncertainty"
        assert persisted.content == "test_uncertainty"

    def test_receive_adaptation_command(self):
        """AdaptationCommand on log_adapt -> Persist with type=AdaptationCommand,
        content = the command's action (not its own content field - Logger.cpp
        copies msg->action into persistMsg.content for this one message type)."""
        msg = AdaptationCommand()
        msg.source = "test_source"
        msg.target = "test_target"
        msg.action = "freq=2.50"
        self.adapt_pub.publish(msg)

        persisted = self._wait_for_persist()
        assert persisted is not None, "No persist message received"
        assert persisted.source == "test_source"
        assert persisted.target == "test_target"
        assert persisted.type == "AdaptationCommand"
        assert persisted.content == "freq=2.50"

    def test_receive_adaptation_command_relays_to_reconfigure(self):
        """AdaptationCommand on log_adapt is also relayed onto 'reconfigure'
        unchanged (Logger.cpp: persist.publish(persistMsg); adapt.publish(msg))."""
        reconfigure_messages = []
        reconfigure_sub = rospy.Subscriber(
            "reconfigure",
            AdaptationCommand,
            lambda m: reconfigure_messages.append(m),
        )
        time.sleep(CONNECTION_WAIT)

        try:
            msg = AdaptationCommand()
            msg.source = "test_source"
            msg.target = "test_target"
            msg.action = "freq=3.00"
            self.adapt_pub.publish(msg)

            assert wait_for(lambda: len(reconfigure_messages) > 0, 3.0), (
                "AdaptationCommand was not relayed onto 'reconfigure'"
            )
            assert reconfigure_messages[-1].source == "test_source"
            assert reconfigure_messages[-1].target == "test_target"
            assert reconfigure_messages[-1].action == "freq=3.00"
        finally:
            reconfigure_sub.unregister()

    def test_multiple_messages_get_independent_timestamps(self):
        """Each Persist record gets its own timestamp (now() - time_ref), not
        a shared/stale one."""
        msg = Status()
        msg.source = "test_source"
        msg.target = "test_target"
        msg.content = "first"
        self.status_pub.publish(msg)
        first = self._wait_for_persist()
        assert first is not None

        time.sleep(0.2)

        msg.content = "second"
        self.status_pub.publish(msg)
        second = self._wait_for_persist()
        assert second is not None

        assert second.timestamp > first.timestamp, (
            "Second persisted message should have a later timestamp than the first"
        )
