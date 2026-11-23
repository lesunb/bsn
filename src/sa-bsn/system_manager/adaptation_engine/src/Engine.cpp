#include "engine/Engine.hpp"

using namespace bsn::goalmodel;

Engine::Engine(int  &argc, char **argv, std::string name): ROSComponent(argc, argv, name), info_quant(0), monitor_freq(1), actuation_freq(1), target_system_model(), strategy(),  priority() {}

Engine::~Engine() {}


void Engine::setUp() {
    ros::NodeHandle handle;
    handle.getParam("qos_attribute", qos_attribute);
    handle.getParam("info_quant", info_quant);
    handle.getParam("monitor_freq", monitor_freq);
    handle.getParam("actuation_freq", actuation_freq);

    rosComponentDescriptor.setFreq(monitor_freq);

    // Antes da alteração, se o Engine iniciasse frações de segundo mais rápido que o DataAccess, 
    // a chamada de serviço falhava, a formula_str retornava vazia, 
    // e o Engine entrava em um estado inválido ou crashava.
    
    // --- CORREÇÃO: Aguarda de forma segura o Data Access subir ---
    ROS_WARN("Engine waiting for DataAccessRequest service to become available...");
    if (!ros::service::waitForService("DataAccessRequest", ros::Duration(15.0))) {
        ROS_ERROR("Timeout waiting for Data Access service in Engine!");
    }

    std::string formula_str = "";
    // Tenta buscar a fórmula. Se falhar na primeira, tenta mais algumas vezes dando spin
    int retry_count = 0;
    while (ros::ok()) {
        formula_str = fetch_formula(qos_attribute);
        if (formula_str != "") {
            break;
        }
        
        retry_count++;
        if (retry_count > 10) {
            ROS_FATAL("Engine could not fetch formula after multiple attempts. Aborting.");
            return;
        }
        
        ros::spinOnce();
        ros::Duration(1.0).sleep();
    }
    
    setUp_formula(formula_str);

    enactor_server = handle.advertiseService("EngineRequest", &Engine::sendAdaptationParameter, this);
    ROS_WARN("EngineRequest service advertised successfully!");
}

void Engine::tearDown() {}

bool Engine::sendAdaptationParameter(archlib::EngineRequest::Request &req, archlib::EngineRequest::Response &res) {
    try {
        res.content = qos_attribute;
        return true;
    } catch(...) {
        return false;
    }
}

void Engine::receiveException(const archlib::Exception::ConstPtr& msg){
    std::string content = msg->content.c_str();

    std::vector<std::string> param = bsn::utils::split(content, '=');

    // /g3t1_1
    std::string first = param[0];
    std::transform(first.begin(), first.end(),first.begin(), ::toupper); // /G3T1_1
    first.erase(0,1); // G3T1_1
    first.insert(int(first.find('T')), "_"); // G3_T1_1
    first = get_prefix() + first; 

    if (priority.find(first) != priority.end()) {
        priority[first] += stoi(param[1]);
        if (priority[first] > 99) priority[first] = 100;
        if (priority[first] < 1) priority[first] = 0;
    } else {
        ROS_ERROR("COULD NOT FIND COMPONENT IN LIST OF PRIORITIES.");
    }
}

/**
   Sets up formula-related structures (i.e, target system model, strategy, and priority)
   @param formula_str A string containing the algebraic formula.
   @return void
 */
void Engine::setUp_formula(std::string formula_str) {
    target_system_model = bsn::model::Formula(formula_str);
    
    // Extracts the terms that will compose the strategy
    std::vector<std::string> terms = target_system_model.getTerms();
    strategy = initialize_strategy(terms);
    // Initializes the target system model
    calculate_qos(target_system_model,strategy);
    priority = initialize_priority(terms);

    return;
}


std::string Engine::fetch_formula(std::string name){
    ros::NodeHandle client_handler;
    ros::ServiceClient client_module;

    client_module = client_handler.serviceClient<archlib::DataAccessRequest>("DataAccessRequest");

    archlib::DataAccessRequest r_srv;
    r_srv.request.name = "/engine";
    r_srv.request.query = name + "_formula";

    if(!client_module.call(r_srv)) {
        ROS_ERROR("Tried to fetch formula string, but Data Access is not responding.");
        return "";
    }
    
    std::string formula_str = r_srv.response.content;

    if(formula_str == ""){
        ROS_ERROR("ERROR: Empty formula string received.");
    }

    return formula_str;
}

/**
 * Calculates the overall QoS attribute based on the target system model and configuration of parameters
 * @param model An algebraic target system model that represents the QoS attribute
 * @param conf A map of the target system model terms and values
 * @return The value of QoS attribute given the strategy
 */
double Engine::calculate_qos(bsn::model::Formula model, std::map<std::string, double> conf) {
    model.setTermValueMap(conf);
    return model.evaluate();
}

/*bool Engine::blacklisted(std::map<std::string,double> &strat) {
    for (std::vector<std::map<std::string,double>>::iterator it = blacklist.begin(); it != blacklist.end(); it++){
        if(*it == strat) return true;
    }

    return false;
}*/

void Engine::body(){
    ros::NodeHandle n;
    ros::Subscriber t_sub = n.subscribe("exception", 1000, &Engine::receiveException, this);

    ros::Rate loop_rate(rosComponentDescriptor.getFreq());
    int update=0;
    // ros::ok, sem os parenteses, e' o ENDERECO da funcao - sempre verdadeiro.
    // Com o typo este laco nunca via o pedido de shutdown: o no' ignorava o
    // SIGINT do roslaunch ate' levar SIGKILL, nunca rodava tearDown() e, num
    // build de cobertura, morria antes de o llvm gravar o .profraw (por isso
    // Engine/ReliabilityEngine/CostEngine apareciam com 0% mesmo com o
    // reli_engine subindo nos testes BDD).
    while (ros::ok()){
        update++;
        if (update >= rosComponentDescriptor.getFreq()*10){
            update = 0;
            std::string formula_str = fetch_formula(qos_attribute);
            if(formula_str=="") continue;
            setUp_formula(formula_str);
        }

        monitor();

        ros::spinOnce();
        loop_rate.sleep();        
    }   

    return;
}
