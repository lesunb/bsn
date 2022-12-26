#include "controller/Controller.hpp"

#include <iostream>

Controller::Controller(int &argc, char **argv, std::string name) : Enactor(argc, argv, name) {}

Controller::~Controller() {}

void Controller::setUp() {
    ros::NodeHandle nh;

    adapt = nh.advertise<archlib::AdaptationCommand>("log_adapt", 10);
    ros::Subscriber voltage_status_sub = nh.subscribe("log_voltage_status", 1000, &Controller::receiveVoltageStatus, this);
    double current_voltage;

    except = nh.advertise<archlib::Exception>("exception", 10);

    double freq;
	nh.getParam("frequency", freq);
    nh.getParam("kp", KP);
    nh.getParam("adaptation_parameter", adaptation_parameter);
	rosComponentDescriptor.setFreq(freq);

    receiveAdaptationParameter();
}

void Controller::receiveEvent(const archlib::Event::ConstPtr& msg) {
    if (msg->content=="activate") {
        invocations[msg->source] = {};
        if(adaptation_parameter == "reliability") {
            r_curr[msg->source] = 1;
            r_ref[msg->source] = 1;
        } else {
            c_curr[msg->source] = 0;
            c_ref[msg->source] = 0;
        }
        //kp[msg->source] = 200;
        kp[msg->source] = KP;
        replicate_task[msg->source] = 1;
        //freq[msg->source] = 20;
        freq[msg->source] = msg->freq;
        exception_buffer[msg->source] = 0;

    } else if (msg->content=="deactivate") {
        invocations.erase(msg->source);
        if(adaptation_parameter == "reliability") {
            r_curr.erase(msg->source);
            r_ref.erase(msg->source);
        } else {
            c_curr.erase(msg->source);
            c_ref.erase(msg->source);
        }
        kp.erase(msg->source);
        replicate_task.erase(msg->source);
        freq.erase(msg->source);
        exception_buffer.erase(msg->source);
    }
}

void Controller::apply_reli_strategy(const std::string &component) {
    std::cout << "r_ref[" << component << "] = "<< r_ref[component] <<std::endl;
    std::cout << "r_curr[" << component << "] = "<< r_curr[component] <<std::endl;
    std::cout << "kp[" << component << "] = "<< kp[component] <<std::endl;

    double error = r_ref[component] - r_curr[component]; //error = Rref - Rcurr

    if(error > stability_margin*r_ref[component] || error < -stability_margin*r_ref[component]) {

        exception_buffer[component] = (exception_buffer[component] < 0) ? 0 : exception_buffer[component] + 1;

        if(component == "/g4t1"){
            // g4t1 reliability is inversely proportional to the sensors frequency
            /*
                Nota:

                -> Quando o componente é a Centralhub, adaptamos as frequências dos sensores. Porquê?
            */
            /*for (std::map<std::string, double>::iterator it = freq.begin(); it != freq.end(); ++it){
                if(it->first != "/g4t1"){
                    freq[it->first] += (error>0) ? ((-kp[it->first]/100) * error) : ((kp[it->first]/100) * error); 
                    if(freq[(it->first)] <= 0) break;
                    archlib::AdaptationCommand msg;
                    msg.source = ros::this_node::getName();
                    msg.target = it->first;
                    msg.action = "freq=" + std::to_string(freq[(it->first)]);
                    adapt.publish(msg);
                }
            }*/
            //double new_freq = freq[component] + ((error>0) ? ((-kp[component]/100) * error) : ((kp[component]/100) * error)); 
            double new_freq = freq[component] + ((kp[component]/100) * error);
            if(new_freq > 0) {
                freq[component] = new_freq;
                archlib::AdaptationCommand msg;
                msg.source = ros::this_node::getName();
                msg.target = component;
                msg.action = "freq=" + std::to_string(freq[component]);
                adapt.publish(msg);
                /*std::cout << "################################################" << std::endl;
                std::cout << "Adapting Centralhub" << std::endl;
                std::cout << "Action: " << msg.action << std::endl;
                std::cout << "################################################" << std::endl;*/
            } /*else {
                std::cout << "################################################" << std::endl;
                std::cout << "COULD NOT ADAPT CENTRALHUB"<< std::endl;
                std::cout << "Calculated frequency: " << new_freq << std::endl;
                std::cout << "################################################" << std::endl;
            }*/
        } else {
            if(adaptation_parameter == "replicate_collect") {
                replicate_task[component] += (error > 0) ? ceil(kp[component] * error) : floor(kp[component] * error);
                if (replicate_task[component] < 1) replicate_task[component] = 1;
                archlib::AdaptationCommand msg;
                msg.source = ros::this_node::getName();
                msg.target = component;
                msg.action = "replicate_collect=" + std::to_string(replicate_task[(component)]);
                adapt.publish(msg);
            } else {
                //freq[component] += (error>0) ? ((-kp[component]/100) * error) : ((kp[component]/100) * error); 
                //double new_freq = freq[component] + ((error>0) ? ((-kp[component]/100) * error) : ((kp[component]/100) * error));
                double new_freq = freq[component] + ((kp[component]/100) * error);
                if(new_freq >= 0.1 && new_freq <= 40) {
                    freq[component] = new_freq;
                    archlib::AdaptationCommand msg;
                    msg.source = ros::this_node::getName();
                    msg.target = component;
                    msg.action = "freq=" + std::to_string(freq[component]);
                    adapt.publish(msg);
                }
            }
        }
    } else {
        exception_buffer[component] = (exception_buffer[component] > 0) ? 0 : exception_buffer[component] - 1;
    }

    if(exception_buffer[component]>4){
        archlib::Exception msg;
        msg.source = ros::this_node::getName();
        msg.target = "/engine";
        msg.content = component+"=1";
        except.publish(msg);
        exception_buffer[component] = 0;
    } else if (exception_buffer[component]<-4) {
        archlib::Exception msg;
        msg.source = ros::this_node::getName();
        msg.target = "/engine";
        msg.content = component+"=-1";
        except.publish(msg);
        exception_buffer[component] = 0;
    }
    
    invocations[component].clear();
}

