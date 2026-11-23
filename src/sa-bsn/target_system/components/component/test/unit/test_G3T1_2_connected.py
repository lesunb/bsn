from test_sensor_connected import ConnectedSensorTestMixin


class TestG3T1_2ConnectedSensor(ConnectedSensorTestMixin):
    __test__ = True
    topic = "ecg_data"
    connected_service_name = "bpm"
    expected_vital_sign = "heart_rate"
    expect_connected_value = True
    expect_unknown_label_in_connected = True
    node_name = "node_test_g3t1_2_connected"
