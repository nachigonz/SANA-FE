"""
Copyright (c) 2023 - The University of Texas at Austin
This work was produced under contract #2317831 to National Technology and
Engineering Solutions of Sandia, LLC which is under contract
No. DE-NA0003525 with the U.S. Department of Energy.

sim.py - Simulator script and utility functionality
"""
import subprocess
import os
import yaml

NETWORK_FILENAME = "runs/connected_layers.net"
ARCH_FILENAME = "loihi.arch"

### SNN utility functions ###

class Network:
    def __init__(self, external_inputs=0):
        self.external_inputs = external_inputs
        self.inputs = []
        self.groups = []
        self._max_tiles = None
        self._max_cores = None
        self._max_compartments = None

    def create_group(self, threshold, reset, leak, log_spikes=False,
                     log_potential=False, force_update=False):
        group_id = len(self.groups)
        group = NeuronGroup(group_id, threshold, reset, leak, log_spikes,
                            log_potential, force_update)
        self.groups.append(group)
        return group

    def create_input(self):
        input_id = len(self.inputs)
        input_node = Input(input_id)
        self.inputs.append(input_node)
        return input_node

    def save(self, filename):
        with open(filename, 'w') as network_file:
            if self.external_inputs > 0:
                network_file.write("x {0} rate\n".format(self.external_inputs))
            for group in self.groups:
                network_file.write(str(group))

            for group in self.groups:
                for neuron in group.neurons:
                    network_file.write(str(neuron))

            for input_node in self.inputs:
                network_file.write(str(input_node))


class NeuronGroup:
    def __init__(self, group_id, threshold, reset, leak, log_spikes=None,
                 log_potential=None, force_update=None):
        # TODO: support all features here
        self.id = group_id
        self.neurons = []
        self.threshold = threshold
        self.reset = reset
        self.reset_mode = None
        self.reverse_reset = None
        self.reverse_reset_mode = None
        self.reverse_threshold = None
        self.leak_decay = leak
        self.max_connections = 1024
        self.log_spikes = log_spikes
        self.log_potential = log_potential
        self.force_update = force_update

    def __str__(self):
        neuron_count = len(self.neurons)

        group_str = f"g {neuron_count}"
        if self.threshold is not None:
            group_str += f" threshold={self.threshold}"
        if self.reset is not None:
            group_str += f" reset={self.reset}"
        if self.reverse_threshold is not None:
            group_str += f" reverse_threshold={self.reverse_threshold}"
        if self.reverse_reset is not None:
            group_str += f" reverse_reset={self.reverse_reset}"
        if self.leak_decay is not None:
            group_str += f" leak_decay={self.leak_decay}"
        if self.reset_mode is not None:
            group_str += f" reset_mode={self.reset_mode}"
        if self.reverse_reset_mode is not None:
            group_str += f" reverse_reset_mode={self.reverse_reset_mode}"
        if self.log_spikes is not None:
            group_str += f" log_spikes={int(self.log_spikes)}"
        if self.log_potential is not None:
            group_str += f" log_v={int(self.log_potential)}"
        if self.force_update is not None:
            group_str += f" force_update={int(self.force_update)}"

        group_str += "\n"
        return group_str

    def create_neuron(self, log_spikes=None, log_potential=None,
                      force_update=None):
        neuron_id = len(self.neurons)
        neuron = Neuron(self, neuron_id, log_spikes=log_spikes,
                        log_potential=log_potential, force_update=force_update)
        self.neurons.append(neuron)
        return neuron


class Input:
    def __init__(self, input_id):
        self.id = input_id
        self.connections = []

    def add_connection(self, dest, weight):
        self.connections.append((dest, weight))

    def __str__(self):
        line = "< {0}".format(self.id)
        for connection in self.connections:
            dest_neuron, weight = connection
            line += " {0} {1} {2}".format(
                dest_neuron.group_id, dest_neuron.id, weight)
        line += '\n'
        return line

