#include <string.h>
#include "../print.hpp"
#include "../plugins.hpp"
#include "../description.hpp"
#include <iostream>

using namespace std;

class LIF: public Base_Soma {

    // output spike
    double spike;
    double s_j; // for debugging purposes only

    // system variables
    double V_j_t;
    double t;

    // user-defined variables;
    double lambda_j;
    double alpha_j;
    double R_j;

    int id, neuron_count, reset_mode, reverse_reset_mode;
	int default_log_potential, default_log_spikes;
	int default_max_connections_out, default_force_update;
	double default_threshold, default_reset;
	double default_reverse_threshold, default_reverse_reset;
	double default_leak_decay, default_leak_bias;

    public:


        LIF(){ 
            default_leak_decay = 0.0;
            default_leak_bias = 0.0;
            default_threshold = 0.0;
            default_reset = 0.0;
        }

        bool update_soma(double input){

            // synaptic & leak doubleegration
            V_j_t = (V_j_t * default_leak_decay) + input - default_leak_bias;

            // threshold, fire, reset
            if(V_j_t >= default_threshold){
                spike = 1;
                V_j_t = default_reset;
            }
            else{
                spike = 0;
            }

            // cout << spike << endl;
            return spike > 0;
        }

        void parameters(struct attributes* attr, const int attribute_count){
            int ret;
            for (int i = 0; i < attribute_count; i++)
            {
                struct attributes *a = &(attr[i]);

                ret = -1;
                if (strncmp("threshold", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(
                        a->value_str, "%lf", &default_threshold);
                }
                else if (strncmp("reverse_threshold", a->key, MAX_FIELD_LEN) ==
                    0)
                {
                    ret = sscanf(a->value_str, "%lf",
                        &default_reverse_threshold);
                }
                else if (strncmp("leak_decay", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf",
                        &default_leak_decay);
                }
                else if (strncmp("leak_bias", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(
                        a->value_str, "%lf", &default_leak_bias);
                }
                else if (strncmp("log_v", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%d",
                        &default_log_potential);
                }
                else if (strncmp("log_spikes", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(
                        a->value_str, "%d", &default_log_spikes);
                }
                else if (strncmp("connections_out", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%d",
                        &default_max_connections_out);
                }
                else if (strncmp("force_update", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%d",
                        &default_force_update);
                }
                else if (strncmp("reset", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(
                        a->value_str, "%lf", &default_reset);
                }
                else if (strncmp("reverse_reset", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf",
                        &default_reverse_reset);
                }

                if (ret < 1)
                {
                    INFO("Invalid attribute (%s:%s)\n", a->key,
                        a->value_str);
                    exit(1);
                }
            } 
        }

        // for debugging purproses only:

        void set_spike(double x){
            spike = x;
        }

        double get_spike(){
            return s_j*spike;
        }

        double get_potential(){
            return V_j_t;
        }

        void prdouble_stats(){
            cout << "Potential: " << V_j_t << "     Spike_weight: " << s_j << "     Lambda_j: " << lambda_j << "    Alpha_j: " << alpha_j << "      R_j: " << R_j;
        }
};

// the class factories

extern "C" Base_Soma* create_core_lif() {
    return new LIF;
}

extern "C" void destroy_core_lif(Base_Soma* lif) {
    delete lif;
}
