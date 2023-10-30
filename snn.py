import abc
import sys

if sys.version_info >= (3, 4):
    ABC = abc.ABC
else:
    ABC = abc.ABCMeta("ABC", (), {"__slots__": ()})


### SNN UTILITY FUNCTIONS ###

class Network:
    def __init__(self, external_inputs=0, save_mappings=False):
        self.external_inputs = external_inputs
        self.inputs = []
        self.groups = []
        self._max_tiles = None
        self._max_cores = None
        self._max_compartments = None
        self._save_mappings = save_mappings

    def create_group(self, threshold, reset, leak, log_spikes=False,
                     log_potential=False, force_update=False,
                     connections_out=None, reverse_threshold=None,
                     reverse_reset_mode=None):
        group_id = len(self.groups)
        group = NeuronGroup(group_id, threshold, reset, leak, log_spikes,
                            log_potential, force_update, connections_out,
                            reverse_threshold, reverse_reset_mode)
        self.groups.append(group)
        return group

    def create_input(self):
        input_id = len(self.inputs)
        input_node = Input(input_id)
        self.inputs.append(input_node)
        return input_node

    def save(self, filename, group_idx=None):
        if group_idx is None:
            group_idx = slice(0, len(self.groups))
        with open(filename, 'w') as network_file:
            if self.external_inputs > 0:
                network_file.write("x {0} rate\n".format(self.external_inputs))
            for group in self.groups[group_idx]:
                network_file.write(str(group))

            for group in self.groups[group_idx]:
                for neuron in group.neurons:
                    neuron._save_mappings = self._save_mappings
                    network_file.write(str(neuron))

            for input_node in self.inputs:
                network_file.write(str(input_node))

    def load(self, filename):
        with open(filename, 'r') as network_file:
            for line in network_file:
                fields = line.split()
                if fields and fields[0] == 'g':
                    # TODO: support other fields to be loaded
                    neuron_count = int(fields[1])
                    group = self.create_group(0.0, 0.0, 0)
                    for _ in range(0, neuron_count):
                        group.create_neuron()

                elif fields and fields[0] == 'n':
                    pass
                    #neuron_address = fields[1]
                    #gid = int(neuron_address.split('.')[0])
                    #group = self.groups[gid]
                    #group.create_neuron()
                elif fields and fields[0] == 'e':
                    edge_info = fields[1]
                    src_address = edge_info.split("->")[0]
                    dest_address = edge_info.split("->")[1]

                    src_gid = int(src_address.split(".")[0])
                    src_nid = int(src_address.split(".")[1])
                    src = self.groups[src_gid].neurons[src_nid]

                    dest_gid = int(dest_address.split(".")[0])
                    dest_nid = int(dest_address.split(".")[1])
                    dest = self.groups[dest_gid].neurons[dest_nid]

                    weight = None
                    for f in fields:
                        if "w=" in f or "weight=" in f:
                            weight = float(f.split("=")[1])
                    src.add_connection(dest, weight)
                elif fields and fields[0] == '&':
                    # TODO: for now ignore the mappings, the whole reason I'm
                    #  trying this code is to explore different mappings
                    pass

        """
        for g in self.groups:
            for n in g.neurons:
                print(n)
        """
        return


class NeuronGroup:
    def __init__(self, group_id, threshold, reset, leak, log_spikes=None,
                 log_potential=None, force_update=None, connections_out=None,
                 reverse_reset=None, reverse_reset_mode=None):
        # TODO: support all features here
        self.id = group_id
        self.neurons = []
        self.threshold = threshold
        self.reset = reset
        self.reset_mode = None
        self.reverse_reset = reverse_reset
        self.reverse_reset_mode = reverse_reset_mode
        self.reverse_threshold = None
        self.leak_decay = leak
        self.connections_out = connections_out
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
        if self.connections_out is not None:
            group_str += f" connections_out={self.connections_out}"

        group_str += "\n"
        return group_str

    def create_neuron(self, log_spikes=None, log_potential=None,
                      force_update=None):
        neuron_id = len(self.neurons)
        neuron = Neuron(self, neuron_id, log_spikes=log_spikes,
                        log_potential=log_potential, force_update=force_update)
        self.neurons.append(neuron)
        return neuron

    
    def create_neuron_type(self, type="lif", parameters={}):
        neuron_id = len(self.neurons)
        neuron = Neuron(self, neuron_id, param_dict=parameters, type=type)
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

class Neuron():
    def __init__(self, group, neuron_id,
                 log_spikes=None, log_potential=None, force_update=None,
                 param_dict=None,
                 type=None):
        self.group = group
        self.id = neuron_id

        if type is not None:
            self.type = type
        else:
            self.type = "lif"
        self.param_dict = param_dict

        self.log_spikes = log_spikes
        self.log_potential = log_potential
        self.force_update = force_update
        self.connections = []
        self.tile = None
        self.core = None
        self.bias = None
        self._save_mappings = False

    def add_connection(self, dest, weight):
        self.connections.append((dest, weight))

    def add_bias(self, bias):
        self.bias = bias

    def __str__(self, map_neuron=True):
        neuron_str = f"n {self.group.id}.{self.id}"
        if self.type is not None:
            neuron_str += f" type={self.type}"

        if self.bias is not None:
            neuron_str += f" bias={self.bias}"

        if self.param_dict is not None:
            for param, val in self.param_dict.items():
                neuron_str += " "
                neuron_str += param
                neuron_str += "="
                neuron_str += str(val)
        else:
            if self.log_spikes is not None:
                self.log_spikes = int(self.log_spikes)
                neuron_str += f" log_spikes={int(self.log_spikes)}"
            if self.log_potential is not None:
                neuron_str += f" log_v={int(self.log_potential)}"
            if self.force_update is not None:
                neuron_str += f" force_update={int(self.force_update)}"
            if (self.group.connections_out is None or (self.connections and
                (len(self.connections) > self.group.connections_out))):
               neuron_str += f" connections_out={len(self.connections)}"
        neuron_str += "\n"

        for connection in self.connections:
            dest_neuron, weight = connection
            neuron_str += f"e {self.group.id}.{self.id}->"
            neuron_str += f"{dest_neuron.group.id}.{dest_neuron.id}"
            if isinstance(weight, float):
                neuron_str += f" w={weight:.5e}"
            else:
                neuron_str += f" w={weight}"
            neuron_str += "\n"

        if self._save_mappings:
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
                 log_spikes=False, log_potential=False, force_update=False,
                 threshold=1.0, reset=0.0, leak=1.0, mappings=None,
                 connections_out=None, reverse_threshold=None,
                 reverse_reset_mode=None):
    print("Creating layer with {0} neurons".format(layer_neuron_count))
    layer_group = network.create_group(threshold, reset, leak, log_spikes,
                                       log_potential, force_update,
                                       connections_out=connections_out,
                                       reverse_threshold=reverse_threshold,
                                       reverse_reset_mode=reverse_reset_mode)

    if mappings is not None:
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