class Neuron:
    def __init__(self, group, neuron_id, log_spikes=None,
                 log_potential=None, force_update=None):
        self.group = group
        self.id = neuron_id
        self.log_spikes = log_spikes
        self.log_potential = log_potential
        self.force_update = force_update
        self.connections = []
        self.tile = None
        self.core = None
        self.bias = None

    def add_connection(self, dest, weight):
        self.connections.append((dest, weight))

    def add_bias(self, bias):
        self.bias = bias

    def __str__(self, map_neuron=True):
        self.leak = 1.0
        neuron_str = f"n {self.group.id}.{self.id}"
        if self.bias is not None:
            neuron_str += f" bias={self.bias}"
        if self.log_spikes is not None:
            self.log_spikes = int(self.log_spikes)
            neuron_str += f" log_spikes={int(self.log_spikes)}"
        if self.log_potential is not None:
            neuron_str += f" log_v={int(self.log_potential)}"
        if self.force_update is not None:
            neuron_str += f" force_update={int(self.force_update)}"
        if len(self.connections) > self.group.max_connections:
           neuron_str += f" connections_out={len(self.connections)}"
        neuron_str += "\n"

        for connection in self.connections:
            dest_neuron, weight = connection
            neuron_str += f"e {self.group.id}.{self.id}->"
            neuron_str += f"{dest_neuron.group.id}.{dest_neuron.id}"
            neuron_str += f" w={weight:.5e}\n"

        if map_neuron:
            neuron_str += "& {0}.{1}@{2}.{3}\n".format(self.group.id, self.id,
                                                    self.tile, self.core)
        return neuron_str


def init_compartments(max_tiles, max_cores, max_compartments):
    compartments = []
    for tile in range(0, max_tiles):
        c = []
        for core in range(0, max_cores):
            c.append(max_compartments)
        compartments.append(c)

    return compartments


def map_neuron_to_compartment(compartments):
    for tile, cores in enumerate(compartments):
        for core, _ in enumerate(cores):
            if compartments[tile][core] > 0:
                compartments[tile][core] -= 1
                return tile, core

    # No free compartments left
    return None, None


def create_layer(network, layer_neuron_count, compartments,
                 log_spikes, log_potential, force_update, threshold, reset,
                 leak, mappings=None):
    print("Creating layer with {0} neurons".format(layer_neuron_count))
    #print("Compartments free: {0}".format(compartments))
    layer_group = network.create_group(threshold, reset, leak, log_spikes,
                                       log_potential, force_update)

    if mappings is not None:
        #print("mappings: {0} len({1}) layer_neuron_count: {2}".format(
        #    mappings, len(mappings), layer_neuron_count))
        assert(len(mappings) == layer_neuron_count)

    for i in range(0, layer_neuron_count):
        if (i % 10000) == 0:
            print(f"Creating neuron {i}")
        neuron = layer_group.create_neuron()

        if mappings is not None:
            tile, core = mappings[i]
        else:
            tile, core = map_neuron_to_compartment(compartments)
        neuron.tile, neuron.core = tile, core

    return layer_group

### Architecture description parsing ###
def parse_file(input_filename, output_filename):
    with open(input_filename, "r") as arch_file:
        arch_dict = yaml.safe_load(arch_file)

    if "architecture" not in arch_dict:
        raise Exception("Error: no architecture defined")

    parse_arch(arch_dict["architecture"])
    arch_elements = _entry_list

    with open(output_filename, "w") as list_file:
        for line in arch_elements:
            list_file.write(line + '\n')
    return


def parse_arch(arch):
    global _tiles
    global _cores_in_tile
    global _entry_list

    _tiles = 0
    _cores_in_tile = []
    _entry_list = []

    arch_name = arch["name"]
    if "[" in arch_name:
        raise Exception("Error: multiple architectures not supported")

    if "tile" not in arch:
        raise Exception("Error: No tiles defined, must be at least one tile")

    tiles = arch["tile"]
    for tile in tiles:
        parse_tile(tile)

    create_noc(arch)
    return


def parse_tile(tile_dict):
    tile_name = tile_dict["name"]
    # Work out how many instances of this tile to create
    if "[" in tile_name:
        # Can use notation [min..max] to indicate range of elements
        range_min, range_max = parse_range(tile_name)
    else:
        range_min, range_max = 0, 0

    for instance in range(range_min, range_max+1):
        tile_name = tile_name.split("[")[0] + "[{0}]".format(instance)
        tile_id = create_tile(tile_dict)

        # Add any elements local to this h/w structure. They have access to any
        #  elements in the parent structures
        if "core" not in tile_dict:
            raise Exception("Error: No cores defined, "
                            "must be at least one core")
        cores = tile_dict["core"]
        for _, core_dict in enumerate(cores):
            parse_core(core_dict, tile_id)

    return

