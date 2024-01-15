#include "component/Sensor.hpp"

Sensor::Sensor(int &argc, char **argv, const std::string &name, const std::string &type, const bool &active, const double &noise_factor, const bsn::resource::Battery &battery, const bool &instant_recharge) : Component(argc, argv, name), type(type), active(active), buffer_size(1), replicate_collect(1), noise_factor(0), battery(battery), data(0.0), instant_recharge(instant_recharge), cost(0.0) {}

Sensor::~Sensor() {}

Sensor& Sensor::operator=(const Sensor &obj) {
    this->type = obj.type;
    this->active = obj.active;
    this->noise_factor = obj.noise_factor;
    this->battery = obj.battery;
    this->data = obj.data;
    this->instant_recharge = obj.instant_recharge;
}

int32_t Sensor::run() {

	setUp();

    if (!shouldStart) {
        Component::shutdownComponent();
    }


    ros::NodeHandle nh;
    ros::Subscriber noise_subs = nh.subscribe("uncertainty_"+ros::this_node::getName(), 10, &Sensor::injectUncertainty, this);
    ros::Subscriber reconfig_subs = nh.subscribe("reconfigure_"+ros::this_node::getName(), 10, &Sensor::reconfigure, this);

    nh.getParam("connect_sensor_"+ros::this_node::getName(), connected_sensor);
    ROS_INFO("Sensor connected = %d", connected_sensor);
    


    sendStatus("init");
    ros::spinOnce();
    
    while (ros::ok()) {
        ros::Rate loop_rate(rosComponentDescriptor.getFreq());
        ros::spinOnce();

        try {
            body();
        } catch (const std::exception& e) {
            ROS_ERROR( "SENSOR FAILED: %s", e.what());
            sendStatus("fail");
            cost = 0;
        } 
        loop_rate.sleep();
    }
    
    return 0;
}

void Sensor::body() {
    
    if (!isActive() && battery.getCurrentLevel() > 90){
        turnOn();
    } else if (isActive() && battery.getCurrentLevel() < 2){
        turnOff();        
    }

    if(isActive()) {
        sendStatus("running");
        
        data = collect();

        /*for data replication, as if replicate_collect values were collected*/
        if(connected_sensor != 2){
            {
                double sum;
                for(int i = 0; i < replicate_collect; ++i) {
                    double aux_data = data;
                    apply_noise(aux_data);
                    sum += aux_data;
                }
                data = sum/replicate_collect;
            }
            data = process(data);
        }
        transfer(data);
		sendStatus("success");
        sendEnergyStatus(cost);
        cost = 0.0;
    } else {
        recharge();
        throw std::domain_error("out of charge");
    }
}

/*
 * error = noise_factor (%)
 * data +- [(error + rand(0,1)) * error] * data
 **/
void Sensor::apply_noise(double &data) {
    double offset = 0;
 
    offset = (noise_factor + ((double)rand() / RAND_MAX) * noise_factor) * data;
    data += (rand()%2==0)?offset:(-1)*offset;
    noise_factor = 0;
}

void Sensor::reconfigure(const archlib::AdaptationCommand::ConstPtr& msg) {
    std::string action = msg->action.c_str();

    std::vector<std::string> pairs = bsn::utils::split(action, ',');

    for (std::vector<std::string>::iterator it = pairs.begin(); it != pairs.end(); ++it){
        std::vector<std::string> param = bsn::utils::split(action, '=');

        if(param[0]=="freq"){
            double new_freq =  stod(param[1]);
            rosComponentDescriptor.setFreq(new_freq);
        } else if (param[0]=="replicate_collect") {
            int new_replicate_collect = stoi(param[1]);
            if(new_replicate_collect>1 && new_replicate_collect<200) replicate_collect = new_replicate_collect;
        }
    }
}

void Sensor::injectUncertainty(const archlib::Uncertainty::ConstPtr& msg) {
    std::string content = msg->content;

    std::vector<std::string> pairs = bsn::utils::split(content, ',');

    for (std::vector<std::string>::iterator it = pairs.begin(); it != pairs.end(); ++it){
        std::vector<std::string> param = bsn::utils::split(content, '=');

        if(param[0]=="noise_factor"){
            noise_factor = stod(param[1]);
        }
    }
}

