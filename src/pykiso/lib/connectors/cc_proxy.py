##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Proxy Channel
*************

:module: cc_proxy

:synopsis: CChannel implementation for multi-auxiliary usage.

CCProxy channel was created, in order to enable the connection of
multiple auxiliaries on one and only one CChannel. This CChannel
has to be used with a so called proxy auxiliary.

.. currentmodule:: cc_proxy

"""

import logging
import queue
from typing import Tuple, Union

from pykiso import Message
from pykiso.connector import CChannel

ProxyReturn = Union[
    Tuple[bytes, int], Tuple[bytes, None], Tuple[Message, None], Tuple[None, None]
]

log = logging.getLogger(__name__)


class CCProxy(CChannel):
    """Proxy CChannel for multi auxiliary usage."""

    def __init__(self, **kwargs):
        """Initialize attributes."""
        super().__init__(**kwargs)
        self.queue_in = None
        self.queue_out = None
        self.timeout = 1

    def _cc_open(self) -> None:
        """Open proxy channel."""
        self.queue_in = queue.Queue()
        self.queue_out = queue.Queue()
        log.debug("Open proxy channel")

    def _cc_close(self) -> None:
        """Close proxy channel."""
        self.queue_in = queue.Queue()
        self.queue_out = queue.Queue()
        log.debug("Close proxy channel")

    def _cc_send(self, *args: tuple, **kwargs: dict) -> None:
        """Populate the queue in of the proxy connector.

        :param args: tuple containing positionnal arguments
        :param kwargs: dictionary containing named arguments
        """
        log.debug(f"put at proxy level: {args} {kwargs}")
        self.queue_in.put((args, kwargs))

    def _cc_receive(self, timeout: float = 0.1, raw: bool = False) -> ProxyReturn:
        """Depopulate the queue out of the proxy connector.

        :param timeout: not used
        :param raw: not used

        :return: raw bytes and source when it exist. if queue timeout
            is reached return None
        """

        try:
            raw_msg, source = self.queue_out.get(True, self.timeout)
            log.debug(f"received at proxy level : {raw_msg} || source {source}")
            return raw_msg, source
        except queue.Empty:
            return None, None
