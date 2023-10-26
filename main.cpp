// Copyright (c) 2023 - The University of Texas at Austin
//  This work was produced under contract #2317831 to National Technology and
//  Engineering Solutions of Sandia, LLC which is under contract
//  No. DE-NA0003525 with the U.S. Department of Energy.
// main.c - Command line interface
// Performance simulation of neuromorphic architectures
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
// #include <pybind11/pybind11.h>

#include "print.hpp"
#include "sim.hpp"
#include "network.hpp"
#include "arch.hpp"
#include "description.hpp"
#include "command.hpp"

void run(struct simulation *sim, struct network *net, struct architecture *arch);
struct timespec calculate_elapsed_time(struct timespec ts_start, struct timespec ts_end);

enum program_args
{
	ARCH_FILENAME,
	NETWORK_FILENAME,
	TIMESTEPS,
	PROGRAM_NARGS,
};

int main(int argc, char *argv[])
{
	FILE *input_fp, *network_fp, *arch_fp;
	struct simulation sim;
	struct network net;
	struct architecture *arch;
	char *filename, *input_buffer;
	double average_power;
	int timesteps, ret;

	filename = NULL;
	input_fp = NULL;
	input_buffer = NULL;
	// Assume that if we don't get to the point where we write this with
	//  a valid value, something went wrong and we errored out
	ret = RET_FAIL;
	arch = arch_init();
	network_init(&net);
	sim_init_sim(&sim);

	INFO("Initializing simulation.\n");
	if (argc < 1)
	{
		INFO("Error: No program arguments.\n");
		goto clean_up;
	}
	// First arg is always program name, skip
	argc--;
	argv++;

	// Parse optional args
	while (argc > 2)
	{
		if (argv[0][0] == '-')
		{
			switch (argv[0][1])
			{
			case 'i':
				filename = argv[1];
				argv++;
				argc--;
				break;
			case 'p':
				sim.log_perf = 1;
				break;
			case 's':
				sim.log_spikes = 1;
				break;
			case 'v':
				sim.log_potential = 1;
				break;
			case 'm':
				sim.log_messages = 1;
				break;
			default:
				INFO("Error: Flag %c not recognized.\n",
								argv[0][1]);
				break;
			}
			argc--;
			argv++;
		}
		else
		{
			break;
		}
	}

	if (filename)
	{
		input_fp = fopen(filename, "r");
		if (input_fp == NULL)
		{
			INFO("Error: Couldn't open inputs %s.\n", filename);
			goto clean_up;
		}
	}

	if (argc < PROGRAM_NARGS)
	{
		INFO("Usage: ./sim [-p<log perf> -s<spike trace> "
				"-v<potential trace> -i <input vectors>] "
				"<arch description> <network description> "
							"<timesteps>\n");
		goto clean_up;
	}

	if (sim.log_potential)
	{
		sim.potential_trace_fp = fopen("potential.trace", "w");
		if (sim.potential_trace_fp == NULL)
		{
			INFO("Error: Couldn't open trace file for writing.\n");
			goto clean_up;
		}
	}
	if (sim.log_spikes)
	{
		sim.spike_trace_fp = fopen("spikes.trace", "w");
		if (sim.spike_trace_fp == NULL)
		{
			INFO("Error: Couldn't open trace file for writing.\n");
			goto clean_up;
		}
	}
	if (sim.log_messages)
	{
		sim.message_trace_fp = fopen("messages.trace", "w");
		if (sim.message_trace_fp == NULL)
		{
			INFO("Error: Couldn't open trace file for writing.\n");
			goto clean_up;
		}

	}
	if (sim.log_perf)
	{
		sim.perf_fp = fopen("perf.csv", "w");
		if (sim.perf_fp == NULL)
		{
			INFO("Error: Couldn't open perf file for writing.\n");
			goto clean_up;
		}
	}

	// Read in program args, sanity check and parse inputs
	filename = argv[ARCH_FILENAME];
	arch_fp = fopen(filename, "r");
	if (arch_fp == NULL)
	{
		INFO("Error: Architecture file %s failed to open.\n", filename);
		goto clean_up;
	}
	ret = description_parse_file(arch_fp, NULL, arch);
	//arch_print_description(&description, 0);
	fclose(arch_fp);
	if (ret == RET_FAIL)
	{
		goto clean_up;
	}

	timesteps = 0;
	ret = sscanf(argv[TIMESTEPS], "%d", &timesteps);
	if (ret < 1)
	{
		INFO("Error: Time-steps must be integer > 0 (%s).\n",
							argv[TIMESTEPS]);
		goto clean_up;
	}
	else if (timesteps <= 0)
	{
		INFO("Error: Time-steps must be > 0 (%d)\n", timesteps);
		goto clean_up;
	}

	filename = argv[NETWORK_FILENAME];
	// Create the network
	network_fp = fopen(filename, "r");
	if (network_fp == NULL)
	{
		INFO("Network data (%s) failed to open.\n", filename);
		goto clean_up;
	}
	INFO("Reading network from file.\n");
	ret = description_parse_file(network_fp, &net, arch);
	fclose(network_fp);
	if (ret == RET_FAIL)
	{
		goto clean_up;
	}
	network_check_mapped(&net);

	arch_create_connection_maps(arch);
	INFO("Creating probe and perf data files.\n");
	if (sim.spike_trace_fp != NULL)
	{
		sim_spike_trace_write_header(&sim);
	}
	if (sim.potential_trace_fp != NULL)
	{
		sim_potential_trace_write_header(&sim, &net);
	}
	if (sim.message_trace_fp != NULL)
	{
		sim_message_trace_write_header(&sim);
	}
	if (sim.perf_fp != NULL)
	{
		sim_perf_write_header(sim.perf_fp);
	}
	// Step simulation
	INFO("Running simulation.\n");
	for (int i = 0; i < timesteps; i++)
	{
		if ((i+1) % 100 == 0)
		{
			// Print heart-beat every hundred timesteps
			INFO("*** Time-step %d ***\n", i+1);
		}
		run(&sim, &net, arch);
	}

	INFO("***** Run Summary *****\n");
	sim_write_summary(stdout, &sim);
	if (sim.total_sim_time > 0.0)
	{
		average_power = sim.total_energy / sim.total_sim_time;
	}
	else
	{
		average_power = 0.0;
	}
	INFO("Average power consumption: %f W.\n", average_power);
	sim.stats_fp = fopen("run_summary.yaml", "w");
	if (sim.stats_fp != NULL)
	{
		sim_write_summary(sim.stats_fp, &sim);
	}
	INFO("Run finished.\n");

clean_up:
	// Free any larger structures here
	network_free(&net);
	arch_free(arch);
	// Free any locally allocated memory here
	free(input_buffer);
	// Close any open files here
	if (sim.potential_trace_fp != NULL)
	{
		fclose(sim.potential_trace_fp);
	}
	if (sim.spike_trace_fp != NULL)
	{
		fclose(sim.spike_trace_fp);
	}
	if (sim.message_trace_fp != NULL)
	{
		fclose(sim.message_trace_fp);
	}
	if (sim.perf_fp != NULL)
	{
		fclose(sim.perf_fp);
	}
	if (sim.stats_fp != NULL)
	{
		fclose(sim.stats_fp);
	}

	if (ret == RET_FAIL)
	{
		return 1;
	}
	else
	{
		return 0;
	}
}

