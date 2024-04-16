#include <string.h>
#include "../print.hpp"
#include "../plugins.hpp"
#include "../arch.hpp"
#include <iostream>
#include <math.h>

using namespace std;

double sgn(double x){
    if(x < 0){
        return -1;
    }
    else if(x == 0){
        return 0;
    }
    return 1;
}

double F(double s, double p){
    if((s >= p) || ((-1*s) >= p)){
        return 1;
    }
    return 0;
}

double delta(double x){
    if(x == 0){
        return 1;
    }
    return 0;
}

class TN_lif_original: public Base_Soma {

    // TN_LIF specific
    public:
        // system variables
        double potential, leak_bias, current_in, bias; // ask about current_in
        double threshold, reverse_threshold, reset, reverse_reset;
        char reset_mode[10];
        string reset_mode_str;
        unsigned int random_r;

        TN_lif_original(){
        }

        virtual void parameters(struct attributes* attr, const int attribute_count) {
            /*** Set attributes ***/
            for (int i = 0; i < attribute_count; i++)
            {
                struct attributes *a = &(attr[i]);
                int ret = 1;

                if (strncmp("leak_bias", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &leak_bias);
                }
                else if (strncmp("bias", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &bias);
                }
                else if (strncmp("threshold", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &threshold);
                }
                else if (strncmp("reverse_threshold", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &reverse_threshold);
                }
                else if (strncmp("reset", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &reset);
                }
                else if (strncmp("reverse_reset", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &reverse_reset);
                }
                else if (strncmp("reset_mode", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%s", reset_mode);
                    reset_mode_str = string(reset_mode);
                }
                if (ret < 1)
                {
                    INFO("Invalid attribute (%s:%s)\n", a->key, a->value_str);
                    exit(1);
                }
            }
        }

        Neuron_Status update_soma(double input){

            Neuron_Status neuron_status = IDLE;

        	// Calculate the change in potential since the last update e.g.
        	//  integate inputs and apply any potential leak
        	TRACE1("Updating potential, before:%f\n", potential);
            
            double v = 0.0;

            if(potential > 0.0){
                potential -= leak_bias;
            }
            else if(potential < 0.0){
                potential += leak_bias;
            }

            potential += input + bias; 
            
            random_r = rand() % 10;

            v  = potential + random_r;

            if(v >= threshold){
                if (reset_mode_str.compare("hard"))
                {
                    potential = reset;
                }
                else if (reset_mode_str.compare("soft"))
                {
                    potential -= threshold;
                }
                else if (reset_mode_str.compare("saturate"))
                {
                    potential = threshold;
                }

                neuron_status = FIRED;
            }
            else if(v <= reverse_threshold){
                if (reset_mode_str.compare("hard"))
                {
                    potential = reverse_reset;
                }
                else if (reset_mode_str.compare("soft"))
                {
                    potential += reverse_threshold;
                }
                else if (reset_mode_str.compare("saturate"))
                {
                    potential = reverse_threshold;
                }

                neuron_status = UPDATED;
            }


            TRACE1("Updating potential, after:%f\n", potential);

            return neuron_status;
        }
        
};

// the class factories

extern "C" Base_Soma* create_TN_lif_original() {
    return new TN_lif_original();
}

// Memory Leak?
extern "C" void destroy_TN_lif_original(Base_Soma* TN_lif_original) {
    delete TN_lif_original;
}