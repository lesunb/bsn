# -*- coding: utf-8 -*-
"""Unit tests for the `data_access` node (DataAccess.cpp), driven through its real ROS interface (persist topic +
DataAccessRequest service); equivalent to bsn_ros2/adaptation/test/test_data_access.py."""
import time

import rospy
from archlib.msg import Persist
from archlib.srv import DataAccessRequest

CONNECTION_WAIT = 0.5


def wait_for(condition_function, timeout=5.0):
    start_time = time.time()
    while time.time() < start_time + timeout:
        if condition_function():
            return True
        time.sleep(0.05)
    return False


class TestDataAccess:
    """Tests for the `data_access` node."""

    @classmethod
    def setup_class(cls):
        rospy.init_node("test_data_access_node", anonymous=True)
        rospy.wait_for_service("DataAccessRequest", timeout=10.0)
        cls.query = rospy.ServiceProxy("DataAccessRequest", DataAccessRequest)

    def setup_method(self):
        self.persist_pub = rospy.Publisher("persist", Persist, queue_size=10)
        time.sleep(CONNECTION_WAIT)

    def teardown_method(self):
        self.persist_pub.unregister()

    def _publish_status(self, source, content):
        msg = Persist()
        msg.source = source
        msg.target = "system"
        msg.type = "Status"
        msg.content = content
        msg.timestamp = 0
        self.persist_pub.publish(msg)

    def _query(self, name, query):
        return self.query(name=name, query=query).content

    def test_reliability_formula_query_returns_non_empty_formula(self):
        """"/engine:reliability_formula" returns the contents of resource/models/reliability.formula
        (only checks that setUp() actually loaded something, not the exact text)."""
        content = self._query("/engine", "reliability_formula")
        assert content != "", "reliability_formula query returned empty content"

    def test_cost_formula_query_returns_non_empty_formula(self):
        content = self._query("/engine", "cost_formula")
        assert content != "", "cost_formula query returned empty content"

    def test_reliability_is_ratio_of_success_to_total(self):
        """calculateComponentReliability: reliability = success/(success+fail),
        matching engine.reli_engine.py's process_reliability_response format
        (":" then digits after each component name)."""
        component = "/test_reliability_component"

        # 3 successes, 1 failure -> 0.75
        self._publish_status(component, "success")
        self._publish_status(component, "success")
        self._publish_status(component, "success")
        self._publish_status(component, "fail")
        time.sleep(0.2)

        assert wait_for(
            lambda: component + ":0.750000;" in self._query("/engine", "all:reliability:"),
            timeout=3.0,
        ), "Expected component reliability 0.75 not found in query response"

    def test_unknown_requester_gets_empty_response(self):
        """processQuery only answers requests from /engine or /enactor -
        anything else silently gets empty content back (the try/catch(...)
        swallows everything, so this is also a no-crash check)."""
        content = self._query("/some_other_requester", "all:reliability:")
        assert content == ""

    def test_node_survives_target_system_data(self):
        """processTargetSystemData updates internal battery tracking (no query surface), so this only confirms the
        node keeps responding to DataAccessRequest afterwards."""
        from messages.msg import TargetSystemData

        pub = rospy.Publisher(
            "TargetSystemData", TargetSystemData, queue_size=10
        )
        time.sleep(CONNECTION_WAIT)
        try:
            msg = TargetSystemData()
            msg.trm_batt = 42.0
            pub.publish(msg)
            time.sleep(0.2)

            # Still responsive.
            content = self._query("/engine", "reliability_formula")
            assert content != ""
        finally:
            pub.unregister()
