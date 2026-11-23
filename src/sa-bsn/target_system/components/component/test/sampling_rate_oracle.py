"""Observation criterion shared by ROS 1 and ROS 2 adaptation tests."""
import math
import threading

WINDOW_S = 6.0
MIN_MESSAGES = 4
MAX_WINDOW_S = 60.0
OBSERVATION_WINDOWS = 3


def summarize_rate(stamps):
    assert len(stamps) >= MIN_MESSAGES, 'Insufficient sensor messages: {}'.format(len(stamps))
    intervals = [b - a for a, b in zip(stamps, stamps[1:])]
    assert all(x > 0 and not math.isinf(x) and not math.isnan(x) for x in intervals), 'Invalid observation intervals'
    ordered = sorted(intervals)
    middle = len(ordered) // 2
    median = ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2.0
    return {'hz': 1.0 / median, 'messages': len(stamps),
            'span_s': stamps[-1] - stamps[0], 'timestamps': stamps}


def assert_rate_changed(before, after, direction):
    assert direction in ('increase', 'decrease')
    first = before['windows']
    second = after['windows']
    assert len(first) == len(second) == OBSERVATION_WINDOWS, 'Three windows required per phase'
    for metric in ('hz', 'count_hz'):
        left = [window[metric] for window in first]
        right = [window[metric] for window in second]
        baseline = sorted(left)[1]
        observed = sorted(right)[1]
        changed = observed > baseline if direction == 'increase' else observed < baseline
        assert changed, 'Median sensor rate did not {}: {} before={}, after={}'.format(direction, metric, left, right)


def observe_rate(subscribe, poll, clock):
    windows = [_observe_window(subscribe, poll, clock) for _ in range(OBSERVATION_WINDOWS)]
    result = {'windows': windows, 'hz': sorted(w['hz'] for w in windows)[1]}
    print('sensor_rate_phase: {}'.format(result))
    return result


def _observe_window(subscribe, poll, clock):
    stamps = []
    lock = threading.Lock()

    def receive(_message):
        with lock:
            stamps.append(clock())

    unsubscribe = subscribe(receive)
    try:
        deadline = clock() + 10.0
        while clock() < deadline:
            poll()
            with lock:
                if stamps:
                    break
        with lock:
            assert stamps, 'Sensor did not publish during discovery'
            stamps[:] = []
        start = clock()
        deadline = start + MAX_WINDOW_S
        while clock() < deadline:
            poll()
            with lock:
                enough = len(stamps) >= MIN_MESSAGES
            if clock() - start >= WINDOW_S and enough:
                break
        with lock:
            result = summarize_rate(list(stamps))
            result['count_hz'] = len(stamps) / (clock() - start)
        print('sensor_rate_observation: {}'.format(result))
        return result
    finally:
        unsubscribe()
