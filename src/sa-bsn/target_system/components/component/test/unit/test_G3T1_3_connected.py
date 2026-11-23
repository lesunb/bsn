from test_sensor_connected import ConnectedSensorTestMixin


class TestG3T1_3ConnectedSensor(ConnectedSensorTestMixin):
    __test__ = True
    topic = "thermometer_data"
    connected_service_name = "temp"
    expected_vital_sign = "temperature"
    expect_connected_value = True
    expect_unknown_label_in_connected = True
    node_name = "node_test_g3t1_3_connected"

