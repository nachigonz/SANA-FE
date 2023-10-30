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
        perf_trace=True, spike_trace=False, potential_trace=False,
        message_trace=False):
    parsed_filename = os.path.join(run_dir,
                                   os.path.basename(arch_path) + ".parsed")
    parse_file(arch_path, parsed_filename)
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
    command = [os.path.join(project_dir, "sim"),] + args + [parsed_filename,
               network_path, f"{timesteps}"]

    print("Command: {0}".format(" ".join(command)))
    ret = subprocess.call(command)
    if ret != 0:
        raise RuntimeError(f"Error: Simulator kernel failed (code={ret}).")

    with open("run_summary.yaml", "r") as run_summary:
        results = yaml.safe_load(run_summary)

    return results


if __name__ == "__main__":
    # Run SANA-FE from the command-line
    import argparse

    parser = argparse.ArgumentParser(prog="python sim.py",
                                    description="Simulating Advanced Neuromorphic Architectures for Fast Exploration")
    parser.add_argument("architecture", help="Architecture description (YAML) file path", type=str)
    parser.add_argument("snn", help="Spiking Neural Network description file path", type=str)
    parser.add_argument("timesteps", help="Number of timesteps to simulate", type=int)
    parser.add_argument("-s", "--spikes", help="Trace spikes", action="store_true")
    parser.add_argument("-v", "--voltages", help="Trace membrane voltages", action="store_true")

    args = parser.parse_args()
    print(args)

    run(args.architecture, args.snn, args.timesteps,
        spike_trace=args.spikes, potential_trace=args.voltages)
    print("sim finished")
