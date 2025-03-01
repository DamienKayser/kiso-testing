##########################################################################
# Copyright (c) 2010-2020 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

import logging
import queue
import sys
import time
import unittest.mock as mock

import pytest

import pykiso
from pykiso.connector import CChannel
from pykiso.lib.auxiliaries.proxy_auxiliary import (
    AuxiliaryInterface,
    ConfigRegistry,
    ProxyAuxiliary,
    log,
)

AUX_LIST_NAMES = ["MockAux1", "MockAux2"]
AUX_LIST_INCOMPATIBLE = ["MockAux3"]


def mock_cc_proxy():
    class MockProxyCChannel(CChannel):
        def __init__(self, *args, **kwargs):
            self.queue_in = queue.Queue()
            self.queue_out = queue.Queue()
            super(MockProxyCChannel, self).__init__(*args, **kwargs)

        def _cc_open(self):
            pass

        def _cc_close(self):
            pass

        def _cc_send(self):
            pass

        def _cc_receive(self):
            pass

    return MockProxyCChannel()


@pytest.fixture
def mock_auxiliaries():
    class MockAux1:
        def __init__(self, **kwargs):
            self.channel = mock_cc_proxy()
            self.is_proxy_capable = True

    class MockAux2:
        def __init__(self, **kwargs):
            self.channel = mock_cc_proxy()
            self.is_proxy_capable = True

    class MockAux3:
        def __init__(self, **kwargs):
            self.channel = mock_cc_proxy()
            self.is_proxy_capable = False

    sys.modules["pykiso.auxiliarie.MockAux1"] = MockAux1()
    sys.modules["pykiso.auxiliarie.MockAux2"] = MockAux2()
    sys.modules["pykiso.auxiliarie.MockAux3"] = MockAux3()


def test_constructor(mocker, cchannel_inst):
    mocker.patch(
        "pykiso.lib.auxiliaries.proxy_auxiliary.ProxyAuxiliary.run", return_value=None
    )

    proxy_inst = ProxyAuxiliary(cchannel_inst, [])

    assert isinstance(proxy_inst.proxy_channels, tuple)
    assert len(proxy_inst.proxy_channels) == 0


@pytest.mark.parametrize(
    "t_dir, t_name",
    [
        (None, None),
        (None, "mysuperlog"),
        ("", None),
        ("", "mysuperlog"),
    ],
)
def test_init_trace(mocker, t_dir, t_name):
    mocker.patch("logging.Logger.addHandler")
    mocker.patch("logging.FileHandler.__init__", return_value=None)

    logger = ProxyAuxiliary._init_trace(True, t_dir, t_name)

    assert isinstance(logger, logging.Logger)
    assert logger.isEnabledFor(logging.DEBUG)
    assert logger == logging.getLogger(f"pykiso.lib.auxiliaries.proxy_auxiliary.PROXY")


def test_init_trace_not_activate(mocker):
    logger = ProxyAuxiliary._init_trace(activate=False)

    assert logger == log


def test_get_proxy_con_valid(mocker, cchannel_inst, mock_auxiliaries):
    mocker.patch(
        "pykiso.lib.auxiliaries.proxy_auxiliary.ProxyAuxiliary.run", return_value=None
    )

    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])

    assert len(proxy_inst.proxy_channels) == 2
    assert isinstance(proxy_inst.proxy_channels[0], CChannel)
    assert isinstance(proxy_inst.proxy_channels[1], CChannel)


def test_get_proxy_con_invalid(mocker, caplog, cchannel_inst):
    mocker.patch(
        "pykiso.lib.auxiliaries.proxy_auxiliary.ProxyAuxiliary.run", return_value=None
    )

    mocker.patch.object(ConfigRegistry, "get_auxes_alias")

    with caplog.at_level(logging.ERROR):
        proxy_inst = ProxyAuxiliary(cchannel_inst, ["not_exist_aux", "fake_aux"])

    assert "Auxiliary : not_exist_aux doesn't exist" in caplog.text
    assert "Auxiliary : fake_aux doesn't exist" in caplog.text
    assert len(proxy_inst.proxy_channels) == 0


def test_get_proxy_con_pre_load(mocker, cchannel_inst):
    mocker.patch(
        "pykiso.lib.auxiliaries.proxy_auxiliary.ProxyAuxiliary.run", return_value=None
    )

    mocker.patch.object(ConfigRegistry, "get_auxes_alias", return_value="later_aux")

    class Linker:
        def __init__(self):
            self._aux_cache = AuxCache()

    class FakeAux:
        def __init__(self):
            self.channel = True
            self.is_proxy_capable = True

    class AuxCache:
        def get_instance(self, aux_name):
            return FakeAux()

    ConfigRegistry._linker = Linker()

    proxy_inst = ProxyAuxiliary(cchannel_inst, ["later_aux"])

    assert len(proxy_inst.proxy_channels) == 1
    assert isinstance(proxy_inst.proxy_channels[0], bool)


