"""First attempt at simulation run script.

Run a few basic experiments, show how we might interface a python
script with the simulator kernel.
"""

import matplotlib
matplotlib.use('Agg')

import csv
import subprocess
import yaml
from matplotlib import pyplot as plt
import pickle
import math
import sys
sys.path.insert(0, '/home/usr1/jboyle/neuro/spike-perf')
import spikeperf

MAX_TILES = 32
MAX_CORES = 4
MAX_COMPARTMENTS = 1024
NETWORK_FILENAME = "runs/connected_layers.net"
ARCH_FILENAME = "loihi.arch"


def run_sim(network, timesteps):
    network.save(NETWORK_FILENAME)
    run_command = ("./sim", ARCH_FILENAME, NETWORK_FILENAME,
               "{0}".format(timesteps))
    print("Command: {0}".format(" ".join(run_command)))
    subprocess.call(run_command)

    with open("stats.yaml", "r") as results_file:
       results = yaml.safe_load(results_file)

    return results


import random
def fully_connected(layer_neuron_count, spiking=True, force_update=False,
                    connection_probability=1.0):
    # Two layers, fully connected
    network = spikeperf.Network()
    loihi_compartments = spikeperf.loihi_init_compartments()

    if spiking:  # always spike
        threshold = -1.0
    else:  # never spike
        threshold = 2*layer_neuron_count

    reset = 0
    log_spikes = False
    log_voltage = False

    # Create layers
    layer_1 = spikeperf.create_layer(network, layer_neuron_count,
                                     loihi_compartments,
                                     log_spikes, log_voltage, force_update,
                                     threshold, reset)
    layer_2 = spikeperf.create_layer(network, layer_neuron_count, loihi_compartments,
                                     log_spikes, log_voltage, force_update,
                                     threshold, reset)

    # Create connections
    weight = 1.0
    for src in layer_1.neurons:
        for dest in layer_2.neurons:
            if random.random() < connection_probability:
                src.add_connection(dest, weight)  # Same weight for all connections

    return network


def connected_layers(weights, spiking=True):
    network = spikeperf.Network()
    loihi_compartments = spikeperf.loihi_init_compartments()

    layer_neuron_count = len(weights)
    if spiking:  # always spike
        threshold = -1.0
    else:  # never spike
        threshold = 2*layer_neuron_count

    reset = 0
    force_update = True
    log_spikes = False
    log_voltage = False

    layer_1 = spikeperf.create_layer(network, layer_neuron_count,
                                     loihi_compartments, log_spikes,
                                     log_voltage, force_update, threshold,
                                     reset)
    layer_2 = spikeperf.create_layer(network, layer_neuron_count,
                                     loihi_compartments, log_spikes,
                                     log_voltage, force_update, threshold,
                                     reset)

    for src in layer_1.neurons:
        for dest in layer_2.neurons:
            # Take the ID of the neuron in the 2nd layer
            weight = float(weights[src.id][dest.id]) / 255
            if weight != 0:
                # Zero weights are pruned i.e. removed
                src.add_connection(dest, weight)

    print(network)
    return network


