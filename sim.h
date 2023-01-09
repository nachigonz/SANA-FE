// sim.h - Neuromorphic simulator kernel
//
// Time-step based simulation, based on loop:
// 1) seed any input spikes
// 2) route spikes
// 3) update neurons and check firing
#ifndef SIM_HEADER_INCLUDED_
#define SIM_HEADER_INCLUDED_

#define RAND_SEED 0xbeef // For srand()
#define MIN(x, y) (((x) < (y)) ? (x) : (y))

struct sim_stats
{
	int time_steps;
	long int total_spikes, total_packets_sent;
	double total_energy, total_sim_time, wall_time;
	double network_time;
};

struct timing
{
	struct core *c;
	int next;
};

enum status
{
	UPDATE_NEURON,
	SEND_SPIKES,
	NEURON_FINISHED,
};

#include "arch.h"
#include "network.h"
#include "stdio.h"
struct sim_stats sim_timestep(struct network *const net, struct architecture *const arch, FILE *probe_spike_fp, FILE *probe_potential_fp, FILE *perf_fp);

int sim_send_messages(struct architecture *arch, struct network *net);
//int sim_route_spikes(struct architecture *arch, struct network *net);
int sim_input_spikes(struct network *net);

void sim_process_neuron(struct network *net, struct neuron *n);
double sim_pipeline_receive(struct neuron *n, struct connection *connection_ptr);
void sim_update_synapse(struct neuron *n);
void sim_update_dendrite(struct neuron *n);
void sim_update_soma(struct neuron *n);
void sim_update_axon(struct neuron *n);

void sim_reset_measurements(struct network *net, struct architecture *arch);
double sim_calculate_energy(const struct architecture *const arch, const double time);
double sim_calculate_time(const struct architecture *const arch, double *network_time);
double sim_calculate_time_old(const struct architecture *const arch);
long int sim_calculate_packets(const struct architecture *arch);

void sim_write_summary(FILE *fp, const struct sim_stats *stats);
void sim_probe_write_header(FILE *spike_fp, FILE *potential_fp, const struct network *net);
void sim_probe_log_timestep(FILE *spike_fp, FILE *potential_fp, const struct network *net);
void sim_perf_write_header(FILE *perf_fp, const struct architecture *arch);
void sim_perf_log_timestep(FILE *fp, const struct architecture *arch, const struct network *net, const struct sim_stats *stats);
int sim_poisson_input(const double firing_probability);
int sim_rate_input(const double firing_rate, double *spike_val);

void sim_start_next_timestep(struct neuron *n);

struct core *sim_init_timing_priority(struct architecture *arch);
struct core *sim_update_timing_queue(struct architecture *arch,
						struct core *top_priority);
//void sim_push_timing_update(struct timing *priority);

#endif
