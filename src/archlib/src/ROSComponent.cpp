#include "archlib/ROSComponent.hpp"

#include <signal.h>

namespace {
    /**
     * Does exactly what roscpp's own default SIGINT handler does: flips
     * ros::ok() so every `while(ros::ok())` loop (run()'s, and the inner one
     * Enactor::body() has, and ros::spin() inside Logger/ParamAdapter) ends,
     * tearDown() runs and main() returns normally.
     *
     * Without it a node built on ROSComponent is simply killed by the signal,
     * because ros::init() below asks for NoSigintHandler and nothing ever
     * installed a replacement - the target_system side has had its own handler
     * for a long time (see target_system/Component.cpp's sigIntHandler, which
     * still overrides this one, since it is installed later, in setUp()), the
     * management side had none.
     *
     * Two consequences, both fixed by exiting normally instead:
     *  - the node never got a chance to run tearDown() on shutdown;
     *  - under a coverage build nothing was ever written: llvm's profile is
     *    flushed at exit, so every node here (enactor, data_access, logger,
     *    param_adapter, engines, patient) reported 0% in coverage.sh's report
     *    even though its rostests ran and passed.
     *
     * SIGTERM is handled too because that is what roslaunch escalates to when
     * a node does not exit quickly enough after the SIGINT.
     */
    void shutdownOnSignal(int /*signal*/) {
        ros::requestShutdown();
    }
}

namespace arch {
	ROSComponent::ROSComponent(int &argc, char **argv, const std::string &name) : rosComponentDescriptor() {
        ros::init(argc, argv, name, ros::init_options::NoSigintHandler); //Configure node name and sets commnd line arguments
        signal(SIGINT, shutdownOnSignal);
        signal(SIGTERM, shutdownOnSignal);
        std::string node_name = getRosNodeName(ros::this_node::getName(), ros::this_node::getNamespace());
        rosComponentDescriptor.setName(node_name);
    }
	ROSComponent::~ROSComponent() {}

    int32_t ROSComponent::run() {
        setUp();

        while(ros::ok()) {
            ros::Rate loop_rate(rosComponentDescriptor.getFreq());
            ros::spinOnce();
            body();
            loop_rate.sleep();
        }

        tearDown();
        return 0;
    }

    std::string ROSComponent::getRosNodeName(const std::string& node_name, const std::string& node_namespace) {
        std::string ros_node_name = node_name;

        ROS_DEBUG("%s", ros_node_name.c_str());
        size_t pos = ros_node_name.find(node_namespace + '/');

        if (pos == std::string::npos)
        {
            pos = ros_node_name.find(node_namespace);
            ros_node_name.replace(pos, node_namespace.length(), "/");
            return ros_node_name;
        }

        // ROS_INFO("namespace %s", node_namespace.c_str());
        ros_node_name.replace(pos, node_namespace.length() + 1, "/");

        return ros_node_name;
    }
}
