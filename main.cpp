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

#include "print.hpp"
#include "sim.hpp"
#include "network.hpp"
#include "arch.hpp"
#include "description.hpp"
#include "command.hpp"
#include "module.hpp"

int main(int argc, char *argv[])
{
	SANA_FE sana_fe;
	int timesteps, ret;

	// Assume that if we don't get to the point where we write this with
	//  a valid value, something went wrong and we errored out
	ret = RET_FAIL;

	if (argc < 1)
	{
		INFO("Error: No program arguments.\n");
		sana_fe.clean_up(RET_FAIL);
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
				sana_fe.set_input(argv[1]);
				argv++;
				argc--;
				break;
			case 'p':
				sana_fe.set_perf_flag();
				break;
			case 's':
				sana_fe.set_spike_flag();
				break;
			case 'v':
				sana_fe.set_pot_flag();
				break;
			case 'm':
				sana_fe.set_mess_flag();
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

	if (argc < PROGRAM_NARGS)
	{
		INFO("Usage: ./sim [-p<log perf> -s<spike trace> "
				"-v<potential trace> -i <input vectors>] "
				"<arch description> <network description> "
							"<timesteps>\n");
		sana_fe.clean_up(RET_FAIL);
	}

	// Read in program args, sanity check and parse inputs
	sana_fe.set_arch(argv[ARCH_FILENAME]);
	sana_fe.set_net(argv[NETWORK_FILENAME]);

	timesteps = 0;
	ret = sscanf(argv[TIMESTEPS], "%d", &timesteps);
	if (ret < 1)
	{
		INFO("Error: Time-steps must be integer > 0 (%s).\n",
							argv[TIMESTEPS]);
		sana_fe.clean_up(RET_FAIL);
	}
	else if (timesteps <= 0)
	{
		INFO("Error: Time-steps must be > 0 (%d)\n", timesteps);
		sana_fe.clean_up(RET_FAIL);
	}

	// Step simulation
	INFO("Running simulation.\n");
	for (long timestep = 1; timestep <= timesteps; timestep++)
	{
		if ((timestep % 100) == 0)
		{
			// Print heart-beat every hundred timesteps
			INFO("*** Time-step %ld ***\n", timestep);
		}
		sana_fe.run_timesteps();
	}

	INFO("***** Run Summary *****\n");
	sana_fe.sim_summary();
	double average_power = sana_fe.get_power();
	INFO("Average power consumption: %f W.\n", average_power);
	INFO("Run finished.\n");

	sana_fe.clean_up(RET_OK);
}