if __name__ == "__main__":
    #core_count = [1, 2, 4, 8, 16, 32, 64, 128]
    times = {0: [], 256: [], 512: [], 768: [], 1024: []}
    energy = {0: [], 256: [], 512: [], 768: [], 1024: []}
    """
    for cores in core_count:
        for compartments in range(0, MAX_COMPARTMENTS+1, 256):
            n = compartments * cores
            network = empty(n, compartments)
            results = run_sim(network, cores)

            times[compartments].append(results["time"])
            energy[compartments].append(results["energy"])

    plt.rcParams.update({'font.size': 14})
    plt.figure(figsize=(5.5, 5.5))
    for compartments in range(0, MAX_COMPARTMENTS+1, 256):
        plt.plot(core_count, times[compartments], "-o")
    plt.ylabel("Time (s)")
    plt.xlabel("Cores Used")
    plt.legend(("0", "256", "512", "768", "1024"))
    plt.ticklabel_format(style="sci", axis="y", scilimits=(0,0))
    plt.savefig("empty_times.png")

    plt.figure(figsize=(5.5, 5.5))
    for compartments in range(0, MAX_COMPARTMENTS+1, 256):
        plt.plot(core_count, energy[compartments], "-o")
    plt.ylabel("Energy (J)")
    plt.xlabel("Cores Used")
    plt.legend(("0", "256", "512", "768", "1024"))
    plt.ticklabel_format(style="sci", axis="y", scilimits=(0,0))
    plt.savefig("empty_energy.png")
    """
    # This experiment looks at two fully connected layers, spiking

    with open("sandia_data/weights.pkl", "rb") as weights_file:
        weights = pickle.load(weights_file)

    neuron_counts = []
    spiking_times = []
    spiking_energy = []

    #for i in range(1, 4):
    timesteps = 2
    for i in range(1, 31):
        layer_neurons = i*i

        #network = fully_connected(layer_neurons, spiking=True, probability=connection_probabilities[i-1])
        commands = connected_layers(weights[i-1], spiking=True)
        print("Testing network with {0} neurons".format(2*layer_neurons))
        results = run_sim(commands, timesteps)

        neuron_counts.append(layer_neurons*2)
        spiking_times.append(results["time"])
        spiking_energy.append(results["energy"])

    # Write all the simulation data to csv
    with open("runs/sim_spiking.csv", "w") as spiking_csv:
        spiking_writer = csv.DictWriter(spiking_csv,
                                        ("neuron_counts", "energy", "time"))
        spiking_writer.writeheader()
        for count, time, energy_val in zip(neuron_counts, spiking_times,
                                                  spiking_energy):
            spiking_writer.writerow({"neuron_counts": count,
                                     "energy": energy_val,
                                     "time": time})

    neuron_counts = []
    nonspiking_times = []
    nonspiking_energy = []

    # The second experiment looks at two fully connected layers, not spiking
    for i in range(1, 31):
        layer_neurons = i*i

        commands = fully_connected(layer_neurons, spiking=False,
                                   force_update=True)
        print("Testing network with {0} neurons".format(layer_neurons*2))
        results = run_sim(commands, timesteps)

        neuron_counts.append(layer_neurons*2)
        nonspiking_times.append(results["time"] / timesteps)
        nonspiking_energy.append(results["energy"] / timesteps)

    with open("runs/sim_nonspiking.csv", "w") as nonspiking_csv:
        nonspiking_writer = csv.DictWriter(nonspiking_csv,
                                           ("neurons", "energy", "time"))
        nonspiking_writer.writeheader()
        for neuron_count, time, energy_val in zip(neuron_counts, nonspiking_times,
                                                  nonspiking_energy):
            nonspiking_writer.writerow({"neurons": neuron_count,
                                        "energy": energy_val,
                                        "time": time})

    # **************************************************************************
    # Read Loihi measurement data from csv, this is only available to me locally
    #  since this is restricted data!
    neuron_counts = []
    loihi_times_spikes = []
    loihi_energy_spikes = []

    spiking_energy = []
    spiking_times = []
    with open("runs/sim_spiking.csv", "r") as spiking_csv:
        spiking_reader = csv.DictReader(spiking_csv)
        for row in spiking_reader:
            spiking_times.append(float(row["time"]))
            spiking_energy.append(float(row["energy"]))
            neuron_counts.append(int(row["neuron_counts"]))

    nonspiking_times = []
    nonspiking_energy = []
    with open("runs/sim_nonspiking.csv", "r") as nonspiking_csv:
        nonspiking_reader = csv.DictReader(nonspiking_csv)
        for row in nonspiking_reader:
            nonspiking_times.append(float(row["time"]))
            nonspiking_energy.append(float(row["energy"]))

    with open("sandia_data/loihi_spiking.csv", "r") as spiking_csv:
        spiking_reader = csv.DictReader(spiking_csv)
        for row in spiking_reader:
            loihi_times_spikes.append(float(row["time"]))
            loihi_energy_spikes.append(float(row["energy"]))

    loihi_times_no_spikes = []
    loihi_energy_no_spikes = []
    with open("sandia_data/loihi_nonspiking.csv", "r") as nonspiking_csv:
        nonspiking_reader = csv.DictReader(nonspiking_csv)
        for row in nonspiking_reader:
            loihi_times_no_spikes.append(float(row["time"]))
            loihi_energy_no_spikes.append(float(row["energy"]))

    plt.figure(figsize=(5.5, 5.5))
    plt.plot(neuron_counts, spiking_times, "-o")
    plt.plot(neuron_counts, loihi_times_spikes, "--x")
    plt.yscale("linear")
    plt.xscale("linear")
    plt.ylabel("Time (s)")
    plt.xlabel("Neurons")
    plt.legend(("Simulated", "Measured"))
    plt.ticklabel_format(style="sci", axis="y", scilimits=(0,0))
    plt.savefig("runs/connected_spiking_time.png")

    plt.figure(figsize=(5.5, 5.5))
    plt.plot(neuron_counts, spiking_energy, "-o")
    plt.plot(neuron_counts, loihi_energy_spikes, "--x", color="orange")
    plt.yscale("linear")
    plt.xscale("linear")
    plt.ylabel("Energy (J)")
    plt.xlabel("Neurons")
    plt.legend(("Simulated", "Measured"))
    #plt.ticklabel_format(style="sci", axis="y", scilimits=(0,0))
    plt.savefig("runs/connected_spiking_energy.png")

    plt.figure(figsize=(5.5, 5.5))
    plt.plot(neuron_counts, nonspiking_energy, "-o")
    plt.yscale("linear")
    plt.xscale("linear")
    plt.ylabel("Energy (J)")
    plt.xlabel("Neurons")
    plt.legend(("Simulated",))
    #plt.ticklabel_format(style="sci", axis="y", scilimits=(0,0))
    plt.savefig("runs/connected_spiking_energy_sim_only.png")

    plt.figure(figsize=(5.5, 5.5))
    plt.plot(neuron_counts, nonspiking_times, "-o")
    plt.plot(neuron_counts, loihi_times_no_spikes, "--x")
    plt.yscale("linear")
    plt.xscale("linear")
    plt.ylabel("Time (s)")
    plt.xlabel("Neurons")
    plt.legend(("Simulated", "Measured"))
    #plt.ticklabel_format(style="sci", axis="y", scilimits=(0,0))
    plt.savefig("runs/connected_not_spiking_time.png")

    plt.figure(figsize=(5.5, 5.5))
    plt.plot(neuron_counts, nonspiking_energy, "-o")
    plt.plot(neuron_counts, loihi_energy_no_spikes, "--x")
    plt.yscale("linear")
    plt.xscale("linear")
    plt.ylabel("Energy (J)")
    plt.xlabel("Neurons")
    plt.legend(("Simulated", "Measured"))
    #plt.ticklabel_format(style="sci", axis="y", scilimits=(0,0))
    plt.savefig("runs/connected_not_spiking_energy.png")

    # Some additional plots to highlight trends
    plt.figure(figsize=(5.5, 5.5))
    plt.plot(neuron_counts, loihi_times_spikes, "--x", color="orange")
    plt.ylabel("Time (s)")
    plt.xlabel("Neurons")
    plt.legend(("Measured",))
    #plt.ticklabel_format(style="sci", axis="y", scilimits=(0,0))
    plt.savefig("runs/connected_spiking_time_loihi_only.png")

    #plt.show()
