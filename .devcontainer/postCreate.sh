python-rospy
cd /workspaces/bsn &&\
    rosdep install --from-paths src --ignore-src -r -y &&\
    catkin_make