Copyright (c) 2023 - The University of Texas at Austin
This work was produced under contract #2317831 to National Technology and
Engineering Solutions of Sandia, LLC which is under contract
No. DE-NA0003525 with the U.S. Department of Energy.

Simulating Advanced Neuromorphic Architectures for Fast Exploration (SANA-FE)

A framework to model energy and performance of neuromorphic hardware.

# To Build

This project uses CMake to create Makefiles. Use with:
`cmake .`

Then build Makefiles with:
`make`

## Dependencies

Building this project requires `cmake`, `make`, and a compiler that supports the C++11
standard.

This project uses Python to launch simulations, parse input files, and process
simulation results. Most project features require Python 3.8 or later, and the
modules listed in `requirements.txt`.

We recommend using `conda` to manage environments e.g.,

`conda create --name sanafe-env --file ./requirements.txt`
`conda activate sanafe-env`

# To Run an Example

`python3 sim.py arch/loihi.yaml snn/example.net 10`

This simulates 10 time-steps of a tiny connected spiking network.

General usage:

`python3 sim.py <architecture description> <SNN description> <N timesteps>`

Examples of more advanced usage are given in `scripts/`. This shows how
more complex simulations and experiments can be created. For example, see
`python3 scripts/calibration.py`

# Input Format

SANA-FE takes command line arguments, an architecture file and a SNN file.
The architecture description files and SNN description files both use custom
file formats. Examples for architectures may be found in `arch/`. Examples for
SNNs may be found in `snn/`.

There are optional flags for enabling traces in simulation. Note that even if
neurons have probes set up, no output will be generated if traces aren't enabled
globally at the command line.

Flags:
* `-v`: Enable potential (v) traces to `potential.trace`
* `-s`: Enable spike traces to `spikes.trace`
* `-p`: Record the simulated performance of each timestep to `perf.csv`
* `-m`: Enable message traces to `messages.trace`
* `-r`: Launch command-line interface for continuous execution.
* `-g`: Enable gui-specific simulation traces.

## SNN Description

Spiking Neural Networks are defined flexibly using a simple custom format.
Each line defines a new entry which may either be a neuron group (g),
neuron (n), edge (e), or mapping (&). Each entry starts with the type of entry
followed by one required field and then any number of named attributes.
Fields are separated by one or more spaces.

Attributes are defined using the syntax: `<attribute>=<value>`. Note, there
is no space before or after the equals. The attribute `soma_hw_name` and
`soma_model` is required to be set for every neuron or neuron group.

A neuron group is some population of neurons. The group defines any common
parameters e.g., for a layer of a deep SNN.

`g <number of neurons> <common attributes>`

Neurons are addressed (using the group number followed by neuron number), and
then all attributes are specified. Note the group must be defined first.

`n group_id.neuron_id <unique attributes>`

An edge connects one source neuron (presynaptic) to one destination neuron
(postsynaptic). The edge may also have attributes such as synaptic weight.

`e src_group_id.src_neuron_id->dest_group_id.dest_neuron_id <edge attributes>`

Finally, mappings place predefined neurons on a hardware core. Here we specify
the neuron and the core.

`& group_id.neuron_id@tile_id.core_id`

## Architecture Description

The architecture description format is based on the YAML file format.

Different architectures are defined using a hierarchical description.
This tool models neuromorphic designs with several assumptions, in order to
simplify the tool.

1) The chip is time-step based. A time-step is a small discrete amount of time.
    This is as opposed to a purely event driven simulation e.g. ROSS.
2) The neural cores adhere to some common design patterns

The top level is always the "architecture". This defines anything at the chip
level, including the NoC interconnect.
A chip contains one or more tiles, which with the interconnect form the NoC.
Each `tile` contains one or more cores, where a core performs computation.
Each neuromorphic `core` contains a subset of certain operations in a hardware
pipeline.
It is assumed that tiles and cores are all parallel processing elements.

