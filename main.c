// main.c
// Performance simulation for neuromorphic architectures
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sim.h"
#include "tech.h"
#include "network.h"

void init_results(struct sim_results *results);
void next_inputs(char *buffer, struct core *cores, const int max_cores, struct neuron **neuron_ptrs);

enum program_args
{
	TECHNOLOGY_FILENAME,
	TIMESTEPS,
	N_CORES,
	NETWORK_FILENAME,
	PROGRAM_NARGS,
};

int main(int argc, char *argv[])
{
	FILE *input_fp, *network_fp, *results_fp, *tech_fp;
	struct technology tech;
	struct core *cores;
	struct neuron **neuron_ptrs;
	struct sim_results results;
	char *filename, *input_buffer;
	int timesteps, max_cores, max_neurons, max_input_line;

	filename = NULL;
	input_fp = NULL;
	network_fp = NULL;
	results_fp = NULL;
	input_buffer = NULL;

	if (argc < 1)
	{
		INFO("Error: No program arguments.\n");
		exit(1);
	}
	// First arg is always program name, skip
	argc--;
	argv++;

	// Parse optional args
	if (argc > 2)
	{
		if ((argv[0][0] == '-') && (argv[0][1] == 'i'))
		{
			// Optional input vector argument
			filename = argv[1];
			argc--;
			argv += 2;
		}
	}

	if (filename)
	{
		input_fp = fopen(filename, "r");
		if (input_fp == NULL)
		{
			INFO("Error: Couldn't open inputs %s.\n", filename);
			exit(1);
		}
	}

	if (argc < PROGRAM_NARGS)
	{
		INFO("Usage: ./sim [-i <input vectors>] <tech file> <timesteps>"
						"<cores> <neuron config>\n");
		exit(1);
	}

	// Initialize the technology parameters - the chip parameters and key
	//  metrics
	// TODO: now we have fully parameterized technology variables, N_CORES
	//  is redundant - we can just set this correctly in the file
	tech_init(&tech);

	// Read in program args, sanity check and parse inputs
	filename = argv[TECHNOLOGY_FILENAME];
	tech_fp = fopen(filename, "r");
	if (tech_fp == NULL)
	{
		INFO("Error: Tech file failed to open.\n");
		exit(1);
	}
	tech_read_file(&tech, tech_fp);

	sscanf(argv[TIMESTEPS], "%d", &timesteps);
	if (timesteps <= 0)
	{
		INFO("Time-steps must be > 0 (%d)\n", timesteps);
		exit(1);
	}

		sscanf(argv[N_CORES], "%d", &max_cores);
	if ((max_cores <= 0) || (max_cores > tech.max_cores))
	{
		INFO("Cores must be > 0 and < %d (%d)\n", tech.max_cores,
								max_cores);
		exit(1);
	}

	max_neurons = max_cores * tech.max_compartments;
	// Input line must be long enough to encode inputs for all neurons
	//  simultaneously
	max_input_line = 32 + (max_neurons*32);

	filename = argv[NETWORK_FILENAME];
	// Create the network
	network_fp = fopen(filename, "r");
	if (network_fp == NULL)
	{
		INFO("Neuron data (%s) failed to open.\n", filename);
		exit(1);
	}

	INFO("Allocating memory for %d cores.\n", max_cores);
	cores = (struct core *) malloc(max_cores * sizeof(struct core));
	for (int i = 0; i < max_cores; i++)
	{
		struct core *c = &(cores[i]);
		// Allocate each core, creating memory for the compartments i.e.
		//  neurons, and all the synaptic data. Since the parameters are
		//  defined at runtime, this must be done dynamically
		c->neurons = (struct neuron *) malloc(tech.max_compartments *
							sizeof(struct neuron));
		if (c->neurons == NULL)
		{
			INFO("Error: failed to allocate neuron.\n");
			exit(1);
		}

		c->synapses = (struct synapse **) malloc(tech.max_compartments *
						sizeof(struct synapse *));
		if (c->synapses == NULL)
		{
			INFO("Error: failed to allocate synapse ptr.\n");
			exit(1);
		}
		// For each compartment, allocate a certain amount of synaptic
		//  memory
		// TODO: this isn't really how it works in the wild. What would
		//  be better is to allocate a single block of synaptic memory
		//  per core. Then each neuron compartment has an index into
		//  its memory within the block. This defines way too much
		//  synaptic memory (GB) when it should be MB.
		for (int j = 0; j < tech.max_compartments; j++)
		{
			c->synapses[j] =
				(struct synapse *) malloc(tech.fan_out *
							sizeof(struct synapse));
			if (c->synapses[j] == NULL)
			{
				INFO("Error: failed to allocate synapse.\n");
			}
		}
	}

	INFO("Allocating memory to track %d neurons.\n", max_neurons);
	neuron_ptrs = (struct neuron **)
				malloc(max_neurons * sizeof(struct neuron *));
	if ((neuron_ptrs == NULL) || (cores == NULL))
	{
		INFO("Error: failed to allocate memory.\n");
		exit(1);
	}
	//INFO("Allocated %ld bytes\n", max_cores * sizeof(struct core));
        for (int i = 0; i < max_neurons; i++)
        {
            neuron_ptrs[i] = NULL;
        }
	network_read_csv(network_fp, neuron_ptrs, cores, max_cores, &tech);
	fclose(network_fp);

	// TODO: eventually we could have some simple commands like
	//  run <n timesteps>
	//  set rate[neuron #] <firing rate>
	//  set threshold[neuron #] <threshold>
	//  That can either be input from the command line or a file
	//  This could replace having a separate input vector file format
	//  It would also be more general / powerful
	init_results(&results);
	if (input_fp != NULL)
	{
		// Allocate a buffer for the inputs
		input_buffer = (char *) malloc(sizeof(char) * max_input_line);
		if (input_buffer == NULL)
		{
			INFO("Error: Couldn't allocate memory for inputs.\n");
			exit(1);
		}
		// Run set of input vectors, each one is presented for the
		//  same number of timesteps
		while (fgets(input_buffer, max_input_line, input_fp))
		{
			next_inputs(input_buffer, cores, max_cores,
								neuron_ptrs);
			INFO("Next inputs set.\n");
			sim_run(timesteps, &tech, cores, max_cores, &results);
		}
	}
	else
	{
		// Single step simulation, based on initial state of network
		sim_run(timesteps, &tech, cores, max_cores, &results);
	}

	INFO("Total simulated time: %es.\n", results.total_sim_time);
	INFO("Total energy calculated: %eJ.\n", results.total_energy);
	INFO("Average power consumption: %fW.\n",
				results.total_energy / results.total_sim_time);
	INFO("Run finished.\n");

	results_fp = fopen("results.yaml", "w");
	if (results_fp != NULL)
	{
		sim_write_results(results_fp, &results);
	}
	fclose(results_fp);

	// Cleanup
        for (int i = 0; i < max_cores; i++)
	{
		struct core *c = &(cores[i]);

		free(c->neurons);
		for (int j = 0; j < tech.max_compartments; j++)
		{
			free(c->synapses[j]);
		}
		free(c->synapses);
	}
	free(cores);
	free(neuron_ptrs);
	free(input_buffer);

	return 0;
}

void next_inputs(char *buffer, struct core *cores, const int max_cores,
						struct neuron **neuron_ptrs)
{
	char *token;
	double firing_rate;
	int neuron_count;

	neuron_count = 0;
	token = strtok(buffer, ",");
	while (token != NULL)
	{
		// This time read all the fields in the line, we're
		//  interested in the synapse data
		int ret = sscanf(token, "%lf", &firing_rate);
		if (ret <= 0)
		{
			INFO("Error: invalid input format (%s)", buffer);
			exit(1);
		}
		if ((firing_rate < 0.0) || (firing_rate > 1.0))
		{
			INFO("Warning: input rate not in range [0,1] (%f)",
								firing_rate);
		}

		neuron_ptrs[neuron_count]->input_rate = firing_rate;
		token = strtok(NULL, ",");
		neuron_count++;
	}
}

void init_results(struct sim_results *results)
{
	results->total_energy = 0.0; // Joules
	results->total_sim_time = 0.0; // Seconds
	results->wall_time = 0.0; // Seconds
	results->time_steps = 0;
	results->total_spikes = 0;
}
