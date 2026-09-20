# -*- coding: utf-8 -*-
"""Unit tests for the `enactor` node (Controller.cpp), COST path; equivalent to bsn_ros2/adaptation/test/test_enactor.py.
Runs against a real `data_access` (test_enactor.launch: adaptation_parameter="cost", kp=150, frequency=5); a freq is published
only if 0.5 <= new_freq <= 25 (/g4t1: new_freq > 0). Reliability twin: test_enactor_reliability.py; readiness: enactor_test_support.py."""
import os
import sys
import time

import rospy

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from enactor_test_support import CYCLE, EnactorHarness


class TestEnactor:
    """Tests for the `enactor` node (Controller) on its cost path, with a
    real `data_access` node alongside it (see test_enactor.launch)."""

    @classmethod
    def setup_class(cls):
        cls.bsn = EnactorHarness(adaptation_parameter="cost")
        cls.bsn.start("test_enactor_node")

    @classmethod
    def teardown_class(cls):
        cls.bsn.stop()

    def setup_method(self):
        self.bsn.reset()

    def test_node_advertises_its_topics(self):
        """Basic health check: setUp() ran and advertised log_adapt/exception
        (Controller::setUp advertises both unconditionally)."""
        published_topics = [name for name, _ in rospy.get_published_topics()]
        assert "/log_adapt" in published_topics
        assert "/exception" in published_topics

    def test_cost_adaptation_lowers_frequency_when_cost_exceeds_reference(self):
        """End-to-end: activate at freq=10 with a Status and an EnergyStatus of 2.0 (cost 2.0). c_ref defaults to 0, so
        error = -2.0 and freq drops by (150/100)*2.0 = 3.0 to 7.0, published on log_adapt."""
        component = "/test_cost_component"
        self.bsn.activate(component, 10.0)
        self.bsn.publish_status(component)

        self.bsn.energy_until_command(component, 2.0)

        assert self.bsn.wait_for_command(component), (
            "Expected an AdaptationCommand for {} on log_adapt, got: {}".format(
                component, [(m.target, m.action) for m in self.bsn.log_adapt_messages]
            )
        )
        freqs = self.bsn.freqs_for(component)
        assert abs(freqs[0] - 7.0) < 0.01, (
            "Expected the first adaptation to be freq=7.000000 "
            "(10 + (150/100)*(0 - 2.0)), got: {}".format(freqs)
        )

    def test_strategy_message_moves_the_cost_reference(self):
        """receiveStrategy moves c_ref away from 0: with c_ref = 5.0 and no cost (c_curr = 0), error = +5.0 and freq rises
        10 + 1.5*5.0 = 17.5. Asserting nothing was published before the Strategy pins the input that reaches the else branch."""
        component = "/test_strategy_component"
        self.bsn.activate(component, 10.0)
        self.bsn.publish_status(component)
        time.sleep(5 * CYCLE)

        assert not self.bsn.commands_for(component), (
            "A component whose cost is 0 and whose c_ref is still 0 is in "
            "tolerance and must not be adapted, got: {}".format(
                self.bsn.commands_for(component)
            )
        )

        self.bsn.set_reference(component, 5.0)

        assert self.bsn.wait_for_command(component), (
            "Expected an AdaptationCommand for {} after a Strategy set its "
            "cost reference to 5.0, got nothing".format(component)
        )
        freqs = self.bsn.freqs_for(component)
        assert abs(freqs[0] - 17.5) < 0.01, (
            "Expected the first adaptation to be freq=17.500000 "
            "(10 + (150/100)*(5.0 - 0)), got: {}".format(freqs)
        )

    def test_component_in_tolerance_reports_a_negative_exception(self):
        """Mirror of the exception test: within the stability margin, exception_buffer decrements every cycle and past -4
        an Exception(component=-1) is published, without any AdaptationCommand (activated + Status only: c_ref = c_curr = 0)."""
        component = "/test_in_tolerance_component"
        self.bsn.activate(component, 10.0)
        self.bsn.publish_status(component)

        assert self.bsn.wait_for_exception(component + "=-1"), (
            "Expected an Exception '{}=-1' after repeated in-tolerance "
            "cycles, got: {}".format(
                component, [m.content for m in self.bsn.exception_messages]
            )
        )
        assert not self.bsn.commands_for(component), (
            "A component in tolerance must not be adapted, got: {}".format(
                self.bsn.commands_for(component)
            )
        )

    def test_repeated_out_of_tolerance_cycles_raise_an_exception(self):
        """Out of the stability margin, exception_buffer increments every cycle and past 4 an Exception(component=1) is
        published. flood_energy republishes faster than the enactor's cycle, since calculateComponentCost zeroes the cost per query."""
        component = "/test_exception_component"
        self.bsn.activate(component, 10.0)
        self.bsn.publish_status(component)

        found = self.bsn.flood_energy(
            component,
            2.0,
            duration=8.0,
            condition=lambda: component + "=1"
            in [m.content for m in self.bsn.exception_messages],
        )

        assert found, (
            "Expected an Exception '{}=1' on the exception topic after "
            "repeated out-of-tolerance cycles, got: {}".format(
                component, [m.content for m in self.bsn.exception_messages]
            )
        )

    def test_deactivated_component_is_no_longer_adapted(self):
        """receiveEvent's "deactivate" branch erases the component from the maps; ROS1 has no unregistered-component guard
        (ROS2 returns early), so freq/kp are re-created as 0.0 and new_freq = 0 fails the >= 0.5 bounds check: "no more commands"."""
        component = "/test_deactivate_component"
        self.bsn.activate(component, 10.0)
        self.bsn.publish_status(component)
        self.bsn.energy_until_command(component, 2.0)
        assert self.bsn.wait_for_command(component), (
            "Precondition failed: the component was never adapted while "
            "active, so this test cannot tell deactivation apart from a "
            "silent pipeline"
        )

        self.bsn.deactivate(component)
        self.bsn.reset()

        deadline = time.time() + 3.0
        while time.time() < deadline:
            self.bsn.publish_status(component)
            self.bsn.publish_energy(component, 2.0)
            time.sleep(0.5)

        assert not self.bsn.commands_for(component), (
            "A deactivated component must not be adapted any more, got: "
            "{}".format(self.bsn.commands_for(component))
        )

    def test_central_hub_is_adapted_below_the_sensor_frequency_bound(self):
        """Controller treats "/g4t1" specially: it only needs new_freq > 0 (others 0.5 <= new_freq <= 25). From freq = 1.0 with
        cost 0.4, new_freq = 0.4: a sensor is untouched but /g4t1 is adapted, so a published freq=0.400000 came from that branch."""
        component = "/g4t1"
        self.bsn.activate(component, 1.0)
        self.bsn.publish_status(component)

        self.bsn.energy_until_command(component, 0.4)

        assert self.bsn.wait_for_command(component), (
            "Expected an AdaptationCommand for {} on log_adapt, got: {}".format(
                component, [(m.target, m.action) for m in self.bsn.log_adapt_messages]
            )
        )
        freqs = self.bsn.freqs_for(component)
        assert abs(freqs[0] - 0.4) < 0.01, (
            "Expected the first adaptation to be freq=0.400000 "
            "(1.0 + (150/100)*(0 - 0.4)), below the 0.5 lower bound that "
            "applies to every other component, got: {}".format(freqs)
        )

        self.bsn.deactivate(component)
