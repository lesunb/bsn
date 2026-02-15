import pytest
import rospy
import rostopic
import ros_pytest
from std_msgs.msg import String, Float64
from asserts import is_node_publishing_to_topics, Command, TIMEOUT_SECONDS
from parsers import get_rostopic_sensor_data, get_rosnode_info
from messages.msg import SensorData
from archlib.msg import Uncertainty, Status
import subprocess
import threading
from services.srv import PatientData, PatientDataResponse, PatientDataRequest
import rosnode
import rosservice
import time
import math

SENSORS = ['/g3t1_1', '/g3t1_2', '/g3t1_3', '/g3t1_4', '/g3t1_5', '/g3t1_6']
low_risk_value_dict = {
    'oxigenation': 90.0,
    'heart_rate': 90.0,
    'temperature': 37.0,
    'abps': 100.0,
    'abpd': 70.0,
    'glucose': 90.0
}
high_risk_value_dict = {
    'oxigenation': 50.0,
    'heart_rate': 120.0,
    'temperature': 45.0,
    'abps': 250.0,
    'abpd': 95.0,
    'glucose': 200.0
}
mid_risk_value_dict = {
    'oxigenation': 60,
    'heart_rate': 100.0,
    'temperature': 40.0,
    'abps': 130.0,
    'abpd': 85.0,
    'glucose': 100.0
}
out_of_range_value_dict = {
    'oxigenation': 101,
    'heart_rate': 301,
    'temperature': 51.0,
    'abps': 301.0,
    'abpd': 305.0,
    'glucose': 301.0
}
low_risk_threshold_dict = 20
high_risk_threshold_dict = 66

