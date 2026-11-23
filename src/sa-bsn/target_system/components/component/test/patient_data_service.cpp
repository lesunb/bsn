#include <ros/ros.h>
#include <services/PatientData.h> // Replace with the correct header if necessary
#include <random>                 // For generating random temperature values

// Random number generators
std::random_device rd;
std::mt19937 gen(rd());
std::uniform_real_distribution<double> normal_dist(36.5, 37.5); // Normal range
std::uniform_real_distribution<double> high_dist(39.0, 41.0);   // High-risk range
std::bernoulli_distribution state_change(0.6);                  // 60% chance of switching states

// Global state to track normal vs. high-risk
bool is_high_risk = false;

// Function to generate temperature based on current state
double generateTemperature()
{
    // Occasionally switch between normal and high-risk states
    if (state_change(gen))
    {
        is_high_risk = !is_high_risk;
        ROS_INFO("Patient state changed: Now %s", is_high_risk ? "HIGH RISK" : "NORMAL");
    }

    // Generate temperature based on the current state
    return is_high_risk ? high_dist(gen) : normal_dist(gen);
}

// Callback function for the 'getPatientData' service
bool mockPatientDataService(services::PatientData::Request &req, services::PatientData::Response &res)
{
    if (req.vitalSign == "temperature")
    {
        res.data = generateTemperature(); // Generate dynamic temperature
        ROS_INFO("Returning simulated temperature: %.2f", res.data);
        return true;
    }
    return false; // If the vital sign is not recognized
}

int main(int argc, char **argv)
{
    ros::init(argc, argv, "patient_data_service");
    ros::NodeHandle nh;

    // Advertise the service
    ros::ServiceServer service = nh.advertiseService("getPatientData", mockPatientDataService);
    ROS_INFO("Patient data service ready to provide dynamic data...");

    ros::spin(); // Keep the node running
    return 0;
}