bool Sensor::isActive() {
    return active;
}

void Sensor::turnOn() {
    active = true;
}

void Sensor::turnOff() {
    active = false;
}

double Sensor::collect_simulation(){
    double m_data = -1;
    ros::ServiceClient client = handle.serviceClient<services::PatientData>("getPatientData");
    services::PatientData srv;

    srv.request.vitalSign = name_node_sensor_simulation;

    if (client.call(srv)) {
        m_data = srv.response.data;
        ROS_INFO("new data collected: [%s]", std::to_string(m_data).c_str());
    } else {
        ROS_INFO("error collecting data");
    }
    return m_data;
}

double Sensor::collect_table(){
    double m_data = -1;

    // Get the path to the sensor data file
    std::string path_file_to_read = get_current_dir_name();
    path_file_to_read += "/data_to_read/";
    path_file_to_read += name_node_sensor;
    path_file_to_read += ".csv";

    std::ifstream file;
    file.open(path_file_to_read);
    if(file.is_open()){
        // Search for the next line of the file
        std::string line;
        std::string csvItem;
        int line_number_counter = 0;
        bool last_line = 1;
        line_marker++;
        while (std::getline(file, line)) {
            line_number_counter++;
            if(line_number_counter == 1){
                m_data = std::stof(line);
            }
            if(line_number_counter == line_marker) {
                m_data = std::stof(line);
                last_line = 0;
                return m_data;
            }
        }
        if(last_line && m_data != -1){
            ROS_INFO("The end of the data file %s has been reached. Starting reading again", (name_node_sensor+".csv").c_str());
            line_marker = 0;
        }
        if(m_data == -1){
            ROS_INFO("Could not open the file or the file is empty. Using simulation data");
            connected_sensor = 0;
            m_data = collect_simulation();
        }
        file.close();
    }
    else{
        ROS_INFO("Could not open the file! Using simulation data");
        std::ofstream o(path_file_to_read.c_str());
        connected_sensor = 0;
        m_data = collect_simulation();
    }
    return m_data;
}

double Sensor::collect_real_sensor(){
    double m_data = -1;

    std::string res;
    ros::ServiceClient client = handle.serviceClient<std_srvs::SetBool>(name_node_sensor);
    std_srvs::SetBool srv;
    srv.request.data = true;
    if (client.call(srv)) {
        res = srv.response.message;
        m_data = std::stof(res);
        ROS_INFO("new data collected: [%s]", std::to_string(m_data).c_str());
    } else {
        ROS_INFO("error collecting data");
    }
    return m_data;
}

void Sensor::convert_name() {
    std::string node_name = ros::this_node::getName();
    if(node_name == "/g3t1_1"){
        name_node_sensor = "spo2";
        name_node_sensor_simulation = "oxigenation";
    }
    else if(node_name == "/g3t1_2"){
        name_node_sensor = "bpm";
        name_node_sensor_simulation = "heart_rate";
    }
    else if(node_name == "/g3t1_3"){
        name_node_sensor = "temp";
        name_node_sensor_simulation = "temperature";
    }
    else if(node_name == "/g3t1_4"){
        name_node_sensor = "abps";
        name_node_sensor_simulation = "abps";
    }
    else if(node_name == "/g3t1_5"){
        name_node_sensor = "abpd";
        name_node_sensor_simulation = "abpd";
    }
    else if(node_name == "/g3t1_6"){
        name_node_sensor = "glucose";
        name_node_sensor_simulation = "glucose";
    }
    else{
        name_node_sensor = node_name;
        name_node_sensor_simulation = node_name;
    }
}

/*  battery will always recover in 200seconds
*
*  b/s = 100% / 200 seconds = 0.2 %/s 
*      => recovers 5% battery per second
*  if we divide by the execution frequency
*  we get the amount of battery we need to
*  recover per execution cycle to achieve the
*  0.2 %/s battery recovery rate
*/
void Sensor::recharge() {
    if(!instant_recharge) {
        if(battery.getCurrentLevel() <= 100) {
            battery.generate(1);
            // battery.generate((100/2000)/rosComponentDescriptor.getFreq());
        }
    } else {
        battery.generate(100);
    }
}