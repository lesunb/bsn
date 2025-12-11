import pytest
from test_sensor import SharedSensorTests

class TestG3T1_1(SharedSensorTests):
    """Test suite for G3T1_1 sensor"""
    topic = 'oximeter_data'
    vital_sign = 'oxigenation'
    