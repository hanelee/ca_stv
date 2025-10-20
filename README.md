# CA Voting Analysis

This is a repository containing code to help analyze the effect of different voting systems within
the state of California.

## Systems Considered


| Voting Rule | Number of Districts |  Number of Winners per District |
|-------------|---------------------|---------------------------------|
|    STV      |          8          |               5                 |
|    STV      |         16          |               5                 |
|    STV      |         10          |               4                 |
|    STV      |         20          |               4                 |
|  Plurality  |         40          |               1                 |
|  Plurality  |         80          |               1                 |


## Preliminary Design

What follows is a detailing of the preliminary design of the experiment. There are several things
that can be expanded on from here, but this should provide some decent scaffolding to work
with.


1. For each of the above district counts, create an ensemble of 1000 plans, and sample 5 of them.
    - This ensemble will need to be expanded later. Generally, if you sample a plan every $N$ steps
      in an ensemble of $d$-district plans where $N > d\log(d)$, then you get a decent mix
      of partitions for statistical analysis (bound comes from coupon-collector problem).

1. For each of the sampled districts, compute a $(H, O)$ pair where $H$ is the hispanic proportion 
   of the voting age population (VAP) and $O = 1 - H$. 

1. Make a slate Plackett-Luce, slate Bradley-Terry, and Cambridge sampler preference profile for 
   each district with the following settings:

    - `n_voters`: 100000
    - `slate_to_candidates`:
        - "H": ["H1", "H2", "H3"],
        - "O": ["O1", "O2", "O3", "O4", "O5", "O6", "O7"],
    - `bloc_proportions`:
        - Depends on the sample
    - `cohesion_parameters`:
        | coh |   H  |   O  |
        |-----|------|------|
        |  H  | 0.77 | 0.23 |
        |  O  | 0.52 | 0.48 |
    - `alphas`:
        |  $\alpha$  |   H  |   O  |
        |------------|------|------|
        |      H     | 0.50 | 0.75 |
        |      O     | 0.75 | 0.50 |

## Software Setup

This repository was developed using the UV build system. This build system is generally available 
through chocolatey on Windows (`choco install uv`), homebrew on MacOS `brew install uv`, and 
through direct installation on Linux (e.g. `apt install uv`). You can also install directly from 
source using the instructions at [UV's homepage](https://docs.astral.sh/uv/) or you can install 
the system into a conda environment (`conda install conda-forge::uv`).

After installing UV, you can build the necessary virtual environment for this repository by 
invoking the command

```bash
uv sync
```

from the terminal while in the base directory.


## Some notes for replication

- There is a file called "py_env" in this repository that contains a single line: 
  `export PYTHONHASHSEED=0`. This environment variable ensures that Python's hashing is
  deterministic across runs. You will either need to source this environment file from your
  terminal, or tell UV to load it whenever you run a python script.

- In the "vk_profile_generator.py" file, we set the random seeds for both numpy and for the python
  random module at the top of the file. The numpy random seed guarantees that the random sampling 
  done by numpy within the VoteKit package is deterministic, and the python random seed ensures 
  that any calls to python's random module are also deterministic. As a note: all of python's 
  random hashing is NOT controlled by the random module and depends on the environment variable
  "PYTHONHASHSEED".

- Likewise, in the "run_all_experiments_parallel.py" file, we set the random seeds for both numpy 
  and for the python random module at the top of the file. This ensures that any random sampling 
  done within this script is also deterministic.

- We record the settings files for all of the experiments that we run since these are the 
  parameters that we pass to the `BlocSlateConfig` class within VoteKit. This class is what we 
  then use to generate the preference profiles for each sample. 
  
  - The profiles themselves are generated but not stored on GitHub due to size constraints. 
    However, if all of the appropriate random seeds are set and the instructions in the following
    section followed, then the results should be deterministic.

- There is a file called ".python-version" in this repository that is used by the UV build system
  to determine which version of python to use within the virtual environment. By including this
  file in all clones of the repository, we ensure that everyone is using the same version of python
  and that there are no unexpected variances the random or hashing behavior of python between runs.

- There is a file called "uv.lock" in this repository that is used by the UV build system to ensure
  that everyone is using the exact same version of all python packages when running the code in 
  this repository.
   


## Building the Dual Graph

A connected version of the dual graph was previously provided in a PKL file, but to turn it into
a JSON file that can easily be read in by GerryChain, you may run the script

```bash
uv run --env-file py_env make_bg_dualgraph.py
```

This only builds the dual grpah on block groups, and a pre-built graph has already been saved in 
the "data" folder.


## Running VoteKit the Pipeline

For now, we will assume that all of the samples that we need are in the "districting" folder. 

All of the settings files are already included in the "vk_run_settings" folder, but to reproduce
them, you may run

```bash
uv run --env-file py_env vk_settings_generator.py
```

Once the settings files are created, you may create all of the profiles using the command


```bash
uv run --env-file py_env vk_profile_generator.py
```

(this should only take a few minutes).

Finally, to run all of the experiments in parallel, you may use the command

```bash
uv run --env-file py_env run_all_experiments_parallel.py
```


## Runtime Notes

After parallelization, running the full pipeline on a machine with 32 cores and sufficient RAM
took approximately 40 minutes when sampling 5 districting plans for each of the systems with
all of the voting behavior models. As such, sampling 50 districting plans should be tractable
to process on a regular consumer machine with a day of processing time.


> [!WARNING]
> While the compute power is relatively low, storing the preference profiles can take up a 
> decent bit of space. As a reference, storing the preference profiles for 5 districting plans
> and 3 voter behavior models took up 8 GB of disk space. Thus storing the profiles for 50
> districting plans and 3 voter behavior models may take up to 80 GB of disk space. 
>
> This can, of course, be mitigated by running one voter model at a time or by generating
> the profiles on the fly before running the election experiments.