Each core is assumed to have a neuromorphic pipeline which processes the updates
for one or more neurons. The pipeline is a fixed sequence of niche hardware
units. Those hardware units could contain digital logic, analog circuits or
even novel devices.

The pipeline contains the following units:

* Input axons receive spike packets from the network.

* The synaptic unit looks up connectivity for incoming spikes and updates
  the relevant synaptic currents.

* The dendritic unit combines currents based on a tree structure and a set
  of operations.

* The soma unit updates membrane potentials based on the dendritic current and
neuron model. If the firing criteria is met, it generates a spike for that
neuron.
The output axons send spikes from the soma out to the network to other
cores' pipelines.

For an example, see `arch/loihi.yaml`. There are a nested series of
keywords, where keywords define required hardware blocks. Each block must be
contain a `name` keyword, which may optionally specify the number of instances.
Blocks are duplicated the number specified in the range, for example:

    # Define 8 cores, 0 through 7
    -name: neuromorphic_core[0..7]

Blocks much also have an `attributes` section and the next hardware block in the
hierarchy. Attributes depend on the hardware being defined, and can be extended
in the future to support new architectures and features.

# Output Format

Outputs are hard fixed, either traces, csv or yaml files. These store varying
levels of detail about the simulation performance and energy / latency
estimates.

`spikes.trace`: The spikes for each time-step on probed neurons

`potential.trace`: The potentials for each time-step on probed neurons

`perf.csv`: Detailed statistics for each timestep and each hardware unit

`messages.trace`: Information on spike messages for each time-step

`run_summary.yaml`: High-level statistics for the simulation e.g. runtime

# Soma Plugin Model

SANA-FE's plugin model utilizes shared .so C++ files to execute all soma
calculations. There are some common plugins provided in the `/plugins`
folder along with their corresponding .cpp file.

To specify the soma plugin, several steps need to be taken:
1. The plugin name needs to be specified in the
architecture yaml file under `soma: -attributes: -model: [plugin name]`
2. The plugin name is set in the net file with the keyword
`soma_model=[plugin name]`.
3. The `/plugins` file contains the plugin compiled into a file with the
format `[plugin name].so`.

Each plugin holds a class that executes the functionality of the soma.
On every creation of a neuron, a new instance of the specific plugin
class will be created and stored.

## Creating a New Plugin

SANA-FE's plugin model makes it easy to create new soma classes and
integrate them directly into your SNN execution. There are, however,
two main interfacing requirements to allow plugins to smoothly execute.

1. The plugin class must extend the `Base_Soma` located in `plugins.hpp`.
This includes implementing the base constructor, `update_soma`, and
`parameters` functions.
2. Two class factory functions need to be created. These have to be in the 
format `create_[plugin_name]` and `destroy_[plugin_name]`. These functions
are used to get an instance of the class.

It is recommended new users read through the loihi_lif.cpp file to see what
an example soma class looks like. The `update_soma` function will be passed
the input current spike as a double and returns `Neuron_Status`, an enum
representing whether the neuron is idle, updated, or fired. The `parameters`
function takes in a struct of `attributes` with a specified int length.
These parameters are arbitrary keyword=value pairs that can pass in any
information to the class. This is where parameters specified in the network
file will be passed to.

To compile a .cpp file into the desired .so plugin file, run these commands
from within the plugins folder:
`g++ -c -fPIC -o [plugin_name].o [plugin_name].cpp`
`gcc -shared -o [plugin_name].so [plugin_name].o`

The .so should be kept, the .o file is unnecessary and can be deleted.

# Project Code

This project has been written in C, C++, and Python. See header files for
more detail.

`sim.py`
`main.cpp`
`sim.cpp`
`network.cpp`
`arch.cpp`
`description.cpp`
`command.cpp`
`plugins.cpp`
`module.cpp`

C code has been written based on the C99 standard.
C++ code has been written based on the C++11 standard.

# Contact
James Boyle: james.boyle@utexas.edu
