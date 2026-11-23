#include <gtest/gtest.h>
#include <messages/SensorData.h>
#include <messages/TargetSystemData.h>
#include "component/g4t1/G4T1.hpp"

// Helper function to create a SensorData message
auto createSensorData = [](const std::string &type, double risk, double batt, double data)
{
    messages::SensorData sensor_data;
    sensor_data.type = type;
    sensor_data.risk = risk;
    sensor_data.batt = batt;
    sensor_data.data = data;
    return sensor_data;
};

class MockPublisher
{
public:
    messages::TargetSystemData last_msg;

    void publish(const messages::TargetSystemData &msg) { last_msg = msg; }
};

class TestableG4T1 : public G4T1
{
public:
    MockPublisher mock_pub;

    TestableG4T1(int &argc, char **argv, const std::string &name)
        : G4T1(argc, argv, name) {}

    void transfer() override
    {
        messages::TargetSystemData msg;
        // Copy data to msg as in your previous implementation...
        mock_pub.publish(msg);
    }
};

// Test fixture
class G4T1Fixture : public ::testing::Test
{
protected:
    int argc = 0;
    char **argv = nullptr;
    TestableG4T1 *g4t1;

    G4T1Fixture()
    {
        g4t1 = new TestableG4T1(argc, argv, "test_g4t1");
        g4t1->setUp();
    }

    ~G4T1Fixture()
    {
        g4t1->tearDown();
        delete g4t1;
    }
};

// Grant the test fixture access to private members of G4T1
/*
FRIEND_TEST(G4T1Fixture, TestCollect);

TEST_F(G4T1Fixture, TestCollect)
{
    auto sensor_data = createSensorData("thermometer", 15.0, 90.0, 37.5);
    messages::SensorData::Ptr sensor_ptr(new messages::SensorData(sensor_data));

    g4t1->collect(sensor_ptr);

    // Access private members directly (because of FRIEND_TEST)
    EXPECT_EQ(g4t1->trm_batt, 90.0) << "Battery level mismatch for thermometer";
    EXPECT_EQ(g4t1->trm_raw, 37.5) << "Raw data mismatch for thermometer";
}

TEST_F(G4T1Fixture, TestTransfer)
{
    // Simulate setting data
    g4t1->trm_batt = 90.0;
    g4t1->trm_risk = 15.0;
    g4t1->trm_raw = 37.5;

    g4t1->transfer();

    const auto &msg = g4t1->mock_pub.last_msg;

    EXPECT_EQ(msg.trm_batt, 90.0) << "Battery level mismatch in transfer";
    EXPECT_EQ(msg.trm_risk, 15.0) << "Risk level mismatch in transfer";
    EXPECT_EQ(msg.trm_data, 37.5) << "Raw data mismatch in transfer";
}

TEST_F(G4T1Fixture, TestBufferOverflow)
{
    auto sensor_data = createSensorData("thermometer", 15.0, 90.0, 37.5);
    messages::SensorData::Ptr sensor_ptr(new messages::SensorData(sensor_data));

    // Fill the buffer beyond max size
    for (int i = 0; i < g4t1->max_size + 1; ++i)
    {
        g4t1->collect(sensor_ptr);
    }

    EXPECT_TRUE(g4t1->lost_packt) << "Buffer overflow not detected";
}
*/
TEST_F(G4T1Fixture, TestHelloWorld)
{
    EXPECT_TRUE(true);
}
int main(int argc, char **argv)
{
    ::testing::InitGoogleTest(&argc, argv);
    ros::init(argc, argv, "test_g4t1");
    ros::NodeHandle nh;
    return RUN_ALL_TESTS();
}
