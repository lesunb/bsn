"""Common observation criterion, compatible with Python 2.7 and Python 3.

This checks observed activity, validity and variation, not causality from a
particular reading. Variation is retained from the legacy characterization;
it is not a universal requirement for a patient with constant inputs.
"""
import math


def assert_health_observation(readings, statuses, expect_output=True):
    assert readings, "No thermometer reading observed; the stimulus is unverified"
    try:
        readings = [float(value) for value in readings]
        states = [float(value) for value in statuses]
    except (TypeError, ValueError, OverflowError):
        raise AssertionError("Malformed numeric observation")
    assert all(not math.isnan(v) and not math.isinf(v) for v in readings), "Invalid reading"
    if not expect_output:
        assert not states, "Health status emitted while the hub was unavailable"
        return
    assert states, "No patient health status observed"
    assert all(0.0 <= value <= 100.0 for value in states), "Health status outside [0, 100]"
    assert len(set(states)) > 1, "No numeric variation in observed health status"
