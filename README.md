# MAvis - 02182

This repository contains content for the MAvis assignments of the DTU course: Symbolic artificial intelligence - 02182, and is considered DTU property.

This README includes guides for setting up your own private downstream repository, installing the requirements, and how to use the client and server.
For information on how to interface with the Pepper robots see the [Robot guide](docs/robot_guide.md).

## Table of contents
- [Table of contents](#table-of-contents)
- [Private repository setup](#private-repository-setup)
- [Requirements](#requirements)
- [Devcontainer](#devcontainer)
  - [Setup](#setup)
  - [Adding pip packages](#adding-pip-packages)
  - [(noVNC) changing the resolution of the virtual environment](#novnc-changing-the-resolution-of-the-virtual-environment)
- [Usage](#usage)
  - [Agent types](#agent-types)
  - [Debugging](#debugging)
  - [Memory settings](#memory-settings)
- [Interactive documentation](#interactive-documentation)


## Private repository setup

To setup your own private repository for your group work, follow these steps:

1. Create an empty private repo. It is absolutely crucial that this repo is *private*.
2. Bare clone the handout repo, and mirror push it to your private repo:
```shell
git clone --bare https://github.com/MAvis-DTU/02182-MAvis-Code-Handout.git
cd 02182-MAvis-Code-Handout.git
git push --mirror https://github.com/dtu-student-123/your-repo.git
cd ..
# Linux based systems
rm -rf 02182-MAvis-Code-Handout.git
# Powershell
rm -r -fo 02182-MAvis-Code-Handout.git
```
3. Add handout repository as a remote in your private repo:
```shell
git clone https://github.com/dtu-student-123/your-repo.git
cd your-repo
git remote add public https://github.com/MAvis-DTU/02182-MAvis-Code-Handout.git
```
4. From now on, every time you need to include new changes from the handout repo, run:
```shell
git pull public main
git push origin main
```

## Requirements
To simplify the installation of the requirements for this repo a [Devcontainer](#devcontainer) has been produces, which creates a virtual development environment with all the necessary requirements.   
However if you want to install the dependencies locally the following section outlines what is required.

---
**IMPORTANT** to interact with the robots used in this course the [libqi](https://github.com/aldebaran/libqi) library is used. `libqi` has a python wrapper [qi](https://pypi.org/project/qi/) which is **only available for unix based systems**. We therefore strongly discourage windows users from taking this path.

To complete assignments, it is required that you can execute Java programs compiled for the most recent Java release. 
You should therefore make sure to have an updated version of a Java Development Kit (JDK) installed before continuing. 
Both Oracle JDK and OpenJDK will do. Additionally, you should make sure your PATH variable is configured 
so that `java` is available in your command-line interface (command prompt/terminal).  
Run `java -version` from the command line to check which version your path is set up to use. It should be the version you just installed.  

The Python client has been tested with Python 3.12, but should work with versions of Python above 3.10.
The client requires the pip packages outlined in the [Devcontainer](#devcontainer) section.

## Devcontainer
To simplify the setup and installation of required dependencies, a [devcontainer](https://containers.dev/overview) has been created. This [docker](https://www.docker.com/) based development environment ensures you have all the necessary dependencies installed, and that your groups environment is the same, thus avoiding the "It works on my computer" cliché.

The environment comes preconfigured with:
- **Java (OpenJDK 17)** – Access via `java`
- **Python 3.12** – Access via `python3` - with the following pip dependencies
    - `psutil` to monitor client memory usage.
    - `debugpy` required to allow debugging through the java server
    - `numpy` to facilitate communication between the robot and the client
    - `scp` to transfer data (images & audio) to and from the robots
    - `qi` the Pepper SDK used to facilitate the communication with the robot
        - **Note** that this package is only available for Unix-based systems (MacOS & Linux)
    - `faster-whisper` to transcribe audio recordings, allowing verbal communication between user and robot.
    - Non-required packages:
        - `opencv-python` intended for manipulating image data from the robots
        - `pupil-apriltags` required to process apriltags
        - `graphviz` required to visualize solution graphs
        - `pdoc` required to run the [docs.py](docs.py) interactive code documentation
- **Graphviz** - For visualizing solution graphs. Accessed through the python package.
- **NoVNC**  - Some systems cannot efficiently forward and visualize the server graphics natively. As a workaround [noVNC](https://novnc.com/info.html) have been used to forward the graphics via a webserver.    
To see the virtual GUI environment, open [localhost:8080/vnc.html](http://localhost:8080/vnc.html) and press connect.  

### Setup
To setup the devcontainer the following **prerequisites** need to be installed:
1. [Docker](https://www.docker.com/)
    - **Note:** If you're using Windows, you may need to enable WSL2 and ensure your user has the correct Docker permissions.
2. [Visual studio code](https://code.visualstudio.com/)
3. The [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) vscode extension.
4. You have followed the [Private repository setup](#private-repository-setup)

With the prerequisites installed, follow these steps:
1. Open your repository in vscode
2. Open the vscode command palette (`ctrl/cmd+shift+p`)
3. Run the `Dev Containers: Rebuild and Reopen in Container` command
    - The first build may take a while - check the logs to track progress.
    - Once your files appear in the Explorer (left panel), the devcontainer is ready.
4. Check the setup
    1. Open the virtual GUI environment: [localhost:8080/vnc.html](http://localhost:8080/vnc.html) and press connect
    2. Execute the following command in the devcontainers terminal:  
        ```shell
        java -jar server.jar -g -s 300 -t 180 -c "python3 client.py classic" -l levels/SAD1.lvl
        ```
    3. If no errors occur and the desktop environment is visualized, the environment is working as intended.
    4. To close the server, cancel the command in the terminal (`ctrl/cmd+c` or `ctrl/cmd+z`)

### Adding pip packages
To ensure packages are installed when building or rebuilding the devcontainer, add wanted pip packages to the [.devcontainer/requirements.students.txt](.devcontainer/requirements.students.txt) file and rebuild the container (vscode command `Dev Containers: Rebuild Container`).

### (noVNC) changing the resolution of the virtual environment
1. Open [.devcontainer/docker-compose.yml](.devcontainer/docker-compose.yml)
2. Adjust the `DISPLAY_WIDTH` and `DISPLAY_HEIGHT` environment variables to your preference
3. Rebuild the devcontainer
    1. Open the vscode command palette (`ctrl+shift+p` or `cmd+shift+p`)
    2. Run the `Dev Containers: Rebuild Container` command

## Usage
All the following commands assume the working directory is the one this README is located in.

You can read about the server options using the -h argument:
```shell
java -jar server.jar -h
```

You can read about the client options using the `-h` flag:
```shell
python3 client.py -h
```

The client requires a agent type each with its own set of possible arguments and descriptions:
```shell
python3 client.py AGENT_TYPE -h
```

Running the server with the actions controlled by the client:
```shell
java -jar server.jar -g -s 300 -t 180 -c "python3 client.py classic" -l levels/SAD1.lvl
```

For strategy based search the client uses BFS by default, but can be changed by providing the `--strategy` argument. For instance, to use DFS:
```shell
java -jar server.jar -g -s 300 -t 180 -c "python3 client.py classic --strategy dfs" -l levels/SAD1.lvl
```

For astar and greedy, the `--heuristic` argument must be passed, specifying which heuristic to use for the strategy. There are currently two available: `goalcount` and `advanced`
For instance, to use astar search with the goalcount heuristic:
```shell
java -jar server.jar -g -s 300 -t 180 -c "python3 client.py classic --strategy astar --heuristic goalcount" -l levels/SAD1.lvl
```

### Agent types
The `agents` folder contains agent types including:
- `classic` - A classic planning agent using GRAPH-SEARCH.
- `decentralised` - A planning agent using DECENTRALISED-AGENTS.
- `helper` - A planning agent using the helper agent algorithm.
- `nondeterministic` - A planning agent using AND-OR-GRAPH-SEARCH with a broken executor.
- `goalrecognition` - A planning agent using the all optimal plans for the actor and AND-OR-GRAPH-SEARCH for the helper
- `robot` - A planning agent which forwards the actions to a connected pepper robot.

### Debugging
As communication with the java server is performed over stdout, `print(<something>)` does not work directly. 
To get information sent to the terminal, you should use `sys.stderr` or the alias `print_debug` from the `search` module:
```python
print(<something>, file=sys.stderr)
# Or
from search import print_debug
print_debug(<something>)
```
Note that the State has a nice string representation such that you can print states to the terminal by writing
```python
print_debug(state)
```
For more advanced debugging using vscode and the devcontainer, simply add the `--debug` flag when running the server, e.g.:
```shell
java -jar server.jar -g -c "python3 client.py --debug classic" -l levels/SAD1.lvl
```
then attach to the debugging server named `MAvis` in the vscode debug tab.  
**Note that the server will still timeout if the `-t` argument is given.**

### Memory settings
*Unless your hardware is unable to support this, you should let the searchclient allocate at least 4GB of memory.*

The searchclient monitors its own process' memory usage and terminates the search if it exceeds a given number of MiB.

To set the max memory usage to 4GB:
```shell
java -jar server.jar -g -s 300 -t 180 -c "python3 client.py --max-memory 4g classic" -l levels/SAD1.lvl
```
Avoid setting max memory usage too high, since it will lead to your OS doing memory swapping which is terribly slow.

## Interactive documentation
To host an interactive and searchable documentation of the code using its docstrings run:
```shell
python3 doc.py
```
This should host a webserver accessible via http://localhost:8080 (port can be changed in [docs.py](docs.py)).

