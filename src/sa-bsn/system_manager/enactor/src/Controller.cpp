#include "controller/Controller.hpp"

#include <iostream>

Controller::Controller(int &argc, char **argv, std::string name) : Enactor(argc, argv, name) {}

Controller::~Controller() {}

void Controller::setUp() {
    ros::NodeHandle nh;

    adapt = nh.advertise<archlib::AdaptationCommand>("log_adapt", 10);
    
    except = nh.advertise<archlib::Exception>("exception", 10);

    double freq;
    nh.getParam("frequency", freq);
    nh.getParam("kp", KP);
    nh.getParam("adaptation_parameter", adaptation_parameter);
    rosComponentDescriptor.setFreq(freq);

    // --- CORREÇÃO: Aguarda os serviços críticos estarem online antes de continuar ---
    ROS_INFO("Waiting for critical services to become available...");
    
    // Aguarda o serviço do Strategy Manager (EngineRequest) por até 10 segundos
    if (!ros::service::waitForService("EngineRequest", ros::Duration(10.0))) {
        ROS_ERROR("Timeout waiting for Strategy Manager service (EngineRequest)!");
    }

    // Aguarda o serviço do Data Access por até 10 segundos
    if (!ros::service::waitForService("DataAccessRequest", ros::Duration(10.0))) {
        ROS_ERROR("Timeout waiting for Data Access service (DataAccessRequest)!");
    }

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
    ROS_DEBUG("r_ref[%s] = %.2f",component.c_str(),r_ref[component]);
    ROS_DEBUG("r_curr[%s] = %.2f",component.c_str(), r_curr[component]);
    ROS_DEBUG("kp[%s] = %.2f",component.c_str(), kp[component]);

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
                ROS_DEBUG("################################################");
                ROS_DEBUG("Adapting Centralhub");
                ROS_DEBUG("Action: %s", msg.action.c_str());
                ROS_DEBUG("################################################");
            } /*else {
                ROS_ERROR("COULD NOT ADAPT CENTRALHUB");
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

void Controller::apply_cost_strategy(const std::string &component) {
    ROS_DEBUG("r_ref[%s] = %.2f",component.c_str(),c_ref[component]);
    ROS_DEBUG("r_curr[%s] = %.2f",component.c_str(), c_curr[component]);
    ROS_DEBUG("kp[%s] = %.2f",component.c_str(), kp[component]);

    double error = c_ref[component] - c_curr[component]; //error = Cref - Ccurr

    if(error > stability_margin*c_ref[component] || error < stability_margin*c_ref[component]) {

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
                ROS_DEBUG("################################################");
                ROS_DEBUG("Adapting Centralhub");
                ROS_DEBUG("Action: %s", msg.action.c_str());
                ROS_DEBUG("################################################");
            } /*else {
                ROS_ERROR("COULD NOT ADAPT CENTRALHUB");
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
                if(new_freq >= 0.5 && new_freq <= 25) {
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