/*
#include <gtest/gtest.h>
#include <stdint.h>

#include "libbsn/range/Range.hpp"
#include "libbsn/generator/Markov.hpp"
#include "libbsn/filters/MovingAverage.hpp"
#include "libbsn/configuration/SensorConfiguration.hpp"

using namespace std;
using namespace bsn::range;
using namespace bsn::filters;
using namespace bsn::configuration;
using namespace bsn::generator;

class IntegrationTest : public testing::Test
{
protected:
    MovingAverage avg1;
    MovingAverage avg2;
    MovingAverage avg4;

    Markov mar1;
    Markov mar2;
    Markov mar4;

    Range l;
    Range m1;
    Range m2;
    Range h1;
    Range h2;

    array<Range, 2> a1;
    array<Range, 2> a2;

    SensorConfiguration s;
    array<float, 25> transitions;
    array<Range, 5> states;

    IntegrationTest() : avg1(), avg2(), avg4(), mar1(), mar2(), mar4(),
                        l(), m1(), m2(), h1(), h2(), a1(),
                        a2(), s(), transitions(), states() {}

    virtual void SetUp()
    {
        transitions = {{0, 100, 0, 0, 0,
                        0, 0, 100, 0, 0,
                        0, 0, 0, 100, 0,
                        0, 0, 0, 0, 100,
                        100, 0, 0, 0, 0}};

        states = {{Range(30.0, 33.0), Range(33.1, 36.4), Range(36.5, 37.5), Range(37.6, 39.0), Range(39.1, 42.0)}};

        h1.setLowerBound(30.0);
        h1.setUpperBound(33.0);

        m1.setLowerBound(33.1);
        m1.setUpperBound(36.4);

        l.setLowerBound(36.5);
        l.setUpperBound(37.5);

        m2.setLowerBound(37.6);
        m2.setUpperBound(39.0);

        h2.setLowerBound(39.1);
        h2.setUpperBound(42.0);

        a1 = {{m1, m2}};
        a2 = {{h1, h2}};

        avg1.setRange(1);
        avg2.setRange(2);
        avg4.setRange(4);

        mar1.transitions = transitions;
        mar1.states = states;
        mar1.currentState = 1;

        mar2.transitions = transitions;
        mar2.states = states;
        mar2.currentState = 2;

        mar4.transitions = transitions;
        mar4.states = states;
        mar4.currentState = 4;

        s.setId(1);
        s.setLowRisk(l);
        s.setMediumRisk(a1);
        s.setHighRisk(a2);
        s.setLowPercentage(Range(0, 0.2));
        s.setMidPercentage(Range(0.21, 0.65));
        s.setHighPercentage(Range(0.66, 1.0));
    }
};

TEST_F(IntegrationTest, IntegrationLow)
{
    ASSERT_EQ(mar2.currentState, 2);

    avg2.insert(mar2.calculate_state(), "thermometer");
    avg2.insert(mar2.calculate_state(), "thermometer");
    double data = avg2.getValue("thermometer");

    ASSERT_LE(data, 37.5);
    ASSERT_LE(36.5, data);

    ASSERT_LE(s.evaluateNumber(data), 0.2);
    ASSERT_LE(0.0, s.evaluateNumber(data));
}

TEST_F(IntegrationTest, IntegrationHigh)
{
    ASSERT_EQ(mar4.currentState, 4);
    avg4.insert(mar4.calculate_state(), "thermometer");
    avg4.insert(mar4.calculate_state(), "thermometer");
    double data = avg4.getValue("thermometer");

    ASSERT_LE(data, 42);
    ASSERT_LE(39.1, data);

    ASSERT_LE(s.evaluateNumber(data), 1.0);
    ASSERT_LE(0.66, s.evaluateNumber(data));
}

TEST_F(IntegrationTest, IntegrationMedium)
{
    ASSERT_EQ(mar1.currentState, 1);
    avg1.insert(mar1.calculate_state(), "thermometer");
    avg1.insert(mar1.calculate_state(), "thermometer");
    double data = avg1.getValue("thermometer");

    ASSERT_LE(data, 36.4);
    ASSERT_LE(33.1, data);

    ASSERT_LE(s.evaluateNumber(data), 0.65);
    ASSERT_LE(0.21, s.evaluateNumber(data));
}
*/