##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

"""
Communication Channel Via segger j-link
***************************************

:module: cc_rtt_segger

:synopsis: channel used to enable RTT communication using Segger J-Link debugger.
    Additionally, RTT logs can be captured by setting the rtt_log_path parameter
    on the specified channel.

.. currentmodule:: cc_rtt_segger

"""

import logging
import threading
import time
from pathlib import Path
from typing import Optional, Union

import pylink

from pykiso import connector
from pykiso.message import Message

log = logging.getLogger(__name__)


class CCRttSegger(connector.CChannel):
    """Channel using RTT to communicate through Segger J-Link debugger."""

    def __init__(
        self,
        serial_number: int = None,
        chip_name: str = "STM32L562QE",
        speed: int = 4000,
        block_address: int = 0x2003F800,
        verbose: bool = False,
        tx_buffer_idx: int = 3,
        rx_buffer_idx: int = 0,
        rtt_log_path: Optional[str] = None,
        rtt_log_buffer_idx: int = 0,
        connection_timeout: int = 5,
        **kwargs,
    ):
        """Initialize attributes.

        :param serial_number: optional segger debugger serial number (required if many connected)
        :param chip_name: microcontoller name (STM....)
        :param speed: communication speed in Hz
        :param block_address: start address to start RTT communication
        :param tx_buffer_idx: buffer index used for transmission
        :param rx_buffer_idx: buffer index used for reception
        :param verbose: boolean indicating if J-Link connection should be verbose in logging
        :param rtt_log_path: path to the folder where the RTT log file should be stored
        :param rtt_log_buffer_idx: buffer index used for RTT logging
        :param connection_timeout: available time (in seconds) to open the connection
        """
        super().__init__(**kwargs)
        self.serial_number = serial_number
        self.chip_name = chip_name
        self.speed = speed
        self.block_address = block_address
        self.tx_buffer_idx = tx_buffer_idx
        self.rx_buffer_idx = rx_buffer_idx
        self.verbose = verbose
        self.jlink = None
        self.connection_timeout = connection_timeout
        self.rtt_log_buffer_idx = rtt_log_buffer_idx
        # initialize rtt logging specific parameters
        self._is_running = False
        self.rtt_log_thread = threading.Thread(target=self.receive_log)
        self.rtt_log_path = rtt_log_path
        if self.rtt_log_path is not None:
            self.rtt_log_buffer_size = 0
            self.rtt_log_path = Path(rtt_log_path)
            rtt_fh = logging.FileHandler(self.rtt_log_path / "rtt.log")
            rtt_fh.setLevel(logging.DEBUG)
            self.rtt_log = logging.getLogger(f"{__name__}.RTT")
            self.rtt_log.setLevel(logging.DEBUG)
            self.rtt_log.addHandler(rtt_fh)

    def _cc_open(self) -> None:
        """Connect debugger/microcontroller.

        This method proceed to the following actions :
        - create a JLink class instance
        - connect to  the debugger(using open method)
        - set debugger interface to SWD
        - connect debugger to the specified chip
        - start RTT communication
        - start RTT Logging the specified channel if activated

        :raise JLinkRTTException: if connection timeout occurred.
        """
        self.jlink = pylink.JLink()

        # connect to J-Link debugger
        if not self.jlink.opened():
            self.jlink.open(self.serial_number)
            log.info(f"connection made with J-Link debugger {self.serial_number}")
        else:
            log.debug("connection to J-Link already started")
        # set target interface to SWD
        self.jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
        # connect debugger to  the specified target
        self.jlink.connect(
            chip_name=self.chip_name, speed=self.speed, verbose=self.verbose
        )
        log.debug(
            f"connection to chip {self.chip_name} performed at speed {self.speed} Hz"
        )
        # start rtt at the specified address
        self.jlink.rtt_start(self.block_address)
        log.info(f"RTT communication started at address {self.block_address}")

        t_start = time.perf_counter()
        while True:
            try:
                num_up = self.jlink.rtt_get_num_up_buffers()
                num_down = self.jlink.rtt_get_num_down_buffers()

                log.debug(
                    f"RTT started. Found {num_up} up and {num_down} down channels."
                )
                break
            except pylink.errors.JLinkRTTException:
                time.sleep(0.1)
                # Exit the while loop once timeout is reached
                if time.perf_counter() > (t_start + self.connection_timeout):
                    raise

        # start rtt logging thread on buffer index rtt_log_buffer_idx
        if self.rtt_log_path is not None:
            try:
                rtt_log_buffer = self.jlink.rtt_get_buf_descriptor(
                    self.rtt_log_buffer_idx, True
                )
                self.rtt_log_buffer_size = rtt_log_buffer.SizeOfBuffer
                if self.rtt_log_buffer_size == 0:
                    raise ValueError
                log.debug(f"RTT log buffer size is {self.rtt_log_buffer_size} bytes")
            except ValueError:
                log.debug("Read RTT log buffer size is 0, defaulting to 1kB")
                self.rtt_log_buffer_size = 1024
            except pylink.errors.JLinkRTTException as e:
                log.error(f"Could not get RTT log buffer size: {e}")
                if self.rtt_log_buffer_idx not in range(num_up + 1):
                    log.error(f"Buffer index must be at most {num_up}")
                    self.rtt_log_buffer_idx = 0
                self.rtt_log_buffer_size = 1024
            finally:
                self._is_running = True
                self.rtt_log_thread.start()
                log.info("RTT logging started")

    def _cc_close(self) -> None:
        """Close current RTT communication in use."""

        if self.jlink is not None:
            self._is_running = False
            self.jlink.rtt_stop()
            self.jlink.close()
            log.info("RTT communication closed")

    def _cc_send(self, msg: Message or bytes, raw: bool = False) -> None:
        """Send message using the corresponding RTT buffer.

        :param msg: message to send, should be Message type or bytes.
        :param raw: if raw is True simply send it as it is, otherwise apply serialization
        """
        try:
            if not raw:
                msg = msg.serialize()
            msg = list(msg)
            bytes_written = self.jlink.rtt_write(self.tx_buffer_idx, msg)
            log.debug(
                f"===> message sent (RTT): on buffer {self.tx_buffer_idx}:{msg}, number of bytes written : {bytes_written}"
            )
        except Exception:
            log.exception(
                f"ERROR occurred while sending {len(msg)} bytes on buffer number {self.tx_buffer_idx}"
            )

    def _cc_receive(
        self, timeout: float = 0.1, raw: bool = False
    ) -> Union[Message, bytes, None]:
        """Read message from the corresponding RTT buffer.

        :param timeout: timeout applied on receive event
        :param raw: if raw is True return raw bytes, otherwise Message type like

        :return: Message or raw bytes if successful, otherwise None
        """
        is_timeout = False
        t_start = time.perf_counter()

        # rtt_read is not a blocking method due to this fact a while loop is used
        # to act like a blocking ones.
        while not is_timeout:
            try:
                # Read the message header
                msg_received = self.jlink.rtt_read(
                    self.rx_buffer_idx, Message().header_size
                )

                # if a message is received
                if msg_received:
                    # Read the payload and CRC
                    msg_received += self.jlink.rtt_read(
                        self.rx_buffer_idx,
                        msg_received[-1] + Message().crc_byte_size,
                    )

                    # Parse the bytes list into bytes string
                    msg_received = bytes(msg_received)
                    log.debug(
                        f"<=== message received (RTT) on buffer {self.rx_buffer_idx}:{msg_received}, number of bytes read : {len(msg_received)}"
                    )
                    if not raw:
                        msg_received = Message.parse_packet(msg_received)
                    break
            except Exception:
                log.exception(
                    f"encountered error while receiving message via {self} on buffer {self.rx_buffer_idx}"
                )
                return None

            # Exit the while loop once timeout is reached
            if time.perf_counter() > (t_start + timeout):
                is_timeout = True
                msg_received = None

        return msg_received

    def receive_log(self) -> None:
        """Receive RTT log messages from the corresponding RTT buffer."""
        while self._is_running:
            # receive at most rtt_log_buffer_size of RTT logs
            log_msg = self.jlink.rtt_read(
                self.rtt_log_buffer_idx, self.rtt_log_buffer_size
            )
            if log_msg:
                self.rtt_log.debug(bytes(log_msg).decode())
