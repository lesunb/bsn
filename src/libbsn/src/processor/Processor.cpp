#include "libbsn/processor/Processor.hpp"
#include <stdio.h>

using namespace std;

namespace bsn {
    namespace processor {
        // Retorna o id baseado no tipo
        int32_t get_sensor_id(string type) {
            if (type == "thermometer")
                return 0;
            else if (type == "ecg")
                return 1;
            else if (type == "oximeter")
                return 2;
            else if (type == "abps")
                return 3;
            else if (type == "abpd")		
                return 4;
            else if (type == "glucosemeter")        
                return 5;
            else {
                cout << "UNKNOWN TYPE " + type + '\n';
                return -1;
            }

        }

        double get_value(string packet){
            double ret = stod(packet.substr(packet.find('-')+1,packet.length()));
            return ret;
        }

        double data_fuse(vector<double> packetsReceived) {	
            //FILE *fp;
            //fp = fopen("/home/samira/Downloads/dados_checagem.txt", "a");

            double average, risk_status;
            int32_t count = 0;
            average = 0;
            int32_t index = 0;
            double bpr_avg = 0.0;
            
            std::vector<double> values;
            std::vector<double>::iterator packets_it;
            for(packets_it = packetsReceived.begin();packets_it != packetsReceived.end();++packets_it){
                if(static_cast<int>(*packets_it) >= 0)  {
                    // Soma à média e retira da fila
                    if(index == 3 || index == 4) {
                        bpr_avg += *packets_it;
                    } else {
                        average += *packets_it;
                        values.push_back(*packets_it);
                    }

                    count++;
                }

                if(index == 4) {
                    if(bpr_avg >= 0.0) {
                        bpr_avg /= 2;
                        average += bpr_avg;
                        values.push_back(bpr_avg);
                    }
                }

                index++;
            }

            if(count == 0)
                return -1;

            // Calcula a media partir da soma dividida pelo número de pacotes lidos
            double avg = (average / count);
            //std::cout<<"-----------------Average ===: "+std::to_string(avg)<<std::endl;

            std::vector<double> deviations;
            double min = 1000; //Maior valor possível é 100
            double max = -1; //Menor valor possível é 0

            size_t i;

            for(i = 0;i < values.size();i++) {
                //Cálculo dos desvios individuais
                double dev;
                dev = values.at(i) - avg;

                deviations.push_back(dev);

                if(dev > max) {
                    max = dev;
                }

                if (dev < min) {
                    min = dev;
                }
            }
            //std::cout<<"-----------------Max ===: "+std::to_string(max)<<std::endl;
            //std::cout<<"-----------------Min ===: "+std::to_string(min)<<std::endl;

            //std::cout<<"-----------------Ther ===: "+std::to_string(values.at(0))<<std::endl;
            //std::cout<<"-----------------Ecg ===: "+std::to_string(values.at(1))<<std::endl;
            //std::cout<<"-----------------Oximeter ===: "+std::to_string(values.at(2))<<std::endl;
            //std::cout<<"-----------------Abps ===: "+std::to_string(values.at(3))<<std::endl;
            //std::cout<<"-----------------Abpd===: "+std::to_string(values.at(4))<<std::endl;
            //std::cout<<"-----------------Glub ===: "+std::to_string(values.at(5))<<std::endl;
            
            double weighted_average = 0.0;
            double weight_sum = 0.0;

            //fprintf(fp, "Max: %f\t",max);
            //fprintf(fp, "Min: %f\t",min);

            // Status de risco do paciente dado em porcentagem
            if(max - min > 0.0) {
                //Se o máximo e mínimo forem diferentes, normalizar desvios e calcular média ponderada
                for(i = 0;i < deviations.size();i++) {
                    //Normalizando desvios entre 0 e 1
                    deviations.at(i) = (deviations.at(i) - min)/(max - min);

                    //fprintf(fp, "Dev_%d: %f\t",i,deviations.at(i));
                    //fprintf(fp, "Risk_%d: %f\t",i,values.at(i));

                    weight_sum += deviations.at(i);
                    weighted_average += values.at(i)*deviations.at(i);
                }

                risk_status = weighted_average/weight_sum;
            } else {
                for(i = 0;i < deviations.size();i++) {
                   // fprintf(fp, "Dev_%d: %f\t",i,deviations.at(i));
                    //fprintf(fp, "Risk_%d: %f\t",i,values.at(i));
                }
                //Se o máximo é igual ao mínimo, a média será calculada e dará o mesmo valor
                risk_status = avg;
            }

            //fprintf(fp, "Risk_Status: %f\n",risk_status);
            

            // 85.0 é um número totalmente ARBITRARIO
            if(risk_status > 66.0){
                cout << "============ EMERGENCY ============(" << risk_status << '%' << ")" << endl;
            }
            else{
                cout << "General risk status: " << risk_status << '%' << endl;
            }
            //fclose(fp);
            return risk_status;
        }
    }
}
