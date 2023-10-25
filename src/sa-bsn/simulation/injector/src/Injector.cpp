#include "Injector.hpp"

Injector::Injector(int  &argc, char **argv, const std::string &name) : ROSComponent(argc, argv, name), cycles(0), duration(), frequency(), amplitude(), noise_factor(), begin(), end(), type() {}
Injector::~Injector() {}

void Injector::setUp() {
    srand(time(NULL));
    log_uncertainty = handle.advertise<archlib::Uncertainty>("log_uncertainty", 10);
    //wait(500000);     
    ros::NodeHandle config;
    
    double freq;
    config.getParam("frequency", freq);
    rosComponentDescriptor.setFreq(freq);

    std::string comps;
    config.getParam("components", comps);
    components = bsn::utils::split(comps, ',');

    for (std::vector<std::string>::iterator component = components.begin(); component != components.end(); ++component){
        uncertainty_pub[*component] = handle.advertise<archlib::Uncertainty>("uncertainty_/"+(*component), 1000);
        config.getParam((*component) + "/type", type[*component]);
        config.getParam((*component) + "/offset", noise_factor[*component]);
        config.getParam((*component) + "/amplitude", amplitude[*component]);
        config.getParam((*component) + "/frequency", frequency[*component]);
        config.getParam((*component) + "/duration", duration[*component]);
        int beg;
        config.getParam((*component) + "/begin", beg);
        begin[*component] = seconds_in_cycles(beg);
        end[*component] = begin[*component] + seconds_in_cycles(duration[*component]);
    }
}

void Injector::tearDown() {}

int64_t Injector::seconds_in_cycles(const double &seconds){
    return seconds*rosComponentDescriptor.getFreq();
}

int64_t Injector::cycles_in_seconds(const double &cycles) {
    return cycles/rosComponentDescriptor.getFreq();
}

double Injector::gen_noise(const std::string &component, double &noise, int &duration, double &amplitude, std::string &type){

    bool is_last_cycle = (cycles == end[component])?true:false;

    if (type=="step" && !is_last_cycle){
        return amplitude;
    } else if (type=="ramp" && !is_last_cycle) {
        return noise + amplitude/seconds_in_cycles(duration);
    } else if (type=="random") {
        return ((double) rand() / (RAND_MAX)) * amplitude;
    } 
    
    return 0.0;
}

void Injector::body() {
    ++cycles;

    for (std::vector<std::string>::iterator component = components.begin(); component != components.end(); ++component){
        if (begin[*component] <= cycles && cycles <= end[*component]) {

            noise_factor[*component] = gen_noise(*component, noise_factor[*component], duration[*component], amplitude[*component], type[*component]);
            inject(*component, "noise_factor=" + std::to_string(noise_factor[*component]));

            //update begin and end tags in last cycle
            if (cycles == end[*component]){
                begin[*component] += seconds_in_cycles(1.0/frequency[*component]);
                end[*component]   += seconds_in_cycles(1.0/frequency[*component]);
            }
        }
    }
}

void Injector::inject(const std::string &component, const std::string &content){
    archlib::Uncertainty msg;

    msg.source = ros::this_node::getName();
    msg.target = "/"+component;
    msg.content = content;

    uncertainty_pub[component].publish(msg);
    log_uncertainty.publish(msg);
    ROS_INFO("Inject [%s] at [%s].", content.c_str(), component.c_str());
}
