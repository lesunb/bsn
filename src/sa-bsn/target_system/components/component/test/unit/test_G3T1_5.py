import pytest
from test_sensor import SharedSensorTests

class TestG3T1_5(SharedSensorTests):
    """Test suite for G3T1_5 sensor"""
    topic = 'abpd_data'
    vital_sign = 'abpd'
    node_name = 'g3t1_5'
    