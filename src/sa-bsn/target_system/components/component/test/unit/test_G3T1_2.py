import pytest
from test_sensor import SharedSensorTests

class TestG3T1_2(SharedSensorTests):
    """Test suite for G3T1_2 sensor"""
    topic = 'ecg_data'
    vital_sign = 'heart_rate'
    