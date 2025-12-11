import pytest
from test_sensor import SharedSensorTests

class TestG3T1_4(SharedSensorTests):
    """Test suite for G3T1_4 sensor"""
    topic = 'abps_data'
    vital_sign = 'abps'
    