void Controller::receiveVoltageStatus(const archlib::VoltageStatus::ConstPtr& msg) {
    ROS_INFO("I heard Controller: [%s: %s]", msg->source.c_str(), to_string(msg->content).c_str());

    // persistMsg.source = msg->source;
    // persistMsg.target = msg->target;
    // persistMsg.type = "VoltageStatus";
    // persistMsg.timestamp = this->now()-time_ref;
    current_voltage = stod(msg->content);
}


void Controller::apply_cost_strategy(const std::string &component) {
    std::cout << "c_ref[" << component << "] = "<< c_ref[component] <<std::endl;
    std::cout << "c_curr[" << component << "] = "<< c_curr[component] <<std::endl;
    std::cout << "kp[" << component << "] = "<< kp[component] <<std::endl;

    // if (c_ref[component] == 0 || c_curr[component] == 0){
    //     return;
    // }
    double desired_voltage = 1.0;
    int kp_volt = 150;
    double error = c_ref[component] - c_curr[component]; //error = Cref - Ccurr
    double voltage_error = desired_voltage - current_voltage;

    if(error > stability_margin*c_ref[component] || error < -stability_margin*c_ref[component]) {

        exception_buffer[component] = (exception_buffer[component] < 0) ? 0 : exception_buffer[component] + 1;

        if(component == "/g4t1"){
            // g4t1 reliability is inversely proportional to the sensors frequency
            /*
                Nota:

                -> Quando o componente é a Centralhub, adaptamos as frequências dos sensores. Porquê?
            */
            /*for (std::map<std::string, double>::iterator it = freq.begin(); it != freq.end(); ++it){
                if(it->first != "/g4t1"){
                    freq[it->first] += (error>0) ? ((-kp[it->first]/100) * error) : ((kp[it->first]/100) * error); 
                    if(freq[(it->first)] <= 0) break;
                    archlib::AdaptationCommand msg;
                    msg.source = ros::this_node::getName();
                    msg.target = it->first;
                    msg.action = "freq=" + std::to_string(freq[(it->first)]);
                    adapt.publish(msg);
                }
            }*/
            //double new_freq = freq[component] + ((error>0) ? ((-kp[component]/100) * error) : ((kp[component]/100) * error)); 
            double new_freq = freq[component] + ((kp[component]/100) * error);
            if(new_freq > 0) {
                freq[component] = new_freq;
                archlib::AdaptationCommand msg;
                msg.source = ros::this_node::getName();
                msg.target = component;
                msg.action = "freq=" + std::to_string(freq[component]);
                adapt.publish(msg);
                //c_curr[component] = 0;
                /*std::cout << "################################################" << std::endl;
                std::cout << "Adapting Centralhub" << std::endl;
                std::cout << "Action: " << msg.action << std::endl;
                std::cout << "################################################" << std::endl;*/
            } /*else {
                std::cout << "################################################" << std::endl;
                std::cout << "COULD NOT ADAPT CENTRALHUB"<< std::endl;
                std::cout << "Calculated frequency: " << new_freq << std::endl;
                std::cout << "################################################" << std::endl;
            }*/
        } else {
            if(adaptation_parameter == "replicate_collect") {
                replicate_task[component] += (error > 0) ? ceil(kp[component] * error) : floor(kp[component] * error);
                if (replicate_task[component] < 1) replicate_task[component] = 1;
                archlib::AdaptationCommand msg;
                msg.source = ros::this_node::getName();
                msg.target = component;
                msg.action = "replicate_collect=" + std::to_string(replicate_task[(component)]);
                adapt.publish(msg);
            } else {
                //freq[component] += (error>0) ? ((-kp[component]/100) * error) : ((kp[component]/100) * error); 
                //double new_freq = freq[component] + ((error>0) ? ((-kp[component]/100) * error) : ((kp[component]/100) * error));
                double new_freq = freq[component] + ((kp[component]/100) * error);
                double new_volt = current_voltage + ((kp_volt/100) * voltage_error);
                ROS_INFO("NEW FREQUENCY [%s]", std::to_string(new_freq).c_str());
                if(new_volt >= 1.0 && new_volt <= 6.0) {
                    archlib::AdaptationCommand voltageMsg;
                    voltageMsg.source = ros::this_node::getName();
                    voltageMsg.target = component;
                    voltageMsg.action = "volt=" + std::to_string(new_volt);
                }
                if(new_freq >= 0.1 && new_freq <= 25) {
                    freq[component] = new_freq;
                    archlib::AdaptationCommand msg;
                    msg.source = ros::this_node::getName();
                    msg.target = component;
                    msg.action = "freq=" + std::to_string(freq[component]);
                    adapt.publish(msg);
                }
            }
        }
    } else {
        exception_buffer[component] = (exception_buffer[component] > 0) ? 0 : exception_buffer[component] - 1;
    }

    if(exception_buffer[component]>4){
        archlib::Exception msg;
        msg.source = ros::this_node::getName();
        msg.target = "/engine";
        msg.content = component+"=1";
        except.publish(msg);
        exception_buffer[component] = 0;
    } else if (exception_buffer[component]<-4) {
        archlib::Exception msg;
        msg.source = ros::this_node::getName();
        msg.target = "/engine";
        msg.content = component+"=-1";
        except.publish(msg);
        exception_buffer[component] = 0;
    }
    
    invocations[component].clear();
}