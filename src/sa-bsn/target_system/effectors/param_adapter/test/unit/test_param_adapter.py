# -*- coding: utf-8 -*-
"""Unit tests for the `param_adapter` node (ParamAdapter.cpp); equivalent to bsn_ros2/system_monitor/test/test_param_adapter.py.
Driven through its real ROS interface (EffectorRegister service + reconfigure/reconfigure_<name> topics). Unlike the ROS2 port, this
node does no BSN-name translation or slash normalization: target_arr is keyed by exactly the name a component registered with."""
import time

import rospy
from archlib.msg import AdaptationCommand
from archlib.srv import EffectorRegister

CONNECTION_WAIT = 0.5


def wait_for(condition_function, timeout=5.0):
    """Wait for a condition function to become true or timeout."""
    start_time = time.time()
    while time.time() < start_time + timeout:
        if condition_function():
            return True
        time.sleep(0.05)
    return False


class TestParamAdapter:
    """Tests for the `param_adapter` node."""

    @classmethod
    def setup_class(cls):
        rospy.init_node("test_param_adapter_node", anonymous=True)
        rospy.wait_for_service("EffectorRegister", timeout=10.0)
        cls.register = rospy.ServiceProxy("EffectorRegister", EffectorRegister)

    def setup_method(self):
        self.command_pub = rospy.Publisher(
            "reconfigure", AdaptationCommand, queue_size=10
        )
        time.sleep(CONNECTION_WAIT)

    def teardown_method(self):
        self.command_pub.unregister()

    def _register(self, name, connection=True):
        response = self.register(name=name, connection=connection)
        return response.ACK

    def test_register_component(self):
        """A component registering should get ACK=True and a
        reconfigure_<name> topic should come into existence."""
        assert self._register("test_component_register") is True
        # Give the newly-advertised topic a moment to show up in the graph.
        time.sleep(0.2)
        published_topics = [name for name, _ in rospy.get_published_topics()]
        assert "/reconfigure_test_component_register" in published_topics

    def test_deregister_component(self):
        """Deregistering an unknown-but-just-registered component also ACKs True (moduleConnect only fails on an exception,
        e.g. erasing a name that was never registered)."""
        assert self._register("test_component_deregister", connection=True) is True
        assert self._register("test_component_deregister", connection=False) is True

    def test_command_routed_to_registered_component(self):
        """A command whose target matches a registered component's name is
        forwarded, unchanged, on reconfigure_<name>."""
        component = "test_target_routed"
        assert self._register(component) is True

        received = []
        sub = rospy.Subscriber(
            "reconfigure_" + component,
            AdaptationCommand,
            lambda m: received.append(m),
        )
        time.sleep(CONNECTION_WAIT)

        try:
            msg = AdaptationCommand()
            msg.source = "test_source"
            msg.target = component
            msg.action = "test_action"
            self.command_pub.publish(msg)

            assert wait_for(lambda: len(received) > 0, 3.0), "No command routed"
            assert received[-1].source == "test_source"
            assert received[-1].target == component
            assert received[-1].action == "test_action"
        finally:
            sub.unregister()

    def test_command_for_unknown_target_is_not_routed_anywhere(self):
        """A command whose target was never registered is just logged and dropped (no topic to assert on); this only checks
        the node keeps running."""
        msg = AdaptationCommand()
        msg.source = "test_source"
        msg.target = "definitely_never_registered"
        msg.action = "test_action"
        self.command_pub.publish(msg)
        time.sleep(0.3)

        published_topics = [name for name, _ in rospy.get_published_topics()]
        assert "/reconfigure_definitely_never_registered" not in published_topics
