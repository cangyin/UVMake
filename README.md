# Introduction
一个简单的 Keil uVision C51 Project 配置脚本。仅具有组织工程文件和配置少量 Project 参数的功能。

# Installation
## dependencies
1. python 3+
2. `pip install lxml ruamel.yaml`

# Basic Usage
在已有 Keil C51 Project 的基础上，该脚本才能运作。

设已有 Keil C51 Project 名为 DemoProject，在 `DemoProject` 文件夹下有
`DemoProject.uvproj` 和 `DemoProject.uvopt` 两文件。

## first command
In parent directory of `DemoProject`
```
uvmake.py DemoProject.yaml  -r -D ./DemoProject
```
Then we got a file named `DemoProject.yaml` in current directory.

You may have noticed one error message, saying:
```
[ERROR][uvmake.py:542] Project files: "project-name.uvproj" or "project-name.uvopt" not exist
```
It's fine, since we only specified the project directory in the command. so `uvmake` is using default project name. To avoid the error message, in this case, append `-P DemoProject` to the command.

`DemoProject.yaml` is the config file for this project, which mimics  a `Makefile`

## make changes in DemoProject.yaml
The config file (which is `DemoProject.yaml` in this case) is in `YAML` format, which is easy to edit by hand.

You make changes in this config file, then run
## the second command
```
uvmake.py DemoProject.yaml
```
Which configures every changes you made into the project files (namely, the *.uvproj and *.uvopt files).

# Features
1. 按 NONE、C_BY_FOLDER、ALL_BY_FOLDER 三种方式组织 Project 源代码文件 (see config file)。
2. 设置 MCU频率、目标文件名、输出文件夹、头文件路径，清除调试断点
3. For detailed parameters that `uvmake` is able to configure, see in config file.  
4. use `uvmake -t` to get a template config file.

    Note: For some reason, some of the comments in config file, which describes purpose of items there, get lost if you update or generate your config file from command `uvmake.py ... -r ...`

# Help Info
`uvmake.py -h`
```
usage:
        uvmake.py  <path-to-config-file>       [options]


Configure tool for Keil uVsion C51 projects (for Keil C51 version 5)

positional arguments:
  <path-to-config-file>
                        path of config file, defaults to `uvmake.yaml` in
                        current directory

optional arguments:
  -h, --help            show this help message and exit
  -t, --config-template
                        generate template config file (file name is taken from
                        option `<path-to-config-file>`). existing file will be
                        overwritten.
  -r, --reverse-config  update the config file according to project files. if
                        config file doesn't already exist, it is generated
                        from template (see option `-t`) first
  -u, --update-config   same as option `-r`
  -K, --no-backup       do not backup project files before making changes.
  -d, --debug           run with debug output
  -v, --version         show version information

project specific arguments:
  -S SOURCE [SOURCE ...], --source SOURCE [SOURCE ...]
                        directories where your C51 source files are, in
                        addition to the value from `uvmake.yaml`
  -I INCLUDE [INCLUDE ...], --include INCLUDE [INCLUDE ...]
                        path for header files (.h files), in addition to the
                        value from `uvmake.yaml`
  -D PROJECT_DIR, --project-dir PROJECT_DIR
                        directory for orginal and generated C51 project files.
                        Overrides the value from `uvmake.yaml`
  -P PROJECT_NAME, --project-name PROJECT_NAME
                        name of the project files. Overrides the value from
                        `uvmake.yaml`
  -N TARGET_NAME, --target-name TARGET_NAME
                        target name of the project
  -O OUTPUT_DIR, --output-dir OUTPUT_DIR
                        output directory for object files of the project.
                        Overrides the value from `uvmake.yaml`
  -o OUTPUT_NAME, --output-name OUTPUT_NAME
                        output object file filename of the project. Overrides
                        the value from `uvmake.yaml`
  -F CLOCK_FREQ, --clock-freq CLOCK_FREQ
                        clock frequency of MCU used in project
```
