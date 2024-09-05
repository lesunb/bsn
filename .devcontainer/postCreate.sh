cd /workspaces/bsn &&\
    rosdep install --from-paths src --ignore-src -r -y &&\
    rm -rf build &&\
    rm -rf devel &&\
    catkin_make
    echo "source /workspaces/bsn/devel/setup.sh" >> /root/.bashrc
    source /opt/ros/melodic/setup.bash

