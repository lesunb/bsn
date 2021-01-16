# BSN implementation on ROS

This is a Body Sensor Network implementation on ROS. So far, the BSN was used for experimentation on solutions for adaptation on the Self-Adaptive Software Systems domain, refer to https://doi.org/10.1145/3194133.3194147 and https://doi.org/10.1109/SEAMS.2019.00020 for more information.  Moreover, information regarding the prototype behaviour and how to develop your own manager is provided in the https://bodysensornetwork.herokuapp.com/ website, which contains an executable instance of the BSN. The following instructions will guide you to to compile, deploy and run the BSN on Linux Ubuntu 18.04 with ROS Melodic distributions. We have not yet tested on other distributions.

## Dependencies:
* [Ros Melodic](http://wiki.ros.org/melodic) which provides software libraries for BSN engines.
* [Cpp rest Sdk](https://github.com/Microsoft/cpprestsdk) which implements HTTP protocols on C++ (get, post...)
* [Lepton](https://github.com/rdinizcal/lepton) ("lightweight expression parser") is a small C++ library for parsing, evaluating, differentiating, and analyzing mathematical expressions.
* [Bsn Library](https://github.com/rdinizcal/libbsn)  provides the implementation of sensors, data fusers and emergency detection
* [Bsn arch](https://github.com/rdinizcal/arch)

## Install dependencies: 
#### ROS:
First it is required to install ROS Melodic. Our development team is strictly using Ubuntu 18.04 (Bionic). To install it please follow this [link](http://wiki.ros.org/melodic/Installation/Ubuntu).  
Also, it is strongly advised to use catkin for managing the ROS packages, refer to this [link](http://wiki.ros.org/ROS/Tutorials/InstallingandConfiguringROSEnvironment) after installing ROS Melodic. As such you will need to create a catkin workspace. You can do so by following the steps:

```
mkdir -p ~/catkin_ws/src
cd ~/catkin_ws/
catkin_make
```

#### CPP rest sdk:
In order to use Cpp rest sdk, it is required to build its dependency source code.  
First install the dependencies.

```
sudo apt-get install g++ git libboost-atomic-dev libboost-thread-dev libboost-system-dev libboost-date-time-dev libboost-regex-dev libboost-filesystem-dev libboost-random-dev libboost-chrono-dev libboost-serialization-dev libwebsocketpp-dev openssl libssl-dev ninja-build
```

Then, clone the repository.

```
git clone https://github.com/Microsoft/cpprestsdk.git casablanca
```

And finally, build it.
```
cd casablanca
mkdir build.debug
cd build.debug
cmake -G Ninja .. -DCMAKE_BUILD_TYPE=Debug
sudo ninja install
```

#### Lepton:
1. First, create and enter build folder.
```
cd lepton
``` 
``` 
mkdir build && cd build
``` 

3. Execute cmake from the build folder.
``` 
cmake ..
``` 

4. Finally, compile and install lepton library.
``` 
sudo make install
``` 

#### Libbsn:
1. Create and enter build folder.
```
cd libbsn
``` 
``` 
mkdir build && cd build
``` 

3. Execute cmake from the build folder.
``` 
cmake ..
``` 

4. Finally, compile and install libbsn library.
``` 
sudo make install
``` 
Once ALL the dependencies have been successfully installed, you can proceed to the next steps.

## Compiling BSN and arch lib

1. Compile under 'catkin_ws' directory.
```
cd ~/catkin_ws/ && 
catkin_make
``` 
## Configuration and Execution

3. Configure roslaunch files for personalized execution under '/catkin_ws/src/bsn/configurations';

4. Execute the BSN either by executing the pre-set run.sh file, that executes all nodes, 
or use roslaunch x.launch to execute a single node:
```
cd ~/catkin_ws/src/bsn/ && 
bash run.sh
``` 

#### In case or error due to the ROS path

You might want to source the setup.bash inside the catkin workspace:
```
echo "source ~/catkin_ws/devel/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

#### In case or error due to cpprestsdk(casablanca) not finding libcrypto

Follow the instructions in the (isuue#1388 from cpprest)[https://github.com/microsoft/cpprestsdk/issues/1388#issuecomment-619570350].
Add the line `INTERFACE_LINK_LIBRARIES "OpenSSL::SSL"` as in the following code:
```
set_target_properties(cpprestsdk::cpprestsdk_openssl_internal PROPERTIES
  INTERFACE_COMPILE_DEFINITIONS "CPPREST_NO_SSL_LEAK_SUPPRESS"
  INTERFACE_LINK_LIBRARIES "OpenSSL::SSL"
)
```

## Main Authors

* **Ricardo D. Caldas** - https://github.com/rdinizcal
* **Gabriel Levi** - https://github.com/gabrielevi10
* **Léo Moraes** - https://github.com/leooleo  
* **Eric B. Gil** - https://github.com/ericbg27/

Adviser: **Genaína N. Rodrigues** - https://cic.unb.br/~genaina/
