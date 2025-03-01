# PyKiso

## Introduction ##
**pykiso** is an integration test framework. With it, it is possible to write
* Whitebox integration tests directly on my target device
* Graybox integration tests to make sure the communication-link with my target device is working as expected
* Blackbox integration tests to make sure my external device interfaces are working as expected

The project will contain:
* The core python framework (this repository)
* Framework plugins that are generic enough to be integrated as "native" (this repository)
* Additional "testApps" for different targets platforms (e.g. stm32, ...) or languages (C, C++, ...) . It could be pure SW or also HW (other repositories)

## Requirements ##

* Python 3.6+
* pip/pipenv (used to get the rest of the requirements)

## Install ##

```bash
cd kiso-testing
pip install .
```

[Pipenv](https://github.com/pypa/pipenv) is more appropriate for developers as it automatically creates virtual environments.

```bash
cd kiso-testing
pipenv install --dev
pipenv shell
```

### Pre-Commit

To improve code-quality, a configuration of [pre-commit](https://pre-commit.com/) hooks are available.
The following pre-commit hooks are used:

- black
- trailing-whitespace
- end-of-file-fixer
- check-docstring-first
- check-json
- check-added-large-files
- check-yaml
- debug-statements

If you don't have pre-commit installed, you can get it using pip:

```bash
pip install pre-commit
```

Start using the hooks with

```bash
pre-commit install
```

## Usage ##

Once installed the application is bound to `pykiso`, it can be called with the following arguments:

```bash
Usage: pykiso [OPTIONS]

  Embedded Integration Test Framework

Options:
  -c, --test-configuration-file FILE
                                  path to the test configuration file (in YAML
                                  format)  [required]

  -l, --log-path PATH             path to log-file or folder. If not set will
                                  log to STDOUT

  --log-level [DEBUG|INFO|WARNING|ERROR]
                                  set the verbosity of the logging
  --version                       Show the version and exit.
  --help                          Show this message and exit.
```

Suitable config files are available in the `test-examples` folder.

### Demo using example config ##

```bash
invoke run
```

### Running the Tests ##

```bash
invoke test
```

or

```bash
pytest
```

## List of limitations / todos for the python side

* [ ] **When the auxiliary does not answer (ping or else), GenericTest.BasicTest.cleanup_and_skip() call will result in a lock and break the framework.**
* [x] No test-setion will be executed, needs to be removed later.
* [x] test configuration files need to be reworked
* [x] Names & configurations in the *cfg file json* are character precise class names & associated parameters.
* [ ] Spelling mistakes need to be fixed!  _*ongoing*_
* [x] Add verbosity parameters to pass to the unittest framework to get more details about the test.
* [ ] **Add result parsing for Jenkins (see: https://stackoverflow.com/questions/11241781/python-unittests-in-jenkins).**
* [x] Create a python package
    * [ ] and host it on pip.