# Copyright (C) 2021  INRIA
# Copyright (C) 2021  University of Lille
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import pytest

from thespian.actors import ActorExitRequest

from dummy.actor import DummyFormulaActor
from powerapi.formula import CpuDramDomainValues
from powerapi.message import StartMessage, FormulaStartMessage, ErrorMessage, EndMessage, OKMessage
from powerapi.report import Report, PowerReport, ProcfsReport
from powerapi.test_utils.abstract_test import AbstractTestActor, recv_from_pipe
from powerapi.test_utils.actor import system
from powerapi.test_utils.dummy_actor import logger
import datetime
from dummy.actor import DummyFormulaValues
from dummy.context import DummyFormulaConfig


class TestDummyFormula(AbstractTestActor):
    @pytest.fixture
    def actor(self, system):
        actor = system.createActor(DummyFormulaActor)
        yield actor
        system.tell(actor, ActorExitRequest())

    @pytest.fixture
    def actor_start_message(self, logger):
        config = DummyFormulaConfig(1000, datetime.timedelta(500))
        values = DummyFormulaValues({'logger': logger},config)
        return FormulaStartMessage('system', 'test_dummy_formula', values, CpuDramDomainValues('test_device', ('test_sensor', 0, 0)))


    def test_property(self, system,started_actor, dummy_pipe_out):
        # produce the reports
        report1 = None

        # send the reports to the formuma
        system.tell(started_actor,report1)

        # retreive the output reports
        _,msg = recv_from_pipe(dummy_pipe_out,1)

        # test the outputs
        assert True

