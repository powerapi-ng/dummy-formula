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
Main module of Dummy
 Initialize the system from the configuration and initiate the run
"""


import logging
import signal
import sys
import json
from typing import Dict
import datetime

from powerapi import __version__ as powerapi_version
from powerapi.dispatcher import DispatcherActor, RouteTable
from powerapi.cli import ConfigValidator
from powerapi.cli.tools import (
    ComponentSubParser,
    ReportModifierGenerator,
    PullerGenerator,
    PusherGenerator,
    CommonCLIParser,
)
from powerapi.message import DispatcherStartMessage
from powerapi.report import PowerReport, ProcfsReport
from powerapi.dispatch_rule import (
    PowerDispatchRule,
    PowerDepthLevel,
    ProcfsDispatchRule,
    ProcfsDepthLevel,
)
from powerapi.filter import Filter
from powerapi.actor import InitializationException
from powerapi.supervisor import Supervisor


from dummy import __version__ as dummy_version
from dummy.actor import (DummyFormulaActor,
                         DummyFormulaValues)
from dummy.context import DummyFormulaConfig


def generate_dummy_parser() -> ComponentSubParser:
    """
    Construct and returns the VirtuamWatts cli parameters parser.
    :return: Dummy cli parameters parser
    """
    parser = ComponentSubParser("dummy")

    # Add the configuration arguments you'll need to the parser

    parser.add_argument(
        "arg1",  # name of the arg
        help="help on arg1",  # help to display when --help is used
        type=None,  # type expected
        default=None,  # Default value if not specified
    )

    return parser


def filter_rule(_):
    """
    No rule is needed
    """
    return True


def run_dummy(args) -> None:
    """
    Run PowerAPI with the Dummy formula.
    :param args: CLI arguments namespace
    """
    fconf = args

    logging.info(
        "Dummy version %s using PowerAPI version %s",
        dummy_version,
        powerapi_version,
    )

    route_table = RouteTable()
    route_table.dispatch_rule(
        PowerReport, PowerDispatchRule(PowerDepthLevel.SENSOR, primary=True)
    )
    route_table.dispatch_rule(
        ProcfsReport, ProcfsDispatchRule(ProcfsDepthLevel.SENSOR,
                                         primary=False)
    )

    report_filter = Filter()

    report_modifier_list = ReportModifierGenerator().generate(fconf)

    # Run the actor system supervisor
    supervisor = Supervisor(args["verbose"])

    def term_handler(_, __):
        supervisor.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, term_handler)
    signal.signal(signal.SIGINT, term_handler)
    try:
        logging.info("Starting Dummy actors...")

        # Generate the pushers
        power_pushers = {}
        pushers_info = PusherGenerator().generate(args)
        for pusher_name in pushers_info:
            pusher_cls, pusher_start_message = pushers_info[pusher_name]
            power_pushers[pusher_name] = supervisor.launch(
                pusher_cls, pusher_start_message
            )

        # Create the Dummy formula from config
        formula_config = DummyFormulaConfig(fconf["arg1"])

        # Instantiate the dispatcher that will provide reports to the formula
        dispatcher_start_message = DispatcherStartMessage(
            "system",
            "cpu_dispatcher",
            DummyFormulaActor,
            DummyFormulaValues(power_pushers, formula_config),
            route_table,
            "cpu",
        )

        # Run the dispatcher
        cpu_dispatcher = supervisor.launch(DispatcherActor,
                                           dispatcher_start_message)
        report_filter.filter(filter_rule, cpu_dispatcher)


        # Generate the puller and launch them
        pullers_info = PullerGenerator(report_filter,
                                       report_modifier_list).generate(
                                           args
                                       )
        for puller_name in pullers_info:
            puller_cls, puller_start_message = pullers_info[puller_name]
            supervisor.launch(puller_cls, puller_start_message)

    # Correctly stop the system if an error occured
    except InitializationException as exn:
        logging.error("Actor initialization error: " + exn.msg)
        supervisor.shutdown()
        sys.exit(-1)


    # The system correctly initialized, start running
    logging.info("Dummy is now running...")
    supervisor.monitor()
    logging.info("Dummy is shutting down...")


def get_config_file(argv):
    """ Retrieve the config file using the cli args"""
    i = 0
    for s in argv:
        if s == "--config-file":
            if i + 1 == len(argv):
                logging.error("config file path needed with argument\
                --config-file")
                sys.exit(-1)
            return argv[i + 1]
        i += 1
    return None


def get_config_from_file(file_path):
    """ Retrieve the config from the config file"""
    config_file = open(file_path, "r")
    return json.load(config_file)


class DummyConfigValidator(ConfigValidator):
    """ Class to validate the config format """
    @staticmethod
    def validate(conf: Dict):
        if not ConfigValidator.validate(conf):
            return False

        # Check that the mandatory arguments are there
        # Assign value to non specifued arguments

        return True


def get_config_from_cli():
    """ Get the config from the cli"""
    parser = CommonCLIParser()
    parser.add_component_subparser(
        "formula", generate_dummy_parser(), "specify the formula to use"
    )
    return parser.parse_argv()


if __name__ == "__main__":
    logging.debug("Loading Dummy' config")

    # Retrieve the config
    config_file_path = get_config_file(sys.argv)
    config = (
        get_config_from_file(config_file_path)
        if config_file_path is not None
        else get_config_from_cli()
    )
    logging.debug("Validate config")

    # Validate the config
    if not DummyConfigValidator.validate(config):
        sys.exit(-1)
    logging.basicConfig(level=logging.WARNING
                        if config["verbose"] else logging.INFO)
    logging.captureWarnings(True)

    logging.debug(str(config))
    logging.debug("Starting Dummy")

    # Start the system
    run_dummy(config)
    sys.exit(0)