def parse_core(core_dict, tile_id):
    core_name = core_dict["name"]

    # Work out how many instances of this tile to create
    if "[" in core_name:
        # Can use notation [min..max] to indicate range of elements
        range_min, range_max = parse_range(core_name)
    else:
        range_min, range_max = 0, 0

    elements = ("axon_in", "synapse", "dendrite", "soma", "axon_out")
    for el in elements:
        if el not in core_dict:
            raise Exception("Error: {0} not defined in core {1}".format(
                el, core_name))

    for instance in range(range_min, range_max+1):
        core_name = core_name.split("[")[0] + "[{0}]".format(instance)
        core_id = create_core(tile_id, core_dict)
        create_axon_in(tile_id, core_id, core_dict["axon_in"][0])
        create_synapse(tile_id, core_id, core_dict["synapse"][0])
        create_dendrite(tile_id, core_id, core_dict["dendrite"][0])
        create_soma(tile_id, core_id, core_dict["soma"][0])
        create_axon_out(tile_id, core_id, core_dict["axon_out"][0])


def parse_range(range_str):
    range_str = range_str.replace("]", "")
    range_str = range_str.split("[")[1]
    range_min = int(range_str.split("..")[0])
    range_max = int(range_str.split("..")[1])

    return range_min, range_max


def get_instances(element_dict):
    element_name = element_dict["name"]

    if "[" in element_name:
        range_min, range_max = parse_range(element_name)
        instances = (range_max - range_min) + 1
    else:
        instances = 1

    return instances


_tiles = 0
_cores_in_tile = []
_entry_list = []


def format_attributes(attributes):
    line = ""
    if attributes is None:
        attributes = {}

    for key in attributes:
        line += (f" {key}={attributes[key]}")
    return line


def create_tile(tile):
    global _tiles
    tile_id = _tiles
    _tiles += 1

    tile = f"t" + format_attributes(tile["attributes"])
    _entry_list.append(tile)
    # Track how many cores are in this tile
    _cores_in_tile.append(0)

    return tile_id


def create_core(tile_id, core_dict):
    core_id = _cores_in_tile[tile_id]
    core = f"c {tile_id}" + format_attributes(core_dict["attributes"])
    _entry_list.append(core)
    _cores_in_tile[tile_id] += 1

    return core_id


def create_synapse(tile_id, core_id, synapse_dict):
    synapse = f"s {tile_id} {core_id}" + format_attributes(synapse_dict["attributes"])
    _entry_list.append(synapse)
    return


def create_dendrite(tile_id, core_id, dendrite_dict):
    dendrite = f"d {tile_id} {core_id}" + format_attributes(dendrite_dict["attributes"])
    _entry_list.append(dendrite)
    return


def create_soma(tile_id, core_id, soma_dict):
    soma = (f"+ {tile_id} {core_id}" + format_attributes(soma_dict["attributes"]))
    _entry_list.append(soma)
    return


def create_axon_in(tile_id, core_id, axon_dict):
    axon = f"i {tile_id} {core_id}" + format_attributes(axon_dict["attributes"])
    _entry_list.append(axon)
    return


def create_axon_out(tile_id, core_id, axon_dict):
    axon = f"o {tile_id} {core_id}" + format_attributes(axon_dict["attributes"])
    _entry_list.append(axon)
    return


def create_noc(noc_dict):
    if "attributes" not in noc_dict:
        raise Exception("Error: NoC not defined for architecture (please add this under attributes)")
    _entry_list.append("@" + format_attributes(noc_dict["attributes"]))
    return


project_dir = os.path.dirname(os.path.abspath(__file__))
def run(arch_path, network_path, timesteps,
        run_dir=os.path.join(project_dir, "runs"),
        spike_trace=False, potential_trace=True, perf_trace=True,
        message_trace=False):
    parse_file(arch_path, os.path.join(run_dir, "arch"))
    # Parse inputs and run simulation
    args = []
    if spike_trace:
        args.append("-s",)
    if potential_trace:
        args.append("-v")
    if perf_trace:
        args.append("-p")
    if message_trace:
        args.append("-m")
    command = [os.path.join(project_dir, "sim"),] + args + [os.path.join(run_dir, "arch"),
               network_path, f"{timesteps}"]

    print("Command: {0}".format(" ".join(command)))
    ret = subprocess.call(command)
    if ret != 0:
        raise RuntimeError(f"Error: Simulator kernel failed (code={ret}).")

    with open("run_summary.yaml", "r") as run_summary:
        results = yaml.safe_load(run_summary)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(prog="python sim.py",
                                    description="Simulating Advanced Neuromorphic Architectures for Fast Exploration")
    parser.add_argument("architecture", help="Architecture description (YAML) file path", type=str)
    parser.add_argument("snn", help="Spiking Neural Network description file path", type=str)
    parser.add_argument("timesteps", help="Number of timesteps to simulate", type=int)

    args = parser.parse_args()
    print(args)

    run(args.architecture, args.snn_path, args.snn)
    print("sim finished")