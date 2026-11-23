from test_sensor_connected import ConnectedSensorTestMixin


class TestG3T1_6ConnectedSensor(ConnectedSensorTestMixin):
    __test__ = True
    topic = "glucosemeter_data"
    connected_service_name = "glucose"
    expected_vital_sign = "glucose"
    expect_connected_value = True
    expect_unknown_label_in_connected = True
    node_name = "node_test_g3t1_6_connected"
