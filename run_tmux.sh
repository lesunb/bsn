#!/bin/bash

bsn_root=$PWD
bsn=${bsn_root}/src/sa-bsn
exec_time=0

if [[ "$#" -gt 1 ]]; then
    echo "Too many arguments were passed!"
    exit 1
fi

if [[ "$#" -eq 0 ]]; then
    exec_time=300
else
    exec_time=$1
fi

if [[ -n ${exec_time//[0-9]/} ]]; then
    echo "The execution time is not an integer!"
    exit 1
fi

function preLaunch() { 
    echo "source ${bsn_root}/devel/setup.sh && cd ${bsn}/configurations/$1"
}

SESSION_NAME=bsn

tmux kill-session -t $SESSION_NAME  > /dev/null

tmux new -d -s $SESSION_NAME

echo "Starting knowledge repository"
################# KNOWLEDGE REPOSITORY #################
config_name="knowledge_repository"
tmux new-window \
    -t $SESSION_NAME: \
    -n data_access \
    "$(preLaunch ${config_name}) && roslaunch --pid=/var/tmp/data_access.pid data_access.launch"
sleep 5 

echo "Starting manager system"
################# MANAGER SYSTEM #################
config_name="system_manager"

tmux new-window \
    -t $SESSION_NAME: \
    -n strategy_manager \
    "$(preLaunch ${config_name}) && roslaunch --pid=/var/tmp/strategy_manager.pid strategy_manager.launch"
sleep 7

tmux new-window \
    -t $SESSION_NAME: \
    -n strategy_enactor \
    "$(preLaunch ${config_name}) && roslaunch --pid=/var/tmp/strategy_enactor.pid strategy_enactor.launch"
sleep 1

echo "Starting logging"
# ################# LOGGING INFRASTRUCTURE #################
config_name="logging_infrastructure"
tmux new-window \
    -t $SESSION_NAME: \
    -n logger \
    "$(preLaunch ${config_name}) && roslaunch --pid=/var/tmp/logger.pid logger.launch"
sleep 1


echo "Starting application"
# ################# APPLICATION #################
config_name="target_system"
tmux new-window \
    -t $SESSION_NAME: \
    -n probe \
    "$(preLaunch ${config_name}) && roslaunch --pid=/var/tmp/probe.pid probe.launch"
sleep 1

tmux new-window \
    -t $SESSION_NAME: \
    -n effector \
    "$(preLaunch ${config_name}) && roslaunch --pid=/var/tmp/effector.pid effector.launch"
sleep 1

tmux new-window \
    -t $SESSION_NAME: \
    -n g4t1 \
    "$(preLaunch ${config_name}) && roslaunch --pid=/var/tmp/g4t1.pid g4t1.launch"
sleep 1

config_name="environment"
tmux new-window \
    -t $SESSION_NAME: \
    -n patient \
    "$(preLaunch ${config_name}) && roslaunch --pid=/var/tmp/patient.pid patient.launch"
sleep 1

config_name="target_system"
tmux new-window \
    -t $SESSION_NAME: \
    -n g3t1_1 \
    "$(preLaunch ${config_name}) && roslaunch --pid=/var/tmp/g3t1_1.pid g3t1_1.launch"
sleep 1

tmux new-window \
    -t $SESSION_NAME: \
    -n g3t1_2 \
    "$(preLaunch ${config_name}) && roslaunch --pid=/var/tmp/g3t1_2.pid g3t1_2.launch"
sleep 2s

tmux new-window \
    -t $SESSION_NAME: \
    -n g3t1_3 \
    "$(preLaunch ${config_name}) && roslaunch --pid=/var/tmp/g3t1_3.pid g3t1_3.launch"
sleep 2s

tmux new-window \
    -t $SESSION_NAME: \
    -n g3t1_4 \
    "$(preLaunch ${config_name}) && roslaunch --pid=/var/tmp/g3t1_4.pid g3t1_4.launch"
sleep 2s

tmux new-window \
    -t $SESSION_NAME: \
    -n g3t1_5 \
    "$(preLaunch ${config_name}) && roslaunch --pid=/var/tmp/g3t1_5.pid g3t1_5.launch"
sleep 2s

tmux new-window \
    -t $SESSION_NAME: \
    -n g3t1_6 \
    "$(preLaunch ${config_name}) && roslaunch --pid=/var/tmp/g3t1_6.pid g3t1_6.launch"
sleep 2s


echo "Starting simulation"
# ################# SIMULATION #################
config_name="simulation"
tmux new-window \
    -t $SESSION_NAME: \
    -n simulation \
    "$(preLaunch ${config_name}) && roslaunch --pid=/var/tmp/injector.pid injector.launch"

# see file .devcontainer/additional_bashrc for this command's source 
sleep "${exec_time}"s && cleanupBSN &

tmux a -t ${SESSION_NAME}