def test_check_compatibility_exception(mocker, cchannel_inst):
    mocker.patch(
        "pykiso.lib.auxiliaries.proxy_auxiliary.ProxyAuxiliary.run", return_value=None
    )

    with pytest.raises(NotImplementedError):
        proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_INCOMPATIBLE])


def test_create_auxiliary_instance_valid(mocker, cchannel_inst):
    mocker.patch(
        "pykiso.lib.auxiliaries.proxy_auxiliary.ProxyAuxiliary.run", return_value=None
    )
    mocker.patch("pykiso.connector.CChannel.open", return_value=None)

    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
    state = proxy_inst._create_auxiliary_instance()

    assert state == True
    assert proxy_inst.stop_event.is_set() == False


def test_create_auxiliary_instance_exception(mocker, cchannel_inst):
    mocker.patch(
        "pykiso.lib.auxiliaries.proxy_auxiliary.ProxyAuxiliary.run", return_value=None
    )
    mocker.patch(
        "pykiso.connector.CChannel.open", return_value=None, side_effect=ValueError()
    )

    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
    state = proxy_inst._create_auxiliary_instance()

    assert state == False
    assert proxy_inst.stop_event.is_set() == True


def test_delete_auxiliary_instance_valid(mocker, caplog, cchannel_inst):
    mocker.patch(
        "pykiso.lib.auxiliaries.proxy_auxiliary.ProxyAuxiliary.run", return_value=None
    )
    mocker.patch("pykiso.connector.CChannel.close", return_value=None)

    with caplog.at_level(logging.INFO):
        proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
        state = proxy_inst._delete_auxiliary_instance()

    assert "Delete auxiliary instance" in caplog.text
    assert state == True


def test_delete_auxiliary_instance_exception(mocker, caplog, cchannel_inst):
    mocker.patch(
        "pykiso.lib.auxiliaries.proxy_auxiliary.ProxyAuxiliary.run", return_value=None
    )
    mocker.patch(
        "pykiso.connector.CChannel.close", return_value=None, side_effect=ValueError()
    )

    with caplog.at_level(logging.ERROR):
        proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
        state = proxy_inst._delete_auxiliary_instance()

    assert "Error encouting during channel closure" in caplog.text
    assert state == True


def test_abort_command(mocker, cchannel_inst):
    mocker.patch(
        "pykiso.lib.auxiliaries.proxy_auxiliary.ProxyAuxiliary.run", return_value=None
    )
    proxy_inst = ProxyAuxiliary(cchannel_inst, [])
    ret_state = proxy_inst._abort_command()
    assert ret_state == True


@pytest.mark.parametrize(
    "message, source",
    [
        (b"\x12\x34\x56", 0x545),
        (b"\x12\x34\x56\x12\x34\x56", None),
    ],
)
def test_receive_message_valid(
    mocker, cchannel_inst, mock_auxiliaries, message, source
):
    mocker.patch(
        "pykiso.lib.auxiliaries.proxy_auxiliary.ProxyAuxiliary.run", return_value=None
    )
    mocker.patch("pykiso.connector.CChannel.cc_receive", return_value=(message, source))

    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
    proxy_inst._receive_message()

    link_aux_1 = sys.modules["pykiso.auxiliarie.MockAux1"]
    link_aux_2 = sys.modules["pykiso.auxiliarie.MockAux2"]

    recv_aux1 = link_aux_1.channel.queue_out.get()
    recv_aux2 = link_aux_2.channel.queue_out.get()

    msg_1, source_1 = recv_aux1
    msg_2, source_2 = recv_aux2

    assert isinstance(recv_aux1, list)
    assert isinstance(recv_aux2, list)
    assert msg_1 == message
    assert source_1 == source
    assert msg_2 == message
    assert source_2 == source


@pytest.mark.parametrize(
    "message, source",
    [
        (None, 0x545),
        (None, None),
    ],
)
def test_receive_message_no_message(
    mocker, cchannel_inst, mock_auxiliaries, message, source
):
    mocker.patch(
        "pykiso.lib.auxiliaries.proxy_auxiliary.ProxyAuxiliary.run", return_value=None
    )
    mocker.patch("pykiso.connector.CChannel.cc_receive", return_value=(None, None))

    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
    proxy_inst._receive_message()

    link_aux_1 = sys.modules["pykiso.auxiliarie.MockAux1"]
    link_aux_2 = sys.modules["pykiso.auxiliarie.MockAux2"]

    assert link_aux_1.channel.queue_out.qsize() == 0
    assert link_aux_2.channel.queue_out.qsize() == 0