void run(struct simulation *sim, struct network *net, struct architecture *arch)
{
	// Run neuromorphic hardware simulation for one timestep
	//  Measure the CPU time it takes and accumulate the stats
	struct timespec ts_start, ts_end, ts_elapsed;

	// Measure the wall-clock time taken to run the simulation
	//  on the host machine
	clock_gettime(CLOCK_MONOTONIC, &ts_start);
	sim_timestep(sim, net, arch);
	// Calculate elapsed time
	clock_gettime(CLOCK_MONOTONIC, &ts_end);
	ts_elapsed = calculate_elapsed_time(ts_start, ts_end);
	sim->wall_time += (double) ts_elapsed.tv_sec+(ts_elapsed.tv_nsec/1.0e9);
	TRACE1("Time-step took: %fs.\n",
		(double) ts_elapsed.tv_sec+(ts_elapsed.tv_nsec/1.0e9));
}

struct timespec calculate_elapsed_time(struct timespec ts_start,
							struct timespec ts_end)
{
	// Calculate elapsed wall-clock time between ts_start and ts_end
	struct timespec ts_elapsed;

	ts_elapsed.tv_nsec = ts_end.tv_nsec - ts_start.tv_nsec;
	ts_elapsed.tv_sec = ts_end.tv_sec - ts_start.tv_sec;
	if (ts_end.tv_nsec < ts_start.tv_nsec)
	{
		ts_elapsed.tv_sec--;
		ts_elapsed.tv_nsec += 1000000000UL;
	}

	return ts_elapsed;
}

namespace py = pybind11;

void init_python(py::module &);

namespace simpy {

PYBIND11_MODULE(simcpp, m) {
    // Optional docstring
    m.doc() = "Python/C++ Interface";
    
    init_python(m);
}
}
