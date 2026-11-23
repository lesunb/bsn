from test_sensor_connected import ConnectedSensorTestMixin


class TestG3T1_5ConnectedSensor(ConnectedSensorTestMixin):
    __test__ = True
    topic = "abpd_data"
    connected_service_name = "abpd"
    expected_vital_sign = "abpd"
    expect_connected_value = True
    expect_unknown_label_in_connected = True
    node_name = "node_test_g3t1_5_connected"
