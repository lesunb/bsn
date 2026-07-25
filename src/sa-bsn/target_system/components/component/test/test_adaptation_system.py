import pytest
import rospy
import threading
from archlib.msg import AdaptationCommand, Status, Uncertainty, Persist
import time

class SharedAdaptationTests:
    """Shared test methods for adaptation system"""
    
    context = {}
    commands = []
    lock = threading.Lock()
    message_lock = threading.Lock()
    received_messages=[]
    persist_received = []
    persist_lock = threading.Lock()
    
    def __init__(cls):
        topic = "log_adapt"

        subscriber = rospy.Subscriber(topic, AdaptationCommand, cls._callback)
        cls.context["adaptation_commands"] = cls.commands
        cls.context["adaptation_commands_lock"] = cls.lock
        cls.context["adaptation_commands_subscriber"] = subscriber

        cls.subPersist = rospy.Subscriber("persist", Persist, cls._callback_persist_message)

    def _callback(cls, msg):
        """Callback for receiving messages from the sensor"""
        with cls.lock:
            cls.commands.append(msg)
    
    def _callback_persist_message(cls, msg):
        if msg.type == "AdaptationCommand":
            with cls.persist_lock:

                cls.persist_received.append(msg)
    
    def __del__(self):
        self.context["adaptation_commands_subscriber"].unregister()
        self.subPersist.unregister()

    @classmethod
    def get_received_commands(cls):
        with cls.context["adaptation_commands_lock"]:
            return cls.context["adaptation_commands"]
            
            