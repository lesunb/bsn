# -*- coding: utf-8 -*-
import pytest
import rospy
import time
import threading
from messages.msg import SensorData, TargetSystemData
from asserts import  Command, TIMEOUT_SECONDS

class TestG4T1:
    """Test suite for G4T1 Central Hub component"""
    
    @classmethod
    def setup_class(cls):
        """Initialize ROS node for testing"""
        cls.received_messages = []
        cls.message_lock = threading.Lock()
        rospy.init_node('test_g4t1_node', anonymous=True)
        
    def setup_method(self):
        """Setup for each test method"""
        # Clear old messages with lock
        with self.message_lock:
            self.received_messages = []
        
        # Subscribe to TargetSystemData topic
        self.subscriber = rospy.Subscriber(
            '/TargetSystemData',
            TargetSystemData,
            self.message_callback
        )
        
        # Publisher for sensor data
        self.sensors_pub = {
            'glucosemeter': rospy.Publisher(
                '/glucosemeter_data',
                SensorData,
                queue_size=10
            ),
            'thermometer': rospy.Publisher(
                '/thermometer_data',
                SensorData,
                queue_size=10
            ),
            'ecg': rospy.Publisher(
                '/ecg_data',
                SensorData,
                queue_size=10
            ),
            'oximeter': rospy.Publisher(
                '/oximeter_data',   
                SensorData,
                queue_size=10
            ),
            'abps': rospy.Publisher(
                '/abps_data',
                SensorData,
                queue_size=10
            ),
            'abpd': rospy.Publisher(
                '/abpd_data',
                SensorData,
                queue_size=10
            ),
        }
        self.sensor_pub = rospy.Publisher(
            '/SensorData',
            SensorData,
            queue_size=10
        )
        
        time.sleep(0.5)  # Wait for connections to establish
        
    def teardown_method(self):
        """Cleanup after each test"""
        self.subscriber.unregister()
        self.sensor_pub.unregister()
        
        # Clear with lock to ensure thread-safety
        with self.message_lock:
            self.received_messages = []
        
    def message_callback(self, msg):
        """Callback for receiving TargetSystemData messages"""
        with self.message_lock:
            self.received_messages.append(msg)
            
    def wait_for_message(self, timeout=3.0, clear_old=True):
        """Wait for a message to be received
        
        Args:
            timeout: Maximum time to wait for message
            clear_old: If True, clears old messages before waiting (default: True)
        """
        if clear_old:
            with self.message_lock:
                self.received_messages = []
            time.sleep(0.2)  # Small delay to allow new messages to arrive
    
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.message_lock:
                if self.received_messages:
                    return self.received_messages[-1]
            time.sleep(0.01)
        return None
    
    def publish_sensor_data(self, sensor_type, risk_value, data_value, batt_value=100.0):
        """Helper to publish sensor data"""
        msg = SensorData()
        msg.type = sensor_type
        msg.risk = risk_value
        msg.data = data_value
        msg.batt = batt_value
        self.sensors_pub[sensor_type].publish(msg)
        time.sleep(0.1)

    # Test collect() method
    def test_collect_thermometer_data(self):
        """Test collecting thermometer sensor data"""
        self.publish_sensor_data('thermometer', 15.0, 36.5, 95.0)

        rospy.sleep(0.5)  # Allow time for processing
        received_msg = self.wait_for_message()

        assert received_msg is not None
        assert received_msg.trm_risk == 15.0
        assert received_msg.trm_data == 36.5
        assert received_msg.trm_batt == 95.0

    # Test transfer() with different risk scenarios
    def test_transfer_very_low_risk_patient(self):
        """Test transfer with very low risk patient (<=20)"""
        sensors = ['thermometer', 'ecg', 'oximeter', 'abps', 'abpd', 'glucosemeter']
        for sensor in sensors:
            self.publish_sensor_data(sensor, 10.0, 100.0, 95.0)
        
        rospy.sleep(1.5)
        received_msg = self.wait_for_message(clear_old=False)
        assert received_msg is not None
        # 10.0 * 0.833 = 8.33
        assert received_msg.patient_status <= 20.0, \
            "patient_status expected <=20, received: {}".format(received_msg.patient_status)
        
    def test_transfer_low_risk_patient(self):
        """Test transfer with low risk patient (20-40)"""
        sensors = ['thermometer', 'ecg', 'oximeter', 'abps', 'abpd', 'glucosemeter']
        for sensor in sensors:
            self.publish_sensor_data(sensor, 35.0, 100.0, 90.0)  # 35 * 0.833 = 29.16
        
        rospy.sleep(1.5)
        received_msg = self.wait_for_message(clear_old=False)
        assert received_msg is not None
        assert 20.0 < received_msg.patient_status <= 40.0, \
            "patient_status expected 20-40, received: {}".format(received_msg.patient_status)
        
    def test_transfer_moderate_risk_patient(self):
        """Test transfer with moderate risk patient (40-60)"""
        sensors = ['thermometer', 'ecg', 'oximeter', 'abps', 'abpd', 'glucosemeter']

        # 55.0 * 0.833 = 45.8 (dentro de 40-60)
        for sensor in sensors:
            self.publish_sensor_data(sensor, 55.0, 100.0, 85.0)

        rospy.sleep(1.5)
        received_msg = self.wait_for_message(clear_old=False)
        assert received_msg is not None, "No message received"

        # Verify all sensors were processed
        assert received_msg.trm_risk == 55.0
        assert received_msg.ecg_risk == 55.0
        assert received_msg.oxi_risk == 55.0
        assert received_msg.abps_risk == 55.0
        assert received_msg.abpd_risk == 55.0
        assert received_msg.glc_risk == 55.0

        # Verify patient_status is in moderate range
        assert 40.0 < received_msg.patient_status <= 60.0, \
            "patient_status expected 40-60, received: {}".format(received_msg.patient_status)
        
    def test_transfer_critical_risk_patient(self):
        """Test transfer with critical risk patient (60-80)"""
        sensors = ['thermometer', 'ecg', 'oximeter', 'abps', 'abpd', 'glucosemeter']
        for sensor in sensors:
            self.publish_sensor_data(sensor, 85.0, 100.0, 80.0)  # 85 * 0.833 = 70.8
        
        rospy.sleep(1.5)
        received_msg = self.wait_for_message(clear_old=False)
        assert received_msg is not None
        assert 60.0 < received_msg.patient_status <= 80.0, \
            "patient_status expected 60-80, received: {}".format(received_msg.patient_status)
        
    def test_transfer_very_critical_risk_patient(self):
        """Test transfer with very critical risk patient (>80)"""
        sensors = ['thermometer', 'ecg', 'oximeter', 'abps', 'abpd', 'glucosemeter']
        for sensor in sensors:
            self.publish_sensor_data(sensor, 100.0, 100.0, 75.0)  # 100 * 0.833 = 83.3
        
        rospy.sleep(1.5)
        received_msg = self.wait_for_message(clear_old=False)
        assert received_msg is not None
        assert received_msg.patient_status > 80.0, \
            "patient_status expected >80, received: {}".format(received_msg.patient_status)

    def test_transfer_mixed_risk_levels(self):
        """Test transfer with different risk levels across sensors"""
        self.publish_sensor_data('thermometer', 10.0, 36.8, 95.0)
        self.publish_sensor_data('ecg', 50.0, 110.0, 90.0)
        self.publish_sensor_data('oximeter', 80.0, 88.0, 85.0)
        self.publish_sensor_data('abps', 15.0, 115.0, 80.0)
        self.publish_sensor_data('abpd', 45.0, 95.0, 75.0)
        self.publish_sensor_data('glucosemeter', 30.0, 120.0, 70.0)
        
        rospy.sleep(1.5)
        received_msg = self.wait_for_message(clear_old=False)
        assert received_msg is not None
        assert 0 <= received_msg.patient_status <= 100.0
        
    def test_transfer_all_sensor_data_fields(self):
        """Test that all sensor data fields are transferred correctly"""
        self.publish_sensor_data('thermometer', 15.0, 37.0, 95.0)
        self.publish_sensor_data('ecg', 20.0, 75.0, 90.0)
        self.publish_sensor_data('oximeter', 18.0, 96.0, 85.0)
        self.publish_sensor_data('abps', 22.0, 120.0, 80.0)
        self.publish_sensor_data('abpd', 19.0, 80.0, 75.0)
        self.publish_sensor_data('glucosemeter', 25.0, 100.0, 70.0)
        
        rospy.sleep(1.5)
        received_msg = self.wait_for_message(clear_old=False)
        assert received_msg is not None, "No message received"
        
        # Check risk values
        assert received_msg.trm_risk == 15.0, "trm_risk: expected 15.0, received {}".format(received_msg.trm_risk)
        assert received_msg.ecg_risk == 20.0, "ecg_risk: expected 20.0, received {}".format(received_msg.ecg_risk)
        assert received_msg.oxi_risk == 18.0, "oxi_risk: expected 18.0, received {}".format(received_msg.oxi_risk)
        assert received_msg.abps_risk == 22.0, "abps_risk: expected 22.0, received {}".format(received_msg.abps_risk)
        assert received_msg.abpd_risk == 19.0, "abpd_risk: expected 19.0, received {}".format(received_msg.abpd_risk)
        assert received_msg.glc_risk == 25.0, "glc_risk: expected 25.0, received {}".format(received_msg.glc_risk)
        
        # Check raw data values
        assert received_msg.trm_data == 37.0
        assert received_msg.ecg_data == 75.0
        assert received_msg.oxi_data == 96.0
        assert received_msg.abps_data == 120.0
        assert received_msg.abpd_data == 80.0
        assert received_msg.glc_data == 100.0
        
        # Check battery values
        assert received_msg.trm_batt == 95.0
        assert received_msg.ecg_batt == 90.0
        assert received_msg.oxi_batt == 85.0
        assert received_msg.abps_batt == 80.0
        assert received_msg.abpd_batt == 75.0
        assert received_msg.glc_batt == 70.0

    # Test boundary conditions
    def test_collect_zero_risk_data(self):
        """Test collecting data with zero risk"""
        self.publish_sensor_data('thermometer', 0.0, 36.5, 100.0)
        time.sleep(0.5)
        
        received_msg = self.wait_for_message()
        assert received_msg is not None, "No message received"
        assert received_msg.trm_risk == 0.0, "Expected 0.0, received {}".format(received_msg.trm_risk)
        
    def test_collect_maximum_risk_data(self):
        """Test collecting data with maximum risk (100)"""
        self.publish_sensor_data('ecg', 100.0, 150.0, 50.0)
        received_msg = self.wait_for_message()
        assert received_msg is not None
        assert received_msg.ecg_risk == 100.0
        
    def test_collect_low_battery_data(self):
        """Test collecting data with low battery level"""
        self.publish_sensor_data('oximeter', 20.0, 95.0, 10.0)
        time.sleep(0.5)
    
        received_msg = self.wait_for_message()
        assert received_msg is not None, "No message received"
        assert received_msg.oxi_batt == 10.0, "Expected 10.0, received {}".format(received_msg.oxi_batt)

    def test_collect_uncertainty_like_oximeter_data(self):
        """Moved from sensor-side: validate central hub collection with perturbed datapoint."""
        self.publish_sensor_data('oximeter', 15.0, 85.5, 88.0)
        rospy.sleep(0.5)

        received_msg = self.wait_for_message()
        assert received_msg is not None, "No message received"
        assert received_msg.oxi_risk == 15.0
        assert received_msg.oxi_data == 85.5
        assert received_msg.oxi_batt == 88.0

    # Test sequential data collection
    def test_sequential_sensor_updates(self):
        """Test that sensor data is updated sequentially"""
        # First update
        self.publish_sensor_data('thermometer', 10.0, 36.5, 95.0)
        msg1 = self.wait_for_message()
        assert msg1.trm_risk == 10.0
        
        # Second update with different value
        self.received_messages = []
        self.publish_sensor_data('thermometer', 30.0, 38.0, 90.0)
        msg2 = self.wait_for_message()
        assert msg2.trm_risk == 30.0
        assert msg2.trm_data == 38.0