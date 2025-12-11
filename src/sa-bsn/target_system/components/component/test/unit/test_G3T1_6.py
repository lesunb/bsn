import pytest
from test_sensor import SharedSensorTests

class TestG3T1_6(SharedSensorTests):
    """Test suite for G3T1_6 sensor"""
    topic = 'glucosemeter_data'
    vital_sign = 'glucose'
    