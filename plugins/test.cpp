#include "../plugins.hpp"
#include <iostream>


class Soma: public Base_Soma { // separate this from basic LIF; i.e. TN not equal to LIF

    // output spike
    int spike;

    // system variables
    int V_j_t;
    int t;
    int A_i_t;
    int p_i_j;
    int p_gamma_j;
    int p_T_j;
    int n_j;
    int omega;



    // user-defined variables;
    int w_i_j;
    int G_i;
    int s_j_G_i;
    int b_j_G_i;
    int eps_j;
    int gamma_j;
    int c_gamma_j;
    int alpha_j;
    int beta_j;
    int M_j;
    int R_j;
    int kappa_j;
    int ro_j;
    int p_seed_j;

    int sgn(int x){
        if(x < 0){
            return -1;
        }
        else if(x == 0){
            return 0;
        }
        return 1;
    }

    int F(int s, int p){
        if((s >= p) || ((-1*s) >= p)){
            return 1;
        }
        return 0;
    }

    int delta(int x){
        if(x == 0){
            return 1;
        }
        return 0;
    }

    public:

        Soma(){
            t=1;
        }

        double update_soma(double input){
            // synaptic integration

            std::cout << "Updating Soma " << t << std::endl;
            t++;
            return V_j_t;
        }

        void set_spike(int x){
            spike = x;
        }

        int get_spike(){
            return spike;
        }
};


// the class factories

extern "C" Base_Soma* create() {
    return new Soma;
}

extern "C" void destroy(Base_Soma* soma) {
    delete soma;
}