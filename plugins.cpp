// Copyright (c) 2023 - The University of Texas at Austin
//  This work was produced under contract #2317831 to National Technology and
//  Engineering Solutions of Sandia, LLC which is under contract
//  No. DE-NA0003525 with the U.S. Department of Energy.
//  plugins.cpp
#include <dlfcn.h>
#include <iostream>
#include "plugins.hpp"

_create_soma* create_soma;
_destroy_soma* destroy_soma;

void init_soma(){
    // load the soma library
    void* soma = dlopen("./plugins/test.so", RTLD_LAZY);
    if (!soma) {
        std::cerr << "Cannot load library: " << dlerror() << '\n';
        return;
    }

    // reset errors
    dlerror();
    
    // Function to create an instance of the Soma class
    create_soma = (_create_soma*) dlsym(soma, "create");
    const char* dlsym_error = dlerror();
    if (dlsym_error) {
        std::cerr << "Cannot load symbol create: " << dlsym_error << '\n';
        return;
    }
    
    // Function to destroy an instance of the Soma class
    destroy_soma = (_destroy_soma*) dlsym(soma, "destroy");
    dlsym_error = dlerror();
    if (dlsym_error) {
        std::cerr << "Cannot load symbol destroy: " << dlsym_error << '\n';
        return;
    }
}
