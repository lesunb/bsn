import subprocess
import time 
def before_all(context):
  
    #context.roscore = subprocess.Popen(
    #    ['roscore'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
    #)
    #time.sleep(14)
  
    
    context.bsn_launch = subprocess.Popen(
        ['roslaunch', 'bsn.launch'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
    )
    time.sleep(25)

def after_all(context):
    #context.roscore.terminate()
    context.bsn_launch.terminate()
