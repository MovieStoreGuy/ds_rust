# --- BEGIN COPYRIGHT BLOCK ---
# Copyright (C) 2016 Red Hat, Inc.
# All rights reserved.
#
# License: GPL (version 3 or any later version).
# See LICENSE for details.
# --- END COPYRIGHT BLOCK ---
#
# Author: William Brown <wibrown@redhat.com>
#

import pytest
from lib389 import DirSrv
from lib389.cli_base import LogCapture
from lib389.instance.setup import SetupDs
from lib389.instance.options import General2Base, Slapd2Base
from lib389._constants import *

import tempfile

INSTANCE_PORT = 54321
INSTANCE_SERVERID = 'standalone'

DEBUGGING = True

class TopologyInstance(object):
    def __init__(self, standalone):
        # For these tests, we don't want to open the instance.
        # instance.open()
        self.standalone = standalone

# Need a teardown to destroy the instance.
@pytest.fixture
def topology(request):

    instance = DirSrv(verbose=DEBUGGING)
    instance.log.debug("Instance allocated")
    args = {SER_PORT: INSTANCE_PORT,
            SER_SERVERID_PROP: INSTANCE_SERVERID}
    instance.allocate(args)
    if instance.exists():
        instance.delete()

    # Create the setupDs
    lc = LogCapture()
    # Give it the right types.
    sds = SetupDs(verbose=DEBUGGING, dryrun=False, log=lc.log)

    # Get the dicts from Type2Base, as though they were from _validate_ds_2_config
    # IE get the defaults back just from Slapd2Base.collect
    # Override instance name, root password, port and secure port.

    general_options = General2Base(lc.log)
    general_options.verify()
    general = general_options.collect()

    slapd_options = Slapd2Base(lc.log)
    slapd_options.set('instance_name', INSTANCE_SERVERID)
    slapd_options.set('port', INSTANCE_PORT)
    slapd_options.set('root_password', PW_DM)
    slapd_options.verify()
    slapd = slapd_options.collect()

    sds.create_from_args(general, slapd, {}, None)
    # Make sure we can connect
    instance.open()

    # Create the example backend with sample entries.
    instance.backends.create(properties= {
        'cn' : ['userRoot'],
        'nsslapd-suffix' : ['dc=example,dc=com'],
        })

    def fin():
        if instance.exists() and not DEBUGGING:
            instance.delete()
    request.addfinalizer(fin)

    return TopologyInstance(instance)


