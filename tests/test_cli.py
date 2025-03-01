##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import os
from pathlib import Path

import pytest

from pykiso import cli


@pytest.mark.parametrize(
    "path, level, expected_level, report_type",
    [
        (None, "INFO", logging.INFO, "junit"),
        (os.getcwd(), "WARNING", logging.WARNING, "text"),
        (None, "ERROR", logging.ERROR, None),
    ],
)
def test_initialize_logging(mocker, path, level, expected_level, report_type):

    mocker.patch("logging.Logger.addHandler")
    mocker.patch("logging.FileHandler.__init__", return_value=None)

    logger = cli.initialize_logging(path, level, report_type)

    assert isinstance(logger, logging.Logger)
    assert logger.isEnabledFor(expected_level)
    assert cli.log_options.log_path == path
    assert cli.log_options.log_level == level
    assert cli.log_options.report_type == report_type


def test_get_logging_options():

    cli.log_options = cli.LogOptions(None, "ERROR", None)

    options = cli.get_logging_options()

    assert options is not None
    assert options.log_level == "ERROR"
    assert options.report_type is None
