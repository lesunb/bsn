#!/usr/bin/env python2

from behave import given, when, then
import rospy
from std_msgs.msg import String
import subprocess
import time
received_message = None

def message_callback(msg):
    global received_message
    received_message = msg.data

@given('ROS is running')
def step_impl(context):
    """ Ensure ROS is initialized. """
    if not rospy.core.is_initialized():
        rospy.init_node('bdd_test_node', anonymous=True)

@when('I publish a message to "/test_topic"')
def step_impl(context):
    """ Publish a message to a ROS topic. """
    global received_message
    received_message = None  # Reset message
    
    pub = rospy.Publisher('/test_topic', String, queue_size=10)
    sub = rospy.Subscriber('/test_topic', String, message_callback)
    
    rospy.sleep(1)  # Wait for subscriber connection

    test_msg = String()
    test_msg.data = "Hello from Behave!"
    pub.publish(test_msg)

    rospy.sleep(2)  # Wait for message to be received

@then('the message should be received')
def step_impl(context):
    """ Check if the message was received. """
    assert received_message == "Hello from Behave!", "Message not received!"
