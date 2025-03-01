##########################################################################
# Copyright (c) 2010-2021 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Interface Definition for Connectors, CChannels and Flasher
**********************************************************

:module: connector

:synopsis: Interface for a channel

.. currentmodule:: connector


"""
import abc
import pathlib
import threading

from .types import MsgType, PathType


class Connector(abc.ABC):
    """Abstract interface for all connectors to inherit from.

    Defines hooks for opening and closing the connector and
    also defines a contextmanager interface."""

    def __init__(self, name: str = None):
        """Constructor.

        :param name: alias for the connector, used for ``repr`` and logging.
        """
        super().__init__()
        self.name = name

    def __repr__(self):
        name = self.name
        repr_ = super().__repr__()
        if name:
            repr_ = repr_[:1] + f"{name} is " + repr_[1:]
        return repr_

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, typ, value, traceback):
        self.close()
        if value is not None:
            raise value

    @abc.abstractmethod
    def open(self):
        """Initialise the Connector."""
        pass

    @abc.abstractmethod
    def close(self):
        """Close the connector, freeing resources."""
        pass


class CChannel(Connector):
    """Abstract class for coordination channel."""

    def __init__(self, **kwargs):
        """constructor"""
        super().__init__(**kwargs)
        self._lock = threading.RLock()

    def open(self) -> None:
        """Open a thread-safe channel.

        :raise ConnectionRefusedError: when lock acquire failed
        """
        # If we successfully lock the channel, open it
        if self._lock.acquire(blocking=False):
            self._cc_open()
        else:
            raise ConnectionRefusedError

    def close(self) -> None:
        """Close a thread-safe channel."""
        # Close channel and release lock
        self._cc_close()
        self._lock.release()

    def cc_send(self, msg: MsgType, raw: bool = False, **kwargs):
        """Send a thread-safe message on the channel and wait for an acknowledgement.

        :param msg: message to send

        :raise ConnectionRefusedError: when lock acquire failed
        """
        # TODO should blocking be a parameter?
        if self._lock.acquire(blocking=False):
            self._cc_send(msg=msg, raw=raw, **kwargs)
        else:
            raise ConnectionRefusedError
        self._lock.release()

    def cc_receive(self, timeout: float = 0.1, raw: bool = False):
        """Read a thread-safe message on the channel and send an acknowledgement.

        :param timeout: time in second to wait for reading a message
        :param raw: should the message be returned raw or should it be interpreted as a
            pykiso.Message?

        :return: Message if successful, None else

        :raise ConnectionRefusedError: when lock acquire failed
        """
        received_message = None
        if self._lock.acquire(blocking=False):
            # Store received message
            received_message = self._cc_receive(timeout=timeout, raw=raw)
        else:
            raise ConnectionRefusedError
        self._lock.release()
        return received_message

    @abc.abstractmethod
    def _cc_open(self):
        """Open the channel."""
        pass

    @abc.abstractmethod
    def _cc_close(self):
        """Close the channel."""
        pass

    @abc.abstractmethod
    def _cc_send(self, msg: MsgType, raw: bool = False) -> None:
        """Sends the message on the channel.

        :param msg: Message to send out
        :param raw: send raw message without further work (default: False)
        """
        # TODO define exception to raise?
        pass

    @abc.abstractmethod
    def _cc_receive(self, timeout: float, raw: bool = False) -> MsgType:
        """How to receive something from the channel.

        :param timeout: Time to wait in second for a message to be received
        :param raw: send raw message without further work (default: False)

        :return: message.Message() - If one received / None - If not
        """
        # TODO define exception to raise?
        pass


class Flasher(Connector):
    """Interface for devices that can flash firmware on our targets."""

    def __init__(self, binary: PathType = None, **kwargs):
        """Constructor.

        :param binary: binary firmware file

        :raise ValueError: if binary doesn't exist or is not a file
        :raise TypeError: if given binary is None
        """
        super().__init__(**kwargs)
        if binary is not None:
            binary = pathlib.Path(binary).resolve()  # force an absolute path
            if binary.exists() and binary.is_file():
                self.binary = binary
            else:
                raise ValueError(
                    f"'binary' must be a path-like object to an existing file (got {binary})"
                )
        else:
            raise TypeError("'binary' must be a path-like object, not None")

    @abc.abstractmethod
    def flash(self):
        """Flash firmware on the target."""
        pass
