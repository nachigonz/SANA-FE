#include <string.h>
#include "../print.hpp"
#include "../plugins.hpp"
#include "../arch.hpp"
#include <iostream>
#include <math.h>

using namespace std;

class HH: public Base_Soma { // Hodgkin-Huxley model inspired by this paper: https://ieeexplore.ieee.org/document/9235538 and this textbook: https://mrgreene09.github.io/computational-neuroscience-textbook

    // HH specific
    public:
        // system variables
        double C_m;
        double g_Na;
        double g_K;
        double g_L;
        double V_Na;
        double V_K;
        double V_L;
        double dt;

        // main parameters
        double V, prev_V;               // membrane potential
        double I;               // stimulation current per area 
        double m;               // m, n, h are coeff
        double n;
        double h;

        // internal results of various differential equations
        double alpha_m;
        double alpha_n;
        double alpha_h;
        double beta_m;
        double beta_n;
        double beta_h;

        double tau_m, tau_n, tau_h;
        double pm, pn, ph;

        double denominator, tau_V, Vinf;

        HH(){
            C_m = 10;         // effective capacitance per area of membrane; default is 1
            g_Na= 1200;       // conductance of sodium
            g_K = 360;        // conductance of potassium
            g_L = 3;      // conductance of leak channel
            V_Na = 50;      // reverse potential of sodium
            V_K = -77;       // reverse potential of potassium
            V_L = -54.387;     // reverse potential of leak channel
            dt = 0.1;
        }

        virtual void parameters(struct attributes* attr, const int attribute_count) {
            /*** Set attributes ***/
            for (int i = 0; i < attribute_count; i++)
            {
                struct attributes *a = &(attr[i]);
                int ret = 1;

                if (strncmp("m", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &m);
                }
                else if (strncmp("n", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &n);
                }
                else if (strncmp("h", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &h);
                }
                else if (strncmp("current", a->key, MAX_FIELD_LEN) == 0)
                {
                    ret = sscanf(a->value_str, "%lf", &I);
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
        	TRACE1("Updating potential, before:%f\n", V);

            alpha_n = (0.01*(V+55)) / (1-exp(-0.1*(V+55)));
            alpha_m = (0.1*(V+40)) / (1-exp(-0.1*(V+40)));
            alpha_h = 0.07*exp(-0.05*(V+65));

            beta_n = 0.125*exp(-0.01125*(V+55));
            beta_m = 4*exp(-0.05556*(V+65));
            beta_h = 1/(1 + exp(-0.1*(V+35)));

            tau_n = 1 / (alpha_n + beta_n);
            tau_m = 1 / (alpha_m + beta_m);
            tau_h = 1 / (alpha_h + beta_h);

            pm = alpha_m/(alpha_m + beta_m);
            pn = alpha_n/(alpha_n + beta_n);
            ph = alpha_h/(alpha_h + beta_h);

            denominator = g_L + g_K*(pow(n,4)) + g_Na*(pow(m,3)*h);
            tau_V = C_m/denominator;
            Vinf = ((g_L)*V_L + g_K*(pow(n,4))*V_K + g_Na*(pow(m,3))*h*V_Na + I)/denominator;

            // update main parameters
            prev_V = V;
            V = Vinf + (V - Vinf)*exp(-1*dt/tau_V);
            m = pm + (m - pm)*exp(-1*dt/tau_m);
            n = pn + (n - pn)*exp(-1*dt/tau_n);
            h = ph + (h - ph)*exp(-1*dt/tau_h);

        	// Check against threshold potential (for spiking)
        	if ((prev_V < 25) && (V > 25)) // if voltage just crossed the 25 mV boundary, then spike
        	{
                neuron_status = FIRED;
        	}
            else{
                neuron_status = UPDATED;
            }

            TRACE1("Updating potential, after:%f\n", V);

            return neuron_status;
        }
};

// the class factories

extern "C" Base_Soma* create_HH() {
    return new HH();
}

// Memory Leak?
extern "C" void destroy_HH(Base_Soma* HH) {
    delete HH;
}