class SharedSensorTests:
    """Shared test methods for sensor testing"""

    @staticmethod
    def assert_sensors_are_publishing_data(node, topic_name):
        """Assert that sensors are actively publishing data"""
        is_publishing, missing_topics = is_node_publishing_to_topics(node, topic_name)
        assert is_publishing, "{} is missing data from these topics: {}".format(node, missing_topics)
    
    @staticmethod
    def assert_topic_has_data(sensor_topic_name, timeout=5.0):
        """Assert that a topic is publishing data within a timeout period"""
        try:
            sensor_data = {}
            cmd = ['rostopic', 'echo', sensor_topic_name, '-n', '1']
            topic_executor = Command(cmd)
            stdout_bytes, stderr_bytes, returncode = topic_executor.run(timeout=TIMEOUT_SECONDS)
            sensor_data[sensor_topic_name] = get_rostopic_sensor_data(returncode, stdout_bytes, stderr_bytes)
            assert sensor_data[sensor_topic_name]['data'], "No data published on topic {}".format(sensor_topic_name)
        except Exception as e:
            if str(e) == "TimeoutExpired":
                raise AssertionError("Timeout: No data published on topic {}".format(sensor_topic_name))
            else:
                raise

    @classmethod
    def setup_class(cls):
        """Initialize ROS node for testing"""          
        cls.received_messages = []
        cls.serviceCount = []
        cls.message_lock = threading.Lock()

        rospy.init_node('node_test')
        
        service_name = "getPatientData"
        cls.patient_service_server = rospy.Service(
            service_name, 
            PatientData, 
            cls.mock_patient_data_service_callback 
        )
        rospy.sleep(0.1) 
        rospy.loginfo("Servico '{}' mockado iniciado para teste.".format(service_name))
    
    def setup_method(self):
        """Setup for each test method"""
        self.received_messages = []
        self.subscriber = rospy.Subscriber(
            self.topic, 
            SensorData, 
            self.message_callback
        )
        time.sleep(0.1)  
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.subscriber.unregister()
        self.received_messages = []

        if self.patient_service_server is not None:
            self.patient_service_server.shutdown("Testes concluidos.")
        
        rospy.loginfo("Servico de mock desligado.")

    @staticmethod
    def mock_patient_data_service_callback(req):
        """
        Funcao callback que simula a logica do servidor.
        Recebe a requisicao (PatientData) e retorna uma Resposta de Low Risk (PatientDataResponse).
        """
        rospy.loginfo("Servico 'getPatientData' chamado no teste: {}".format(req.vitalSign))
        
        res = PatientDataResponse()
        res.data = low_risk_value_dict[req.vitalSign]
        return res

    @staticmethod
    def mock_patient_data_service_with_high_risk_callback(req):
        """
        Funcao callback que simula a logica do servidor.
        Recebe a requisicao (PatientData) e retorna uma Resposta de High Risk (PatientDataResponse).
        """
        rospy.loginfo("Servico 'getPatientData' (High risk) chamado no teste: {}".format(req.vitalSign))
        
        res = PatientDataResponse()
        res.data = high_risk_value_dict[req.vitalSign]
        return res
    
    @staticmethod
    def mock_patient_data_service_with_mid_risk_callback(req):
        """
        Funcao callback que simula a logica do servidor.
        Recebe a requisicao (PatientData) e retorna uma Resposta de Mid Risk (PatientDataResponse).
        """
        rospy.loginfo("Servico 'getPatientData' (Mid risk) chamado no teste: {}".format(req.vitalSign))
        
        res = PatientDataResponse()
        res.data = mid_risk_value_dict[req.vitalSign]
        return res

    @staticmethod
    def mock_patient_data_service_with_out_of_range_callback(req):
        """
        Funcao callback que simula a logica do servidor.
        Recebe a requisicao (PatientData) e retorna uma Resposta de Out of Range (PatientDataResponse).
        """
        rospy.loginfo("Servico 'getPatientData' (Out of range) chamado no teste: {}".format(req.vitalSign))
        
        res = PatientDataResponse()
        res.data = out_of_range_value_dict[req.vitalSign]
        return res

    @staticmethod
    def mock_patient_data_service_with_unknown_callback(req):
        """
        Funcao callback que simula a logica do servidor.
        Recebe a requisicao (PatientData) e retorna uma Resposta de Unknown (PatientDataResponse).
        """
        rospy.loginfo("Servico 'getPatientData' (Unknown) chamado no teste: {}".format(req.vitalSign))

        res = PatientDataResponse()
        res.data = -1
        return res
    
    def message_callback(self, msg):
        """Callback for receiving messages from the sensor"""
        print("Mensagem recebida no topico {}: data={}".format(self.topic, msg.data))
        with self.message_lock:
            self.received_messages.append(msg)
    
    def wait_for_message(self, timeout=2.0):
        """Wait for a message to be received"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.message_lock:
                if self.received_messages:
                    return self.received_messages[-1]
            time.sleep(0.01)
        return None

    def wait_for_status(self, status_messages, status_lock, timeout=2.0, matcher=None):
        """Wait for a status message to be received"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            with status_lock:
                if status_messages:
                    if matcher is None:
                        return status_messages[-1]
                    for msg in status_messages:
                        if matcher(msg):
                            return msg
            time.sleep(0.01)
        return None

    def test_transfer_with_low_risk_data(self):
        """Test transfer with low risk data"""
        test_data = low_risk_value_dict[self.vital_sign]
        received_msg = self.wait_for_message()
        print("Received message: {}".format(received_msg.risk))
        assert received_msg is not None
        assert received_msg.risk < low_risk_threshold_dict
        assert received_msg.data == test_data

    @pytest.fixture
    def mock_high_risk_service(self):
        """Fixture to setup high risk service mock"""
        if self.patient_service_server is not None:
            self.patient_service_server.shutdown("Reconfigurando para high risk.")
            rospy.sleep(0.1)
        service_name = "getPatientData"
        self.patient_service_server = rospy.Service(
            service_name, 
            PatientData, 
            self.mock_patient_data_service_with_high_risk_callback 
        )
        rospy.wait_for_service(service_name)
        rospy.sleep(1)

        self.subscriber = rospy.Subscriber(
            self.topic, 
            SensorData, 
            self.message_callback
        )
        print("High risk service mock setup complete.")
        time.sleep(1)  
        yield

    def test_transfer_with_high_risk_data(self, mock_high_risk_service):
        """Test transfer with high risk  data"""
        test_data = high_risk_value_dict[self.vital_sign]
        received_msg = self.wait_for_message()
        
        assert received_msg is not None
        assert received_msg.risk > high_risk_threshold_dict
        assert received_msg.data == test_data

    @pytest.fixture
    def mock_mid_risk_service(self):
        """Fixture to setup mid risk service mock"""
        if self.patient_service_server is not None:
            self.patient_service_server.shutdown("Reconfigurando para mid risk.")
            rospy.sleep(0.1)
        service_name = "getPatientData"
        self.patient_service_server = rospy.Service(
            service_name, 
            PatientData, 
            self.mock_patient_data_service_with_mid_risk_callback 
        )
        rospy.wait_for_service(service_name)
        rospy.sleep(1)

        self.subscriber = rospy.Subscriber(
            self.topic, 
            SensorData, 
            self.message_callback
        )

        print("Mid risk service mock setup complete.")
        time.sleep(1)  
        yield

    def test_transfer_with_mid_risk_data(self, mock_mid_risk_service):
        """Test transfer with mid risk  data"""
        test_data = mid_risk_value_dict[self.vital_sign]
        received_msg = self.wait_for_message()
        print("Received message: {}, {}".format(received_msg.risk, test_data))
        assert received_msg is not None
        assert received_msg.risk > low_risk_threshold_dict and received_msg.risk < high_risk_threshold_dict
        assert received_msg.data == test_data

    @pytest.fixture
    def mock_out_of_range_service(self):
        """Fixture to setup out of range service mock"""
        if self.patient_service_server is not None:
            self.patient_service_server.shutdown("Reconfigurando para out of range.")
            rospy.sleep(0.1)
        service_name = "getPatientData"
        self.patient_service_server = rospy.Service(
            service_name, 
            PatientData, 
            self.mock_patient_data_service_with_out_of_range_callback
        )
        rospy.wait_for_service(service_name)
        rospy.sleep(1)

        self.subscriber = rospy.Subscriber(
            self.topic, 
            SensorData, 
            self.message_callback
        )
        print("Out of range service mock setup complete.")
        time.sleep(1)  
        yield

    def test_transfer_with_out_of_range_data(self, mock_out_of_range_service):
        """Test transfer with out of range data"""
        received_msg = self.wait_for_message()
        assert received_msg is None

    @pytest.fixture
    def mock_unknown_service(self):
        """Fixture to setup unknown service mock"""
        if self.patient_service_server is not None:
            self.patient_service_server.shutdown("Reconfigurando para unknown.")
            rospy.sleep(0.1)
        service_name = "getPatientData"
        self.patient_service_server = rospy.Service(
            service_name, 
            PatientData, 
            self.mock_patient_data_service_with_unknown_callback
        )
        rospy.wait_for_service(service_name)
        rospy.sleep(1)

        self.subscriber = rospy.Subscriber(
            self.topic, 
            SensorData, 
            self.message_callback
        )
        print("Out of range service mock setup complete.")
        time.sleep(1)  
        yield

    def test_transfer_with_unknown_data(self, mock_unknown_service):
        """Test transfer with unknown data (out of range)"""
        received_msg = self.wait_for_message()
        assert received_msg is None or math.isnan(received_msg.risk) or received_msg.risk == -1, "Expected risk to be NaN or -1 for unknown data, got {}".format(received_msg.risk)

    def test_transfer_with_accuracy_fail(self, mock_mid_risk_service):
        """Test transfer with accuracy fail (label mismatch)"""
        if self.vital_sign != 'oxigenation':
            pytest.skip("Accuracy fail test only applies to g3t1_1")

        status_messages = []
        status_lock = threading.Lock()

        def status_callback(msg):
            with status_lock:
                status_messages.append(msg)

        status_subscriber = rospy.Subscriber(
            "collect_status",
            Status,
            status_callback
        )

        received_msg = self.wait_for_message()
        assert received_msg is not None

        uncertainty_topics = ["uncertainty_g3t1_1", "uncertainty_/g3t1_1"]
        uncertainty_pubs = [
            rospy.Publisher(topic, Uncertainty, queue_size=10)
            for topic in uncertainty_topics
        ]
        time.sleep(0.2)

        uncertainty_msg = Uncertainty()
        uncertainty_msg.source = "test"
        uncertainty_msg.target = "g3t1_1"
        uncertainty_msg.content = "noise_factor=0.3"

        for _ in range(3):
            for publisher in uncertainty_pubs:
                publisher.publish(uncertainty_msg)
            time.sleep(0.2)

        status_msg = self.wait_for_status(
            status_messages,
            status_lock,
            timeout=6.0,
            matcher=lambda msg: msg.source.endswith("g3t1_1") and msg.content == "fail"
        )
        status_subscriber.unregister()

        assert status_msg is not None
        assert status_msg.source.endswith("g3t1_1")
        assert status_msg.content == "fail"

        
    def test_battery_consumption(self, mock_mid_risk_service):
        """Test that battery level decreases after operations"""
        received_msg1 = self.wait_for_message()
        assert received_msg1 is not None
        initial_battery = received_msg1.batt
        
        # Wait for next message
        time.sleep(0.5)
        del self.received_messages[:]
        received_msg2 = self.wait_for_message()
        
        if received_msg2 is not None:
            # Battery should decrease or stay same (if instant recharge)
            assert received_msg2.batt <= initial_battery

    # def test_service_integration(self):
    #     """Test that sensor properly integrates with patient data service"""
    #     received_msg = self.wait_for_message(timeout=3.0)
        
    #     assert received_msg is not None
    #     # Data should come from the mocked service
    #     assert received_msg.data == low_risk_value_dict[self.vital_sign]
