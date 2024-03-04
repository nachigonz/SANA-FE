// Copyright (c) 2023 - The University of Texas at Austin
//  This work was produced under contract #2317831 to National Technology and
//  Engineering Solutions of Sandia, LLC which is under contract
//  No. DE-NA0003525 with the U.S. Department of Energy.
// module.cpp - Pybind module interface
// Performance simulation of neuromorphic architectures
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "print.hpp"
#include "sim.hpp"
#include "network.hpp"
#include "arch.hpp"
#include "description.hpp"
#include "command.hpp"
#include "main.hpp"
#include "pybind11/pybind11.h"

namespace py = pybind11;

class SANA_FE{
	public:
		struct simulation *sim;
		struct network net;
		struct architecture *arch;
		double average_power;
		int timesteps;
		FILE *input_fp;

		SANA_FE(){
			init();
		}
		void init(){
			arch = arch_init();
			network_init(&net);
			INFO("Initializing simulation.\n");
			sim = sim_init_sim();
		}
		int force_spike(int group_id, int n_id, int num_spikes){
			if (num_spikes < 0)
				return -1;
			if (group_id >= net.neuron_group_count)
				return -1;
			if (n_id >= net.groups[group_id].neuron_count)
				return -1;
			net.groups[group_id].neurons[n_id].forced_spikes = num_spikes;
			return num_spikes;
		}
		void run_timesteps(int timesteps = 1){
			for (int i = 0; i < timesteps; ++i){
				run(sim, &net, arch);
			}
		}
		void set_input(char *filename){
			input_fp = fopen(filename, "r");
			if (input_fp == NULL)
			{
				INFO("Error: Couldn't open inputs %s.\n", filename);
				clean_up(RET_FAIL);
			}
		}
		void set_perf_flag(bool flag = true){
			if (flag){
				sim->log_perf = 1;

				sim->perf_fp = fopen("perf.csv", "w");
				if (sim->perf_fp == NULL)
				{
					INFO("Error: Couldn't open perf file for writing.\n");
					clean_up(RET_FAIL);
				}
				sim_perf_write_header(sim->perf_fp);
			}
			else{
				sim->log_perf = 0;
				if (sim->perf_fp != NULL)
					fclose(sim->perf_fp);
			}
		}
		void set_spike_flag(bool flag = true){
			if (flag){
				sim->log_spikes = 1;

				sim->spike_trace_fp = fopen("spikes.trace", "w");
				if (sim->spike_trace_fp == NULL)
				{
					INFO("Error: Couldn't open trace file for writing.\n");
					clean_up(RET_FAIL);
				}
				sim_spike_trace_write_header(sim);
			}
			else{
				sim->log_spikes = 0;
				if (sim->spike_trace_fp != NULL)
					fclose(sim->spike_trace_fp);
			}
		}
		void set_pot_flag(bool flag = true){
			if (flag){
				sim->log_potential = 1;

				sim->potential_trace_fp = fopen("potential.trace", "w");
				if (sim->potential_trace_fp == NULL)
				{
					INFO("Error: Couldn't open trace file for writing.\n");
					clean_up(RET_FAIL);
				}
				sim_potential_trace_write_header(sim, &net);
			}
			else{
				sim->log_potential = 0;
				if (sim->potential_trace_fp != NULL)
					fclose(sim->potential_trace_fp);
			}
		}
		void set_mess_flag(bool flag = true){
			if (flag){
				sim->log_messages = 1;

				sim->message_trace_fp = fopen("messages.trace", "w");
				if (sim->message_trace_fp == NULL)
				{
					INFO("Error: Couldn't open trace file for writing.\n");
					clean_up(RET_FAIL);
				}
				sim_message_trace_write_header(sim);
			}
			else{
				sim->log_messages = 0;
				if (sim->message_trace_fp != NULL)
					fclose(sim->message_trace_fp);
			}
		}
		void set_arch(char* filename){
			FILE* arch_fp = fopen(filename, "r");
			if (arch_fp == NULL)
			{
				INFO("Error: Architecture file %s failed to open.\n", filename);
				clean_up(RET_FAIL);
			}
			int ret = description_parse_file(arch_fp, NULL, arch);
			//arch_print_description(&description, 0);
			fclose(arch_fp);
			if (ret == RET_FAIL)
			{
				clean_up(RET_FAIL);
			}
			arch_create_connection_maps(arch);
		}
		void set_net(char* filename){
			FILE* network_fp = fopen(filename, "r");
			if (network_fp == NULL)
			{
				INFO("Network data (%s) failed to open.\n", filename);
				clean_up(RET_FAIL);
			}
			INFO("Reading network from file.\n");
			int ret = description_parse_file(network_fp, &net, arch);
			fclose(network_fp);
			if (ret == RET_FAIL)
			{
				clean_up(RET_FAIL);
			}
			network_check_mapped(&net);

			// Change Potential logging with new headers from net.
			if (sim->log_potential){
				set_pot_flag(true);
			}
		}

		void clean_up(description_ret ret = RET_OK){
			// Free any larger structures here
			network_free(&net);
			arch_free(arch);

			// Close any open files here
			if (sim->potential_trace_fp != NULL)
			{
				fclose(sim->potential_trace_fp);
			}
			if (sim->spike_trace_fp != NULL)
			{
				fclose(sim->spike_trace_fp);
			}
			if (sim->message_trace_fp != NULL)
			{
				fclose(sim->message_trace_fp);
			}
			if (sim->perf_fp != NULL)
			{
				fclose(sim->perf_fp);
			}
			if (sim->stats_fp != NULL)
			{
				fclose(sim->stats_fp);
			}

			// Free the simulation structure only after we close all files
			free(sim);

			if (ret == RET_FAIL)
			{
				exit(1);
			}
			else
			{
				exit(0);
			}
		}
};

void test_pybind(void){
	INFO("Printing through Pybind!\n");
}

PYBIND11_MODULE(simcpp, m) {
    m.doc() = R"pbdoc(
        SANA-FE Cpp Module with Pybind11 
        --------------------------------

        .. currentmodule:: simcpp

        .. autosummary::
           :toctree: _generate

           test_pybind
		   SANA_FE
    )pbdoc";

    m.def("test_pybind", &test_pybind, R"pbdoc(
        test_pybind function from main.cpp

        Test pybind11 functionality.
    )pbdoc");

	py::class_<SANA_FE>(m, "SANA_FE")
		.def(py::init())
		.def("init", &SANA_FE::init)
        .def("force_spike", &SANA_FE::force_spike)
        .def("run_timesteps", &SANA_FE::run_timesteps)
		.def("set_input", &SANA_FE::set_input)
		.def("set_perf_flag", &SANA_FE::set_perf_flag)
		.def("set_spike_flag", &SANA_FE::set_spike_flag)
		.def("set_pot_flag", &SANA_FE::set_pot_flag)
		.def("set_mess_flag", &SANA_FE::set_mess_flag)
		.def("set_arch", &SANA_FE::set_arch)
		.def("set_net", &SANA_FE::set_net)
		.def("clean_up", &SANA_FE::clean_up);
}
