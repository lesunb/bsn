# -*- coding: utf-8 -*-
"""Unit tests for the `enactor` node (Controller.cpp), RELIABILITY path (the real system's configuration); it needs its own launch
because `adaptation_parameter` is read once in setUp() and every branch keys off it. r_curr comes from data_access as
success/(success + fail) over its 10.1s window and is not zeroed per query; error = r_ref - r_curr, new_freq = freq + (kp/100)*error."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from enactor_test_support import CYCLE, EnactorHarness


class TestEnactorReliability:
    """Tests for the `enactor` node (Controller) on its reliability path,
    with a real `data_access` node alongside it (see
    test_enactor_reliability.launch)."""

    @classmethod
    def setup_class(cls):
        cls.bsn = EnactorHarness(adaptation_parameter="reliability")
        cls.bsn.start("test_enactor_reliability_node")

    @classmethod
    def teardown_class(cls):
        cls.bsn.stop()

    def setup_method(self):
        self.bsn.reset()

    def test_component_at_its_reliability_reference_is_still_adapted(self):
        """Pins ROS1's stability-margin behavior: it tests `error > margin*r_ref || error < margin*r_ref` (Controller.cpp), true for
        almost any error, so even error = 0 publishes a no-op new_freq = 10; the ROS2 port's `abs(error) > threshold` publishes
        nothing. It also proves the launch is on the reliability path (the same stimulus on the cost path publishes nothing)."""
        component = "/test_reli_reference_component"
        self.bsn.activate(component, 10.0)
        self.bsn.publish_status(component, "success")

        assert self.bsn.wait_for_command(component), (
            "Expected the no-op AdaptationCommand ROS1's stability-margin "
            "check lets through for {}, got: {}".format(
                component, [(m.target, m.action) for m in self.bsn.log_adapt_messages]
            )
        )
        freqs = self.bsn.freqs_for(component)
        assert abs(freqs[0] - 10.0) < 0.01, (
            "Expected freq=10.000000 (unchanged: 10 + (150/100)*0), "
            "got: {}".format(freqs)
        )

    def test_reliability_below_reference_raises_the_frequency(self):
        """One success and one failure give reliability 0.5, so error = +0.5 and freq rises by 0.75 to 10.75. Asserts "some command
        was freq=10.75", not the first, since earlier no-op commands are published with new_freq == freq (10.0)."""
        component = "/test_reli_drop_component"
        self.bsn.activate(component, 10.0)
        self.bsn.publish_status(component, "success")
        self.bsn.publish_status(component, "fail")

        assert self.bsn.wait_for_freq(component, 10.75), (
            "Expected an AdaptationCommand freq=10.750000 for {} "
            "(10 + (150/100)*(1 - 0.5)), got: {}".format(
                component, self.bsn.commands_for(component)
            )
        )

    def test_strategy_message_moves_the_reliability_reference(self):
        """receiveStrategy writes r_ref on this path: with r_ref = 0.5 and only successes (r_curr = 1), error is negative:
        10 + 1.5*(0.5 - 1) = 9.25, i.e. the enactor slows a component that is more reliable than needed."""
        component = "/test_reli_strategy_component"
        self.bsn.activate(component, 10.0)
        self.bsn.set_reference(component, 0.5)
        self.bsn.publish_status(component, "success")

        assert self.bsn.wait_for_freq(component, 9.25), (
            "Expected an AdaptationCommand freq=9.250000 for {} after a "
            "Strategy lowered its reliability reference to 0.5 "
            "(10 + (150/100)*(0.5 - 1)), got: {}".format(
                component, self.bsn.commands_for(component)
            )
        )

    def test_repeated_failures_raise_an_exception(self):
        """Out of tolerance, exception_buffer increments per cycle and past 4 an Exception(component=1) is published. One "fail"
        Status is enough (reliability stays 0 until it ages out of the 10.1s window), unlike the cost path's per-query zeroing."""
        component = "/test_reli_exception_component"
        self.bsn.activate(component, 10.0)
        self.bsn.publish_status(component, "fail")

        assert self.bsn.wait_for_exception(component + "=1"), (
            "Expected an Exception '{}=1' on the exception topic after "
            "repeated out-of-tolerance cycles, got: {}".format(
                component, [m.content for m in self.bsn.exception_messages]
            )
        )

    def test_deactivated_component_is_no_longer_adapted(self):
        """receiveEvent's "deactivate" branch erases the component; as on the cost path ROS1 has no unregistered guard, so freq/kp
        reset to 0.0 and new_freq = 0 fails the >= 0.1 bounds check: the commands simply stop."""
        component = "/test_reli_deactivate_component"
        self.bsn.activate(component, 10.0)
        self.bsn.publish_status(component, "success")
        assert self.bsn.wait_for_command(component), (
            "Precondition failed: the component was never adapted while "
            "active, so this test cannot tell deactivation apart from a "
            "silent pipeline"
        )

        self.bsn.deactivate(component)
        self.bsn.reset()
        time.sleep(10 * CYCLE)

        assert not self.bsn.commands_for(component), (
            "A deactivated component must not be adapted any more, got: "
            "{}".format(self.bsn.commands_for(component))
        )
