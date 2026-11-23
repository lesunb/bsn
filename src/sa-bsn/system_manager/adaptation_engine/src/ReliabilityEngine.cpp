#include "engine/ReliabilityEngine.hpp"

using namespace bsn::goalmodel;

struct comp{
    template<typename T>
    bool operator()(const T& l, const T& r) const
    {
        if (l.second != r.second)
            return l.second < r.second;
 
        return l.first < r.first;
    }
};

ReliabilityEngine::ReliabilityEngine(int  &argc, char **argv, std::string name): Engine(argc, argv, name), setpoint(), offset(), gain(), tolerance(0.02), cycles(0), prefix("R_"), enact() {}

ReliabilityEngine::~ReliabilityEngine() {}

void ReliabilityEngine::setUp() {
    Engine::setUp();
    ros::NodeHandle handle;
    handle.getParam("setpoint", setpoint);
	handle.getParam("offset", offset);
	handle.getParam("gain", gain);

    enact = handle.advertise<archlib::Strategy>("strategy", 10);
}

void ReliabilityEngine::tearDown() {
    Engine::tearDown();
}

std::string ReliabilityEngine::get_prefix() {
    return prefix;
}


/**
   Returns an initialized strategy with init_value values.
   @param terms The terms that compose the strategy.
   @return The map containing terms of the formula and initial values.
 */
std::map<std::string, double> ReliabilityEngine::initialize_strategy(std::vector<std::string> terms){
    std::map<std::string, double> strategy;
    
    for (std::vector<std::string>::iterator it = terms.begin(); it != terms.end(); ++it) {
        strategy[*it] = 1;
    }

    return strategy;
}

/**
   Returns an initialized priorities vector with init_value values.
   @param terms The terms that compose the strategy.
   @return The map containing terms of the formula and initial values.
 */
std::map<std::string, int> ReliabilityEngine::initialize_priority(std::vector<std::string> terms) {
    std::map<std::string, int> priority;
    
    for (std::vector<std::string>::iterator it = terms.begin(); it != terms.end(); ++it) {
        if((*it).find("R_") != std::string::npos) {
            priority[*it] = 50;
        }
    }

    return priority;
}

void ReliabilityEngine::monitor() {
    ROS_DEBUG(" ");
    cycles++;

    // request system status data for the knowledge repository
    ros::NodeHandle client_handler;
    ros::ServiceClient client_module;

    client_module = client_handler.serviceClient<archlib::DataAccessRequest>("DataAccessRequest");
    
    //reset the formula_str
    for (std::map<std::string,double>::iterator it = strategy.begin(); it != strategy.end(); ++it){
        if(it->first.find("CTX_") != std::string::npos)  it->second = 0;
        if(it->first.find("R_") != std::string::npos)  it->second = 1;
        if(it->first.find("F_") != std::string::npos)  it->second = 1;
    }

    archlib::DataAccessRequest r_srv;
    r_srv.request.name = "/engine";
    r_srv.request.query = "all:reliability:" + std::to_string(info_quant);

    if(!client_module.call(r_srv)) {
        ROS_ERROR("Failed to connect to data access node.");
        return;
    } /*request reliability for all tasks*/
    
    //expecting smth like: "/g3t1_1:success,fail,success;/g4t1:success; ..."
    std::string ans = r_srv.response.content;
    if(ans == ""){
        ROS_ERROR("Received empty answer when asked for reliability.");
    }

    std::vector<std::string> pairs = bsn::utils::split(ans, ';');
    
    for (std::string it : pairs) {
        std::vector<std::string> pair = bsn::utils::split(it, ':');
        std::string first = pair[0];
        std::string second = pair[1];

        //a "/g3t1_1 arrives here"
        std::transform(first.begin(), first.end(),first.begin(), ::toupper); // /G3T1_1
        first.erase(0,1); // G3T1_1
        first.insert(int(first.find('T')),"_"); // G3_T1_1

        std::vector<std::string> values = bsn::utils::split(second, ',');

        strategy["R_" + first] = stod(values[values.size()-1]);
        ROS_DEBUG("R_%s = %.2f",first.c_str(), strategy["R_" + first]);
    } 

    //request context status for all tasks
    archlib::DataAccessRequest c_srv;
    c_srv.request.name = "/engine";
    c_srv.request.query = "all:event:1";

    if (!client_module.call(c_srv)) {
        ROS_ERROR("Failed to connect to data access node.");
        return;
    } 
    
    //expecting smth like: "/g3t1_1:activate;/g4t1:deactivate; ..."
    ans = c_srv.response.content;

    if (ans == "") {
        ROS_ERROR("Received empty answer when asked for event.");
    }

    std::vector<std::string> ctx_pairs = bsn::utils::split(ans, ';');
    
    for (std::string ctx : ctx_pairs) {
        std::vector<std::string> pair = bsn::utils::split(ctx, ':');
        std::string first = pair[0];
        std::string second = pair[1];

        //a "/g3t1_1 arrives here"
        std::transform(first.begin(), first.end(),first.begin(), ::toupper); // /G3T1_1
        first.erase(0,1); // G3T1_1
        first.insert(int(first.find('T')),"_"); // G3_T1_1

        std::vector<std::string> values = bsn::utils::split(second, ',');
        for (std::string value : values) {
            if (first != "G4_T1") {
                strategy["CTX_" + first] = 1;
                
                if (value == "deactivate") {
                    strategy["R_" + first] = 1;
                    deactivatedComponents["R_" + first] = 1;
                    ROS_WARN("%s was deactivated and its reliability was set to 1", first.c_str());
                }
            } else {
                if (value == "activate") {
                    strategy["CTX_" + first] = 1;
                    deactivatedComponents["R_" + first] = 0;
                } else {
                    strategy["CTX_" + first] = 0; 
                    deactivatedComponents["R_" + first] = 1;
                }
            }
        }
    }
    
    analyze();
}

