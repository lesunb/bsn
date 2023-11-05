source /opt/ros/melodic/setup.bash

function cleanupBSN() { 
    kill $(cat /var/tmp/data_access.pid && rm /var/tmp/data_access.pid) & sleep 1s
    kill $(cat /var/tmp/strategy_enactor.pid && rm /var/tmp/strategy_enactor.pid) & sleep 1s
    kill $(cat /var/tmp/logger.pid && rm /var/tmp/logger.pid) & sleep 1s
    kill $(cat /var/tmp/probe.pid && rm /var/tmp/probe.pid) & sleep 1s
    kill $(cat /var/tmp/effector.pid && rm /var/tmp/effector.pid) & sleep 1s
    kill $(cat /var/tmp/g4t1.pid && rm /var/tmp/g4t1.pid) & sleep 1s
    kill $(cat /var/tmp/g3t1_1.pid && rm /var/tmp/g3t1_1.pid) & sleep 1s
    kill $(cat /var/tmp/g3t1_2.pid && rm /var/tmp/g3t1_2.pid) & sleep 1s
    kill $(cat /var/tmp/g3t1_3.pid && rm /var/tmp/g3t1_3.pid) & sleep 1s
    kill $(cat /var/tmp/g3t1_4.pid && rm /var/tmp/g3t1_4.pid) & sleep 1s
    kill $(cat /var/tmp/g3t1_5.pid && rm /var/tmp/g3t1_5.pid) & sleep 1s
    kill $(cat /var/tmp/g3t1_6.pid && rm /var/tmp/g3t1_6.pid) & sleep 1s
    kill $(cat /var/tmp/patient.pid && rm /var/tmp/patient.pid) & sleep 1s
    kill $(cat /var/tmp/injector.pid && rm /var/tmp/injector.pid) & sleep 1s
    kill $(cat /var/tmp/strategy_manager.pid && rm /var/tmp/strategy_manager.pid) & sleep 1s
    kill $(pgrep roscore)
}

export -f cleanupBSN
