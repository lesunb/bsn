import pytest
from test_sensor import SharedSensorTests

class TestG3T1_3(SharedSensorTests):
    """Test suite for G3T1_3 sensor"""
    topic = 'thermometer_data'
    vital_sign = 'temperature'
    