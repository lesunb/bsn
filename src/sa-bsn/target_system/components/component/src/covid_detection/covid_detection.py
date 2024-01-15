#!/usr/bin/env python
import rospy
from messages.msg import TargetSystemData

import pickle
import pandas as pd

def callback(data):
    caminho = __file__.replace("covid_detection.py", "model_covid_prediction.pkl")
    # Abrir o arquivo pickle e carregar o modelo
    with open(caminho, 'rb') as file:
        model = pickle.load(file)

    data_to_test = pd.DataFrame({'Oxygen': data.oxi_data, 'PulseRate': data.ecg_data, 'Temperature': ((data.trm_data * 1.8) + 32)}, index=[0])
    resultado = model.predict(data_to_test)
    debug = 1
    if(debug==1):
        # Realiza a previsao de um unico caso de teste
        rospy.loginfo("Debug: oxi_data %f" % (data.oxi_data))
        rospy.loginfo("Debug: ecg_data %f" % (data.ecg_data))
        rospy.loginfo("Debug: trm_data C %f" % (data.trm_data))
        rospy.loginfo("Debug: trm_data F %f" % ((data.trm_data * 1.8) + 32))
        rospy.loginfo("Debug: Covid suspect %i" % (resultado))
    if(resultado[0]==1):
        rospy.loginfo("The patient's condition was compatible with a suspected case of Covid-19. Please see a doctor.")
    else:
        rospy.loginfo("The patient's condition appears to be without signs of Covid-19. If you experience any symptoms, consult a doctor")

def listener():
    rospy.init_node('covid_detection_listener', anonymous=True)
    rospy.Subscriber("TargetSystemData", TargetSystemData, callback)

    # spin() simply keeps python from exiting until this node is stopped
    rospy.spin()

if __name__ == '__main__':
    listener()