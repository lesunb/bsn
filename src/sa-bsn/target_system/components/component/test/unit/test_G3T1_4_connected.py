import threading
import time

import pytest
import rospy
from std_srvs.srv import SetBool, SetBoolResponse

from messages.msg import SensorData
from test_sensor import low_risk_value_dict


class TestG3T1_4ConnectedSensor(object):
    """Tests for G3T1_4 when connected to a real sensor (spo2 service)."""

    topic = "abps_data"

    @classmethod
    def setup_class(cls):
        cls.received_messages = []
        cls.message_lock = threading.Lock()
        cls.service_lock = threading.Lock()
        cls.spo2_service = None
        cls.test_value = low_risk_value_dict["oxigenation"]

        if not rospy.core.is_initialized():
            rospy.init_node("node_test_g3t1_4_connected", anonymous=True)

        cls._start_spo2_service()
        rospy.sleep(0.2)

    @classmethod
    def _start_spo2_service(cls):
        with cls.service_lock:
            if cls.spo2_service is not None:
                return
            cls.spo2_service = rospy.Service("spo2", SetBool, cls._spo2_callback)

    @classmethod
    def _stop_spo2_service(cls):
        with cls.service_lock:
            if cls.spo2_service is not None:
                cls.spo2_service.shutdown("spo2 service stopped for test")
                cls.spo2_service = None

    @classmethod
    def _spo2_callback(cls, _req):
        return SetBoolResponse(success=True, message=str(cls.test_value))

    def setup_method(self):
        self.received_messages = []
        self.subscriber = rospy.Subscriber(self.topic, SensorData, self._message_callback)
        time.sleep(0.2)

    def teardown_method(self):
        self.subscriber.unregister()
        self.received_messages = []
        self._start_spo2_service()
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

    def test_collect_handles_spo2_service_failure(self):
        self._stop_spo2_service()
        with self.message_lock:
            del self.received_messages[:]
        message = self._wait_for_message()
        assert message is not None
