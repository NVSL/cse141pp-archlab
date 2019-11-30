import os
import logging as log
import re
from .SubCommand import SubCommand
import packet

class PacketCmd(SubCommand):
    def __init__(self, parent):
        super(PacketCmd, self).__init__(parent_subparser=parent, name="packet", help="Manipulate packet.com hosts")
        self.parser.add_argument("--foo", help="bar")

    def run(self, args):
        token = os.environ["PACKET_AUTH_TOKEN"]
        project=os.environ["PACKET_PROJECT_ID"]

        manager = packet.Manager(auth_token=token)

        current_devices = manager.list_devices(project_id=project)
        basename="node"
        maxn = 0
        for d in current_devices:
            log.debug(f"Found device: {d['hostname']}")
            m = re.match(f"{basename}-(\d+)", d['hostname'])
            if m:
                maxn = max(maxn, int(m.group(1)))
                log.debug(f"{d['hostname']} matches pattern.  new max = {maxn}")
        hostname = f"{basename}-{maxn+1}"

        device = manager.create_device(project_id=project,
                                       hostname=hostname,
                                       plan='x1.small.x86', facility='any',
                                       operating_system='ubuntu_16_04')
        print(device)