void ReliabilityEngine::analyze() {
    ROS_DEBUG(" ");

    double r_curr;
    double error;

    r_curr = calculate_qos(target_system_model,strategy);

    error = setpoint - r_curr;
    // if the error is out of the stability margin, plan!
    if ((error > setpoint * tolerance) || (error < -tolerance * setpoint)) {
        if (cycles >= monitor_freq / actuation_freq) {
            cycles = 0;
            plan();
        }
    }
    
}

void ReliabilityEngine::plan() {
    ROS_DEBUG(" ");

    ROS_DEBUG ("setpoint= %.2f", setpoint);
    double r_curr = calculate_qos(target_system_model,strategy);
    ROS_DEBUG("r_curr= %.2f",r_curr);
    double error = setpoint - r_curr;
    ROS_DEBUG("error= %.2f",error);

    //reset the formula_str
    std::vector<std::string> r_vec;
    for (std::map<std::string,double>::iterator it = strategy.begin(); it != strategy.end(); ++it) {
        if(it->first.find("R_") != std::string::npos) {
            std::string task = it->first;
            task.erase(0,2);
            if((strategy["CTX_"+task] != 0) && (strategy["F_"+task] != 0)){ // avoid ctx = 0 components thus infinite loops
                if(!deactivatedComponents[it->first]) {
                    r_vec.push_back(it->first);
                    strategy[it->first] = r_curr;
                } else {
                    strategy[it->first] = 1;
                }
            }
        }
    }  

    //reorder r_vec based on priority
    std::vector<std::string> aux = r_vec;
    r_vec.clear();
    std::set<std::pair<std::string,int>, comp> set(priority.begin(), priority.end());

    for (auto const &pair : set) {
        if (!deactivatedComponents[pair.first] && std::find(aux.begin(), aux.end(), pair.first) != aux.end()) { // key from priority exists in r_vec
            r_vec.push_back(pair.first);
        }
    }

    // ladies and gentleman, the search...

    std::vector<std::map<std::string, double>> solutions;
    for(std::vector<std::string>::iterator i = r_vec.begin(); i != r_vec.end(); ++i) { 
        //reset offset
        for (std::vector<std::string>::iterator it = r_vec.begin(); it != r_vec.end(); ++it) {
            if(error>0){
                strategy[*it] = r_curr*(1-offset);
            } else if(error<0) {
                strategy[*it] = (r_curr*(1+offset)>1)?1:r_curr*(1+offset);
            }
        }
        double r_new = calculate_qos(target_system_model,strategy);
        ROS_DEBUG("offset= %.2f", r_new);

        std::map<std::string,double> prev;
        double r_prev=0;
        if(error > 0){
            do {
                prev = strategy;
                r_prev = r_new;
                strategy[*i] += gain*error;
                r_new = calculate_qos(target_system_model,strategy);
            } while(r_new < setpoint && r_prev < r_new && strategy[*i] > 0 && strategy[*i] < 1);
        } else if (error < 0){
            do {
                prev = strategy;
                r_prev = r_new;
                strategy[*i] += gain*error;
                r_new = calculate_qos(target_system_model,strategy);
            } while(r_new > setpoint && r_prev > r_new && strategy[*i] > 0 && strategy[*i] < 1);
        }

        strategy = prev;
        r_new = calculate_qos(target_system_model,strategy);

        for(std::vector<std::string>::iterator j = r_vec.begin(); j != r_vec.end(); ++j) { // all the others
            if(*i == *j) continue;

            if(error > 0){
                do {
                    prev = strategy;
                    r_prev = r_new;
                    strategy[*j] += gain*error;
                    r_new = calculate_qos(target_system_model,strategy);
                } while(r_new < setpoint && r_prev < r_new && strategy[*j] > 0 && strategy[*j] < 1);
            } else if (error < 0) {
                do {
                    prev = strategy;
                    r_prev = r_new;
                    strategy[*j] += gain*error;
                    r_new = calculate_qos(target_system_model,strategy);
                } while(r_new > setpoint && r_prev > r_new && strategy[*j] > 0 && strategy[*j] < 1);
            }
            
            strategy = prev;
            r_new = calculate_qos(target_system_model,strategy);
        }
        solutions.push_back(strategy);
    }

    for (std::vector<std::map<std::string,double>>::iterator it = solutions.begin(); it != solutions.end(); it++){
        strategy = *it;
        double r_new = calculate_qos(target_system_model,strategy);

        /*ROS_DEBUG("strategy: [");
        for (std::map<std::string,double>::iterator itt = (*it).begin(); itt != (*it).end(); ++itt) {
            if(itt->first.find("R_") != std::string::npos) {
                ROS_DEBUG("%s : %s, "itt->first,itt->second);
            }
        }
        ROS_DEBUG("] = %s", std::string(r_new);*/

        if(/*!blacklisted(*it) && */(r_new > setpoint*(1-tolerance) && r_new < setpoint*(1+tolerance))){ // if not listed and converges, yay!
            execute();
            return;
        }
    }

    ROS_INFO("Did not converge :(");
}

