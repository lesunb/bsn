import rospy
import threading
import time
from archlib.msg import AdaptationCommand, Status
from messages.msg import SensorData
from services.srv import PatientData
from test_sensor import SharedSensorTests


class TestSensorCore(SharedSensorTests):
    """Sensor.cpp-focused tests (generic sensor behavior) using g3t1_1 as execution target."""

    topic = 'oximeter_data'
    vital_sign = 'oxigenation'

    def test_collect_handles_patient_service_failure(self):
        """Cover collect() branch when getPatientData call fails (Sensor.cpp generic behavior)."""
        if self.patient_service_server is not None:
            self.patient_service_server.shutdown("Simulando indisponibilidade do getPatientData")
            self.patient_service_server = None

        with self.message_lock:
            del self.received_messages[:]

        received_msg = self.wait_for_message(timeout=2.5)
        assert received_msg is not None
        assert received_msg.data == 0.0

        # Restore default mock service to avoid impacting following tests.
        self.patient_service_server = rospy.Service(
            "getPatientData",
            PatientData,
            self.mock_patient_data_service_callback,
        )
        rospy.sleep(0.1)

    def _ensure_patient_service(self):
        if self.patient_service_server is None:
            self.patient_service_server = rospy.Service(
                "getPatientData",
                PatientData,
                self.mock_patient_data_service_callback,
            )
            rospy.sleep(0.1)

    @staticmethod
    def _publish_reconfigure(action, repeats=3):
        reconfigure_topics = ["reconfigure_g3t1_1", "reconfigure_/g3t1_1"]
        publishers = [
            rospy.Publisher(topic, AdaptationCommand, queue_size=10)
            for topic in reconfigure_topics
        ]
        rospy.sleep(0.2)

        command = AdaptationCommand()
        command.source = "test"
        command.target = "g3t1_1"
        command.action = action

        for _ in range(repeats):
            for publisher in publishers:
                publisher.publish(command)
            time.sleep(0.1)

    def test_reconfigure_frequency_command_increases_publish_rate(self):
        """Cover Sensor::reconfigure(freq) by observing faster output cadence."""
        sample_times = []
        sample_lock = threading.Lock()

        def timed_callback(_msg):
            with sample_lock:
                sample_times.append(time.time())

        timed_subscriber = rospy.Subscriber(self.topic, SensorData, timed_callback)

        self._publish_reconfigure("freq=4")

        timeout = time.time() + 2.2
        while time.time() < timeout:
            with sample_lock:
                if len(sample_times) >= 4:
                    break
            time.sleep(0.05)

        timed_subscriber.unregister()

        with sample_lock:
            assert len(sample_times) >= 4

    def test_reconfigure_replicate_collect_keeps_streaming_data(self):
        """Cover Sensor::reconfigure replicate_collect branch (lines 112-115)."""
        self._ensure_patient_service()

        with self.message_lock:
            del self.received_messages[:]

        self._publish_reconfigure("replicate_collect=3")

        message = self.wait_for_message(timeout=3.0)
        assert message is not None

    def test_out_of_charge_cycle_emits_fail_and_then_recovers(self):
        """Cover turnOff/recharge/turnOn paths via high-frequency battery drain cycle."""
        self._ensure_patient_service()

        status_messages = []
        status_lock = threading.Lock()

        def status_callback(msg):
            with status_lock:
                status_messages.append(msg)

        status_subscriber = rospy.Subscriber("collect_status", Status, status_callback)

        try:
            self._publish_reconfigure("freq=200", repeats=5)

            deadline = time.time() + 25.0
            fail_idx = -1
            recovered = False

            while time.time() < deadline and not recovered:
                with status_lock:
                    local = [m for m in status_messages if m.source.endswith("g3t1_1")]

                for idx, msg in enumerate(local):
                    if fail_idx == -1 and msg.content == "fail":
                        fail_idx = idx
                    if fail_idx != -1 and idx > fail_idx and msg.content == "success":
                        recovered = True
                        break

                if recovered:
                    break
                time.sleep(0.1)

            assert fail_idx != -1
            assert recovered
        finally:
            self._publish_reconfigure("freq=1", repeats=2)
            status_subscriber.unregister()
