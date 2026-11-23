"""Capture both BSN-P03 topics on one monotonic observer clock."""
import ctypes
import threading
import time


class Timespec(ctypes.Structure):
    _fields_ = [('seconds', ctypes.c_long), ('nanoseconds', ctypes.c_long)]


_clock_gettime = ctypes.CDLL(None, use_errno=True).clock_gettime
_clock_gettime.argtypes = [ctypes.c_int, ctypes.POINTER(Timespec)]
_clock_gettime.restype = ctypes.c_int


def monotonic_ns():
    stamp = Timespec()
    if _clock_gettime(1, ctypes.byref(stamp)) != 0:  # CLOCK_MONOTONIC on Linux
        raise OSError(ctypes.get_errno(), 'clock_gettime failed')
    return stamp.seconds * 1000000000 + stamp.nanoseconds


def capture_temporal_topics(rospy, sensor_type, target_type, sensor_info, duration):
    lock = threading.Lock()
    stopped = threading.Event()
    sensor = {'risk': [], 'data': [], '%time': []}
    target = {sensor_info['risk_key']: [], sensor_info['data_key']: [], '%time': []}

    def record_sensor(msg):
        stamp = monotonic_ns()
        with lock:
            if not stopped.is_set():
                sensor['risk'].append(msg.risk)
                sensor['data'].append(msg.data)
                sensor['%time'].append(stamp)

    def record_target(msg):
        stamp = monotonic_ns()
        with lock:
            if not stopped.is_set():
                target[sensor_info['risk_key']].append(getattr(msg, sensor_info['risk_key']))
                target[sensor_info['data_key']].append(getattr(msg, sensor_info['data_key']))
                target['%time'].append(stamp)

    subscriptions = []
    try:
        subscriptions.append(rospy.Subscriber(sensor_info['topic'], sensor_type, record_sensor))
        subscriptions.append(rospy.Subscriber('/TargetSystemData', target_type, record_target))
        deadline = monotonic_ns() + int(duration * 1000000000)
        while not rospy.is_shutdown() and monotonic_ns() < deadline:
            time.sleep(0.01)
    finally:
        with lock:
            stopped.set()
        for subscription in subscriptions:
            subscription.unregister()
    assert sensor['%time'], 'No sensor messages captured for temporal observation'
    assert target['%time'], 'No central hub messages captured for temporal observation'
    return {sensor_info['topic']: sensor}, target