void ReliabilityEngine::execute() {
    ROS_DEBUG(" ");

    std::string content = "";
    size_t index = 0;
    bool flag = false;  //nasty
    bool flagO = false; //uber nasty
    //get the reliabilities in the formula_str and send!
    // send in form "/g3t1_1:0.89;/g4t1=0.2;..."
    for (std::map<std::string,double>::iterator it = strategy.begin(); it != strategy.end(); ++it) {
        std::string aux = "";
        if(it->first.find("R_") != std::string::npos) { //if it is a R_ term of the formula_str 
            aux += it->first;
            std::transform(aux.begin(), aux.end(), aux.begin(), ::tolower);

            std::vector<std::string> str = bsn::utils::split(aux, '_');
            content += "/";
            content += str[1]; //g3
            content += str[2] ; //t1
            if(str.size()>3) content += "_" + str[3]; //_1:
            content += ":"; 
            content += std::to_string(it->second) + ","; // 0.82 
            flag = true;
        }
        if(flag){
            //remove last ','
            content.pop_back();
            content += ";";
            flag = false;
            flagO = true;
        }
        aux.clear();
    }

    //remove last ';'
    if(flagO) content.pop_back();

    archlib::Strategy msg;
    msg.source = "/engine";
    msg.target = "/enactor";
    msg.content = content;

    enact.publish(msg);

    ROS_DEBUG("[%s]",content.c_str());

    return;
}
