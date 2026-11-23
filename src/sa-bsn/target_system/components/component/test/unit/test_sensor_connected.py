import threading
import time
import math

import pytest
import rospy
from std_srvs.srv import SetBool, SetBoolResponse

from messages.msg import SensorData
from test_sensor import low_risk_value_dict


class ConnectedSensorTestMixin(object):
    """Shared connected-sensor behavior tests."""

    __test__ = False

    topic = None
    connected_service_name = None
    expected_vital_sign = None
    expect_connected_value = True
    expect_unknown_label_in_connected = False
    node_name = "node_test_sensor_connected"

    @classmethod
    def setup_class(cls):
        cls.received_messages = []
        cls.message_lock = threading.Lock()
        cls.service_lock = threading.Lock()
        cls.connected_service = None
        cls.test_value = (
            low_risk_value_dict[cls.expected_vital_sign]
            if cls.expected_vital_sign in low_risk_value_dict
            else 0.0
        )

        if not rospy.core.is_initialized():
            rospy.init_node(cls.node_name, anonymous=True)

        cls._start_connected_service()
        rospy.sleep(0.2)

    @classmethod
    def _start_connected_service(cls):
        if not cls.connected_service_name:
            return
        with cls.service_lock:
            if cls.connected_service is not None:
                return
            cls.connected_service = rospy.Service(
                cls.connected_service_name, SetBool, cls._connected_callback
            )

    @classmethod
    def _stop_connected_service(cls):
        if not cls.connected_service_name:
            return
        with cls.service_lock:
            if cls.connected_service is not None:
                cls.connected_service.shutdown(
                    "{} service stopped for test".format(cls.connected_service_name)
                )
                cls.connected_service = None

    @classmethod
    def _connected_callback(cls, _req):
        return SetBoolResponse(success=True, message=str(cls.test_value))

    def setup_method(self):
        self.received_messages = []
        self.subscriber = rospy.Subscriber(self.topic, SensorData, self._message_callback)
        time.sleep(0.2)

    def teardown_method(self):
        self.subscriber.unregister()
        self.received_messages = []
        self._start_connected_service()
        time.sleep(0.1)

    def _message_callback(self, msg):
        with self.message_lock:
            self.received_messages.append(msg)

    def _wait_for_message(self, timeout=3.0):
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.message_lock:
                if self.received_messages:
                    return self.received_messages[-1]
            time.sleep(0.01)
        return None

    def _wait_for_message_value(self, expected_value, timeout=5.0, eps=1e-6):
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.message_lock:
                for msg in reversed(self.received_messages):
                    if abs(msg.data - expected_value) <= eps:
                        return msg
            time.sleep(0.01)
        return None

    def test_collect_uses_connected_service_value(self):
        if not self.expect_connected_value:
            pytest.skip("sensor does not use connected service path in collect()")

        message = self._wait_for_message()
        assert message is not None
        assert message.data == self.test_value

    def test_collect_handles_connected_service_failure(self):
        if not self.connected_service_name:
            pytest.skip("no connected service configured for this sensor")

        self._stop_connected_service()
        with self.message_lock:
            del self.received_messages[:]

        # Give the sensor at least one collection cycle with the service down.
        time.sleep(1.2)

        # The expected behavior is graceful recovery once the service is back.
        self._start_connected_service()

        message = self._wait_for_message_value(self.test_value, timeout=5.0)
        assert message is not None
        assert message.data == self.test_value

    def test_transfer_with_unknown_label_in_connected_mode(self):
        if not self.expect_unknown_label_in_connected:
            pytest.skip("unknown-label check not enabled for this sensor connected test")

        message = self._wait_for_message()
        assert message is not None
        assert math.isnan(message.risk)
