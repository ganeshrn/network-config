# Task template
The ```template``` task provides a means to build network device configurations
based on the device facts.  It uses the values of the current device and
tranforms them into device level configuration commands.  The configuration is
then returned to the playbook as a fact.

The ```template``` task is based on an internal template language that is
loosely based on the Ansible playbook directives.  It has been specifically
designed to make writing network device configurations easier than using
Jinaj2.

## Requirements
The following is the list of requirements for using the this task:

None

## Operation
The ```template``` task will load a template file that includes the set of
lines to be templated.  The template file format supports a number of
directives that can be used to control how the final configuration is rendered.  

The set of template directives is available [here](template_directives.md)

This task accepts the path to the source directory where the device templates
are located.  It will then iterate over all of the device templates rendering
the final device configuration and return the output in the ```configuration```
fact.

The task supports additional, optional arguments that can be used to filter
which files are templated.  Please see the [arguments](#arugments) section 
for more details.

## Arguments
The following are the list of required and optional arguments supported by this
task.

### source_dir
This argument specifies the path to the template files.  All template files
located in the ```source_dir``` will be loaded and used as templates unless
filtered by either ``exclude_files``` or ```include_files``` as noted below.

### exclude_files
The ```exclude_files``` accepts a list of absolute filenames or regular
expressions that define template files that should not be considered when
loading the templates files from the ```source_dir```

### include_files
The ```include_files``` accepts a list of absolute filenames or regular
expressions that define template files that should be considered when loading
the tempplate files for the ```source_dir```

### private_vars
The ```private_vars``` argument accepts a dictionary value that defines
additional variable to be used for templating the configuration but are not
stored in the host facts.

## Adding additional platform support
The ```get``` task can be extended to support additional network devices by
provider providers that return the device configuration.  In order to provide
support for additional platforms, simply add the ```get.yaml``` tasks in once
of the search locations and the role will automatically find it.

## Notes
None

## Changelog

* 2.5.0 - initial task added to the role

