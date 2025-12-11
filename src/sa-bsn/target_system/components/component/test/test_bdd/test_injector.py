import ros_pytest
from pytest_bdd import scenarios, given, when, then, parsers
from test_sensor import SharedSensorTests
import rospy
import rosnode

scenarios("./features/injector.feature")
