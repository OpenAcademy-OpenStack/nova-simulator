# vim: tabstop=4 shiftwidth=4 softtabstop=4 #
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
:mod:`simulator` -- Fake driver that simulates errors and cluster capacity
===========================================================================
"""

import logging
import random
import time

import fake
from nova import exception
from oslo.config import cfg

LOG = logging.getLogger(__name__)
CONF = cfg.CONF

simulator_opts = [
    cfg.FloatOpt('simulator_delay_probability',
                 default=0.0,
                 help='Delay a request issued to the SimulatorDriver with the'
                      'specified probability'),
    cfg.IntOpt('simulator_delay_ms',
               default=0,
               help='Delay a request by the specified number of milliseconds'),
    cfg.FloatOpt('simulator_error_probability',
                 default=0.0,
                 help='Inject a NovaException to the SimulatorDriver with the'
                      'specified probability'),
    ]

CONF.register_opts(simulator_opts)

CONF = cfg.CONF
CONF.import_opt('host', 'nova.netconf')
CONF.import_opt('simulator_error_probability', 'nova.virt.simulator')
CONF.import_opt('simulator_delay_probability', 'nova.virt.simulator')
CONF.import_opt('simulator_delay_ms', 'nova.virt.simulator')

to_simulate = ['spawn', 'live_snapshot', 'snapshot', 'reboot',
               'resume_state_on_host_boot', 'rescue', 'unrescue',
               'migrate_disk_and_power_off', 'finish_revert_migration',
               'power_off', 'power_on', 'soft_delete', 'restore',
               'pause', 'unpause', 'suspend', 'resume', 'destroy',
               'swap_volume', 'finish_migration', 'finish_migration']


def inject(p):
    return random.random() < p


def simulate(method):
    if callable(method) and method.__name__ not in to_simulate:
        return method

    if inject(CONF.simulator_delay_probability):
        delay_duration = random.random() * CONF.simulator_delay_ms / 1000.0
        LOG.debug("Simulator injecting delay of %s ms" % delay_duration)
        time.sleep(delay_duration)

    if inject(CONF.simulator_error_probability):
        LOG.debug("Simulator injecting NovaException")
        raise exception.NovaException

    return method


class SimulatorDriver(fake.FakeDriver):
    def __init__(self, virtapi, read_only=False):
        super(SimulatorDriver, self).__init__(virtapi, read_only)

        nodes = []
        nodes.append(CONF.host)
        fake.set_nodes(nodes)
        self.host_status_base = {
            'vcpus': 2,
            'memory_mb': 512,
            'local_gb': 6000,
            'vcpus_used': 0,
            'memory_mb_used': 0,
            'local_gb_used': 0,
            'hypervisor_type': 'fake',
            'hypervisor_version': '1.0',
            'hypervisor_hostname': CONF.host,
            'cpu_info': {},
            'disk_available_least': 5000,
        }
        self.host_resource = {
            'vcpus': 1,
            'memory_mb': 1024,
            'memory_mb_used': 0,
            'local_gb': 1028,
            'vcpus_used': 0,
            'memory_mb_used': 0,
            'local_gb_used': 0,
            'hypervisor_type': 'fake',
            'hypervisor_version': '1.0',
            'hypervisor_hostname': CONF.host,
            'disk_available_least': 0,
            'cpu_info': '?'
        }

    def get_available_resource(self, nodename):
        """Updates compute manager resource info on ComputeNode table.

           Since we don't have a real hypervisor, pretend we have lots of
           disk and ram.
        """
        if nodename not in fake._FAKE_NODES:
            return {}

        host = self.fake_get_host_resource()

        return host

    def fake_get_host_resource(self):
        """Any calculation of host resource cost in simulator project "
        in the future shoule be added here"""
        return self.host_resource

    def __getattribute__(self, *args):
        f = super(SimulatorDriver, self).__getattribute__(*args)
        return simulate(f)
