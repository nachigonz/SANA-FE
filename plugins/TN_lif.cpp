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

class TN_lif: public Base_Soma {

    // TN_LIF specific
    public:
        // system variables
        double V_j_t;
        double t;
        int p_i_j;
        int p_lambda_j;
        int p_T_j;
        int n_j;
        double omega;

        // user-defined variables;
        double eps_j;
        double lambda_j;
        double c_lambda_j;
        double alpha_j;
        double beta_j;
        int M_j;
        double R_j;
        double kappa_j;
        double gamma_j;
        double p_seed_j;

        TN_lif(){
            p_i_j = rand() % 10;
            p_lambda_j = rand() % 10;
            p_T_j = rand() % 10;
        }

        virtual void parameters(struct attributes* attr, const int attribute_count) {
            /*** Set attributes ***/
            for (int i = 0; i < attribute_count; i++)
            {
                struct attributes *a = &(attr[i]);
                int ret = 1;

                if (strncmp("eps_j", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &eps_j);
                }
                else if (strncmp("lambda_j", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &lambda_j);
                }
                else if (strncmp("c_lambda_j", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &c_lambda_j);
                }
                else if (strncmp("alpha_j", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &alpha_j);
                }
                else if (strncmp("beta_j", a->key, MAX_FIELD_LEN) ==
                    0)
                {
                    ret = sscanf(a->value_str, "%lf", &beta_j);
                }
                else if (strncmp("M_j", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &M_j);
                }
                else if (strncmp("R_j", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &R_j);
                }
                else if (strncmp("kappa_j", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &kappa_j);
                }
                else if (strncmp("gamma_j", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &gamma_j);
                }
                else if (strncmp("p_seed_j", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &p_seed_j);
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
        	TRACE1("Updating potential, before:%f\n", V_j_t);

            // synaptic integration
            V_j_t = V_j_t + input;

            // leak integration
            omega = (1- eps_j) + eps_j*sgn(V_j_t);
            V_j_t = V_j_t + omega*((1 - c_lambda_j)*lambda_j + c_lambda_j*F(lambda_j, p_lambda_j)*sgn(lambda_j));

            // threshold, fire, reset
            n_j = p_T_j & M_j;

            if (V_j_t < -1 * (beta_j*kappa_j + (beta_j + n_j)*(1 - kappa_j)))
            {
                neuron_status = UPDATED;
                V_j_t = -1*beta_j*kappa_j + (-1*delta(lambda_j)*R_j + delta(lambda_j - 1)*(V_j_t + (beta_j + n_j)) + delta(lambda_j - 2)*V_j_t)*(1 - kappa_j);
            }

        	// Check against threshold potential (for spiking)
        	if (V_j_t >= (alpha_j +  n_j))
        	{
                neuron_status = FIRED;
                V_j_t = delta(gamma_j)*R_j + delta(gamma_j - 1)*(V_j_t - (alpha_j + n_j)) + delta(gamma_j - 2) * V_j_t;
        	}

            TRACE1("Updating potential, after:%f\n", V_j_t);

            return neuron_status;
        }
};

// the class factories

extern "C" Base_Soma* create_TN_lif() {
    return new TN_lif();
}

// Memory Leak?
extern "C" void destroy_TN_lif(Base_Soma* TN_lif) {
    delete TN_lif;
}