def test_receive_message_exception(mocker, caplog, cchannel_inst):
    mocker.patch(
        "pykiso.lib.auxiliaries.proxy_auxiliary.ProxyAuxiliary.run", return_value=None
    )
    mocker.patch(
        "pykiso.connector.CChannel.cc_receive",
        return_value=None,
        side_effect=ValueError(),
    )

    with caplog.at_level(logging.ERROR):
        proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
        proxy_inst._receive_message()

    assert "encountered error while receiving message via" in caplog.text


@pytest.mark.parametrize(
    "message, remote_id",
    [
        (b"\x12\x34\x56", 0x545),
        (b"\x12\x34", 0x001),
        (b"\x12\x34\x12\x34\x56", None),
    ],
)
def test_dispatch_command(mocker, cchannel_inst, mock_auxiliaries, message, remote_id):
    mocker.patch(
        "pykiso.lib.auxiliaries.proxy_auxiliary.ProxyAuxiliary.run", return_value=None
    )

    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])

    conn_use = sys.modules["pykiso.auxiliarie.MockAux1"].channel
    conn_not_use = sys.modules["pykiso.auxiliarie.MockAux2"].channel

    proxy_inst._dispatch_command(message, conn_use, remote_id)

    msg, r_id = conn_not_use.queue_out.get()

    assert conn_use.queue_out.qsize() == 0
    assert msg == message
    assert r_id == remote_id


def test_run_command(mocker, cchannel_inst, mock_auxiliaries):
    mocker.patch(
        "pykiso.lib.auxiliaries.proxy_auxiliary.ProxyAuxiliary.run", return_value=None
    )

    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])

    conn_1 = sys.modules["pykiso.auxiliarie.MockAux2"].channel
    conn_2 = sys.modules["pykiso.auxiliarie.MockAux1"].channel

    command_1 = ((), {"msg": b"\x12\x34\x56", "remote_id": 0x512})
    command_2 = ((), {"msg": b"\x12", "remote_id": None})
    command_3 = ((), {"msg": b"\x12\x34\x56\x78", "remote_id": 0x56})

    conn_1.queue_in.put(command_1)
    conn_1.queue_in.put(command_2)
    conn_2.queue_in.put(command_3)

    proxy_inst._run_command()

    assert conn_1.queue_in.qsize() == 0
    assert conn_2.queue_in.qsize() == 0
    assert conn_1.queue_out.qsize() == 1
    assert conn_2.queue_out.qsize() == 2

    msg, r_id = conn_2.queue_out.get()
    assert msg == b"\x12\x34\x56"
    assert r_id == 0x512

    msg, r_id = conn_2.queue_out.get()
    assert msg == b"\x12"
    assert r_id == None

    msg, r_id = conn_1.queue_out.get()
    assert msg == b"\x12\x34\x56\x78"
    assert r_id == 0x56


def test_run(mocker, cchannel_inst, mock_auxiliaries):
    mocker.patch(
        "pykiso.lib.auxiliaries.proxy_auxiliary.AuxiliaryInterface.create_instance",
        return_value=True,
    )
    mocker.patch(
        "pykiso.lib.auxiliaries.proxy_auxiliary.AuxiliaryInterface.delete_instance",
        return_value=True,
    )
    mocker.patch(
        "pykiso.connector.CChannel.cc_receive", return_value=(b"\x12\x34\x56", None)
    )

    proxy_inst = ProxyAuxiliary(cchannel_inst, [*AUX_LIST_NAMES])
    proxy_inst.queue_in.put("create_auxiliary_instance")
    time.sleep(0.015)
    assert proxy_inst.is_instance == True
    proxy_inst.queue_in.put("delete_auxiliary_instance")
    time.sleep(0.015)
    assert proxy_inst.is_instance == False
    proxy_inst.stop()

    conn_1 = sys.modules["pykiso.auxiliarie.MockAux2"].channel
    conn_2 = sys.modules["pykiso.auxiliarie.MockAux1"].channel

    msg, r_id = conn_1.queue_out.get()
    assert msg == b"\x12\x34\x56"
    assert r_id == None
    msg, r_id = conn_2.queue_out.get()
    assert msg == b"\x12\x34\x56"
    assert r_id == None
