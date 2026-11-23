#include <gtest/gtest.h>
#include <ros/ros.h>
#include <std_msgs/String.h>
#include <messages/SensorData.h>
#include <messages/TargetSystemData.h>
#include <services/PatientData.h>

ros::NodeHandle *nh;
bool emergency_detected = false;
ros::Time start_time;

// Callback function for emergency detection
void targetSystemCallback(const messages::TargetSystemData::ConstPtr &msg)
{
    if (msg->patient_status > 65.0) // High-risk threshold
    {
        emergency_detected = true;
    }
}

// Mock service callback to simulate patient data collection
bool mockPatientDataService(services::PatientData::Request &req, services::PatientData::Response &res)
{
    if (req.vitalSign == "temperature")
    {
        res.data = 41.0; // Simulated high-risk temperature
        return true;
    }
    return false;
}

// Test case: Full data flow - G3T1_3 collects patient data, G4T1 detects emergency
TEST(SensorExecutionTest, EmergencyDetectionWithFullDataFlow)
{
    // Set up subscribers for emergency detection
    ros::Subscriber sub = nh->subscribe("TargetSystemData", 10, targetSystemCallback);

    // Sleep to ensure nodes have stabilized
    ros::Duration(1.0).sleep(); // Wait 1 second for stability

    // Create a service client for getPatientData
    ros::ServiceClient client = nh->serviceClient<services::PatientData>("getPatientData");
    services::PatientData srv;
    srv.request.vitalSign = "temperature";

    // Call the service before checking emergency detection
    if (client.call(srv))
    {
        ROS_INFO("Service response: %.2f", srv.response.data);
    }
    else
    {
        FAIL() << "Failed to call getPatientData service!";
    }

    // Ensure the service is available before attempting to call it
    bool service_available = ros::service::waitForService("getPatientData", ros::Duration(5.0));
    ASSERT_TRUE(service_available) << "The service getPatientData is not available.";

    // Simulate the data flow by triggering the callback and checking emergency detection
    ros::Time timeout = ros::Time::now() + ros::Duration(1.0);
    while (ros::Time::now() < timeout)
    {
        ros::spinOnce();
        if (emergency_detected)
            break;
    }

    // Verify that emergency was detected in time
    ASSERT_TRUE(emergency_detected) << "G4T1 did not detect emergency in time!";
}

int main(int argc, char **argv)
{
    ros::init(argc, argv, "sensor_execution_test");
    ros::NodeHandle nh_local;
    nh = &nh_local;
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
