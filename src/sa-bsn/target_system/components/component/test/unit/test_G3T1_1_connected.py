from test_sensor_connected import ConnectedSensorTestMixin


class TestG3T1_1ConnectedSensor(ConnectedSensorTestMixin):
    __test__ = True
    topic = "oximeter_data"
    connected_service_name = "spo2"
    expected_vital_sign = "oxigenation"
    expect_connected_value = True
    expect_unknown_label_in_connected = True
    node_name = "node_test_g3t1_1_connected"
