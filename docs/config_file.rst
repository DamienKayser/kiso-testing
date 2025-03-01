.. _config_file:


Test Configuration File
=======================

The test configuration files are written in YAML.

Let's use an example to understand the structure.

.. literalinclude:: ../examples/dummy.yaml
    :language: yaml
    :linenos:

Connectors
----------

The connector definition is a named list (dictionary in python) of key-value pairs, namely config and type.

.. literalinclude:: ../examples/dummy.yaml
    :language: yaml
    :lines: 12-21

The channel alias will identify this configuration for the auxiliaries.

The config can be omitted, `null`, or any number of key-value pairs.

The type consists of a module location and a class name that is expected to be found in the module.
The location can be a path to a python file (Win/Linux, relative/absolute) or a python module on the python path (e.h. `pykiso.lib.connectors.cc_uart`).

.. code:: yaml

    <chan>:                      # channel alias
        config:                  # channel config, optional
            <key>: <value>       # collection of key-value pairs, e.g. "port: 80"
        type: <module:Class>     # location of the python class that represents this channel


Auxiliaries
-----------

The auxiliary definition is a named list (dictionary in python) of key-value pairs, namely config, connectors and type.

.. literalinclude:: ../examples/dummy.yaml
    :language: yaml
    :lines: 1-11


The auxiliary alias will identify this configuration for the testcases.
When running the tests the testcases can import an auxiliary instance defined here using

.. code:: python

    from pykiso.auxiliaries import <alias>

The connectors can be omitted, `null`, or any number of role-connector pairs.
The roles are defined in the auxiliary implementation, usual examples are `com` and `flash`.
The channel aliases are the ones you defined in the connectors section above.

The config can be omitted, `null`, or any number of key-value pairs.

The type consists of a module location and a class name that is expected to be found in the module.
The location can be a path to a python file (Win/Linux, relative/absolute) or a python module on the python path (e.h. `pykiso.lib.auxiliaries.communication_auxiliary`).

.. code:: yaml

    <aux>:                           # aux alias
        connectors:                  # list of connectors this auxiliary needs
            <role>: <channel-alias>  # <role> has to be the name defined in the Auxiliary class,
                                     #  <channel-alias> is the alias defined above
        config:                      # channel config, optional
            <key>: <value>           # collection of key-value pairs, e.g. "port: 80"
        type: <module:Class>         # location of the python class that represents this auxiliary


Test Suites
-----------

The test suite definition is a list of key-value pairs.

.. literalinclude:: ../examples/dummy.yaml
    :language: yaml
    :lines: 22-

Each test suite consists of a `test_suite_id`, a `suite_dir` and a `test_filter_pattern`.


Real-World Configuration File
-----------------------------

.. literalinclude:: ../examples/uart.yaml
    :language: yaml
    :linenos:


Deactivation of specific loggers
--------------------------------

By default, every logger that does not belong to the `pykiso` package or that is not an `auxiliary` logger will see its level set to WARNING even if you have in the command line `pykiso --log-level DEBUG`.
This aims to reduce redundant logs from additional modules during the test execution.
For keeping specific loggers to the set log-level, it is possible to set the `activate_log` parameter in the `auxiliary` config.
The following example deactivates the `jlink` logger from the `pylink` package, imported in `cc_rtt_segger.py`:

.. code:: yaml

auxiliaries:
  aux1:
    connectors:
      com: rtt_channel
    config:
      activate_log:
      # only specifying pylink will include child loggers
      - pylink.jlink
      - my_pkg
    type: pykiso.lib.auxiliaries.dut_auxiliary:DUTAuxiliary
connectors:
  rtt_channel:
    config: null
    type: pykiso.lib.connectors.cc_rtt_segger:CCRttSegger

Based on this example, by specifying `my_pkg`, all child loggers will also be set to the set log-level.

.. note:: If e.g. only the logger `my_pkg.module_1` should be set to the level, it should be entered as such.

Ability to use environment variables
------------------------------------

It is possible to replace any value by an environment variable in the YAML files. When using environment variables, the following format should be respected: `ENV{my-env-var}`.
In the following example, an environment variable called `TEST_SUITE_1` contains the path to the test suite 1 directory.

.. literalinclude:: ../examples/dummy_env_var.yaml
    :language: yaml
    :lines: 22-25


Specify files and folders
-------------------------

To specify files and folders you can use absolute or relative paths.
Relative paths are always given relative to the location of the yaml file.

Relative path or file locations must always start with "./"

.. code:: yaml

    example_config:
        rel_script_path: './script_folder/my_awesome_script.py'
        abs_script_path_win: 'C:/script_folder/my_awesome_script.py'
        abs_script_path_unix: '/home/usr/script_folder/my_awesome_script.py'

Make a proxy auxiliary trace
----------------------------

Proxy auxiliary is capable of creating a trace file, where all received messages at connector
level are written. This feature is useful when proxy auxiliary is associated with a connector
who doesn't have any trace capability (in contrast to cc_pcan_can or cc_rtt_segger for example).

Everything is handled at configuration level and especially at yaml file :

.. code:: yaml

  proxy_aux:
    connectors:
      # communication channel alias
      com: <channel-alias>
    config:
      # Auxiliaries alias list bound to proxy auxiliary
      aux_list : [<aux alias 1>, <aux alias 2>, <aux alias 3>]
      # activate trace at proxy level, sniff everything received at
      # connector level and write it in .log file.
      activate_trace : True
      # by default the trace is placed where pykiso is launched
      # otherwise user should specify his own path
      # (absolute and relative)
      trace_dir: ./suite_proxy
      # by default the trace file's name is :
      # YY-MM-DD_hh-mm-ss_proxy_logging.log
      # otherwise user should specify his own name
      trace_name: can_trace
    type: pykiso.lib.auxiliaries.proxy_auxiliary:ProxyAuxiliary
