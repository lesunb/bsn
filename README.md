# Self-Adaptive Body Sensor Network (SA-BSN)

![GitHub](https://img.shields.io/github/license/lesunb/bsn) ![GitHub release (latest by date)](https://img.shields.io/github/v/release/lesunb/bsn) [![DOI](https://zenodo.org/badge/233956479.svg)](https://zenodo.org/badge/latestdoi/233956479)

The Self-Adaptive Body Sensor Network (SA-BSN) features an exempalr of self-adaptive system [[1]](https://doi.org/10.1109/SEAMS51251.2021.00037) designed for experimentation on solutions for adaptation in the domain of Self-Adaptive Software Systems. Body Sensor Networks (BSNs) are networks of wearable and implantable sensors that collect physiological data (e.g., heart beat rate, blood oxigenation) from the human body. These networks are often considered safety-critical, as they enable real-time monitoring of vital signs and other health-related parameters. In addition, they interface a body of knowledge of ever evolving diseases and health conditions with a the vastness of human individuality. No solution to indentification of health conditions is comprehensive enough to tackle the current nor future diseases that may pose a threat to human condition. The self-adaptive body sensor network paves the way to such ambitious goal.

The SA-BSN provides a platform for researchers and developers to explore and evaluate adaptive solutions in the Self-Adaptive Software Systems domain. It has been utilized in various experiments and studies, as referenced in the following publications: [[2]](https://doi.org/10.1145/3194133.3194147)[[3]](https://doi.org/10.1109/SEAMS.2019.00020)[[4]](https://doi.org/10.1145/3387939.3391595).

## Recommended Reference

```
@INPROCEEDINGS{bsn,
  author={Gil, Eric Bernd and Caldas, Ricardo and Rodrigues, Arthur and da Silva, Gabriel Levi Gomes and Rodrigues, Genaína Nunes and Pelliccione, Patrizio},
  booktitle={2021 International Symposium on Software Engineering for Adaptive and Self-Managing Systems (SEAMS)}, 
  title={Body Sensor Network: A Self-Adaptive System Exemplar in the Healthcare Domain}, 
  year={2021},
  pages={224-230},
  doi={10.1109/SEAMS51251.2021.00037}}
``` 

## Getting Started

Check our [demonstration video of the SA-BSN](https://youtu.be/iDEd_tW9JZE).

Download our [SA-BSN Virtual Machine (Virtual Box) for People in a Hurry](https://drive.google.com/file/d/1RYrZ27LWRvqaxsgNcApXMxwrLK6BBPsV/view?usp=sharing). 
(_~10 minutes!!_)

The password from the virtual machine is the same as the user. So,

```
user: bsn
password: bsn
```

To compile and run the SA-BSN, follow the instructions (tested on Linux Ubuntu 18.04 with ROS Melodic): 

### Build the SA-BSN

_(Jump this step if you are in our provided VM)_

#### **Dependencies**

[ROS Melodic for Ubuntu 18.04](http://wiki.ros.org/melodic/Installation/Ubuntu) is the underlying framework in which the SA-BSN runs.
* Python 3.8 and python libraries:
  * pickle
  * pandas
  * seaborn
  * sklearn

### 1.2) Execute the SA-BSN
[Catkin](http://wiki.ros.org/ROS/Tutorials/InstallingandConfiguringROSEnvironment) for ROS packages management. 

[Rosdep](https://wiki.ros.org/rosdep#Installing_rosdep) for ROS dependencies management.

[Rosmon](http://wiki.ros.org/rosmon) for execution and node monitoring.

[Rosserial](http://wiki.ros.org/rosserial_arduino) (optional) for execution with Arduino and sensors

#### **Create clone and build**

Clone the sa-bsn.

```
git clone https://github.com/lesunb/bsn.git
```

Enter the sa-bsn folder, install internal dependencies, and then compile it with catkin.

```
cd bsn &&
rosdep install --from-paths src --ignore-src -r -y &&
catkin_make
```

To run tests:
```
catkin_make run_tests && catkin_test_results
```

### Execute the SA-BSN

The SA-BSN's execution relies on a single command, where the argument (i.e., 600) represents the execution time (in seconds):

```
roscore
```

```
cd bsn && 
mon launch bsn.launch
``` 

If you want to coneect with Arduino and real sensors use:

```
roscore
rosrun rosserial_python serial_node.py "Arduino serial port"
```

The Arduino serial port is given by the operating system. In ubuntu it is usually "/dev/ttyACM0".

```
cd bsn && 
mon launch bsn_sensors.launch
``` 

In case you don't have rosmon installed, try:

```
cd bsn && 
bash run.sh 600
``` 

For a customized execution, check the configuration files under sa-bsn/configurations.

### Analyze the SA-BSN

During the execution a logging mechanism records data in logfiles, that can be found in sa-bsn/src/knowledge_repository/resource/logs. Each logfile is named after a type of message and an id (i.e., logName_logID) and the entries are composed by the messages content.

To compute the evolution of the QoS attributes (i.e., reliability and cost) over time and how well the adaptation manager adapts the system, we use a python script that reads the logs as input and plots a timeseries + displays adaptation metrics as output.

The python script can be found at sa-bsn/src/sa-bsn/simulation/analyzer.

To compute the QoS attributes and analyze the adaptation, type:

```
cd bsn/src/sa-bsn/simulation/analyzer
python3 analyzer.py [logID] [metric] [plot_component_metrics] [setpoint]
```

where:

* [logID] is the ID for the execution log files.
* [metric] is the name of the QoS attribute (e.g., reliability)
* [plot_component_metrics] is a boolean parameter that defines whether individual component's QoS attribute should be plotted or not.
* [setpoint] is the value of the setpoint used in the execution.

One example of the command usage is:

```
python3 analyzer.py 1610549979516318295 reliability False 0.9
```

## Common Mistakes

### In case of error due to the ROS path

You might want to source the setup.bash inside the catkin workspace:
```
echo "source ~/bsn/devel/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

Main Authors

* [**Ricardo Caldas**](https://rdinizcal.github.io/)
* [**Gabriel Levi**](https://github.com/gabrielevi10)
* [**Léo Moraes**](https://github.com/leooleo)  
* [**Eric B. Gil**](https://github.com/ericbg27)
* [**Samuel Couto**](https://github.com/SCouto97)

Adviser: [**Genaína N. Rodrigues**](https://genaina.github.io/)

## Acknowledgment

This study was financed in part by CAPES-Brasil – Finance Code 001, through CAPES scholarship, by CNpq under grant number 306017/2018-0, by University of Brasilia under Call DPI/DPG 03/2020, by FAPDF Call 03/2018 by the Wallenberg Al, Autonomous Systems and Software Program (WASP) funded by the Knut and Alice Wallenberg Foundation
