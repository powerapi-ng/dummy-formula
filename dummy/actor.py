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

"""
Module that define the virtuallWatts actor
"""

from typing import Dict
from thespian.actors import ActorAddress

from powerapi.formula import AbstractCpuDramFormula, FormulaValues
from powerapi.message import FormulaStartMessage
from powerapi.report import Report

from .context import DummyFormulaConfig


class DummyFormulaValues(FormulaValues):
    """
    Special parameters needed for the formula
    """
    def __init__(self, power_pushers: Dict[str, ActorAddress],
                 config: DummyFormulaConfig):
        """
        :param config: Configuration of the formula
        """
        FormulaValues.__init__(self, power_pushers)
        self.config = config


class DummyFormulaActor(AbstractCpuDramFormula):
    """
    This actor handle the reports for the VirutalWatts formula.
    """

    def __init__(self):
        """
        Instantiate the object.
        It will be initialized later when receiving a start message from the supervisor.
        """
        AbstractCpuDramFormula.__init__(self, FormulaStartMessage)

        self.config = None

    def _initialization(self, start_message: FormulaStartMessage):
        """
        Initialize the object attribute using the start message from the supervisor
        """

        AbstractCpuDramFormula._initialization(self, start_message)
        self.config = start_message.values.config




    def receiveMsg_Report(self, message: Report, _):
        """
        :param message: A  Report received from sender

        You should use one function for each kind of report you want to receive.
        """
        self.log_debug('receive Procfs Report :' + str(message))

        # Treat the report

        # Produce the output report
        report = None

        # Send the report to the pushers
        for name, pusher in self.pushers.items():
            self.log_debug('send ' + str(report) + ' to ' + name)
            self.send(pusher, report)
