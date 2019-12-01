import logging as log
import json
import platform
import argparse
import sys
import os

import re
from .SubCommand import SubCommand
import packet
from .Columnize import columnize

class PacketCommand(SubCommand):
    def __init__(self, *args, **kwargs):
        super(PacketCommand, self).__init__(*args, **kwargs)
        self.token = os.environ["PACKET_AUTH_TOKEN"]
        self.project = os.environ["PACKET_PROJECT_ID"]
        self.manager = packet.Manager(auth_token=self.token)

        
class PacketList(PacketCommand):
    def __init__(self, parent):
        super(PacketList, self).__init__(parent_subparser=parent, name="ls", help="List hosts")

    def run(self, args):
        params = {
            'per_page': 50
        }
        current_devices = self.manager.list_devices(project_id=self.project, params=params)

        rows=[["hostname","id"]]
        for h in current_devices:
            rows.append([f"{h['hostname']}",f"{h['id']}"])
        sys.stdout.write(columnize(rows))
        
class PacketDelete(PacketCommand):
    def __init__(self, parent):
        super(PacketDelete, self).__init__(parent_subparser=parent, name="rm", help="List hosts")
        self.parser.add_argument("device", nargs="+", help="Device id")

    def run(self, args):
        for id in args.device:
            log.info(f"Deleting '{id}'")
            try:
                device = self.manager.get_device(id)
                device.delete()
            except packet.baseapi.Error as e:
                log.error(f"{e}")
                
                
class PacketCreate(PacketCommand):
    def __init__(self, parent):
        super(PacketCreate, self).__init__(parent_subparser=parent, name="create", help="Manipulate packet.com hosts")

    def run(self, args):
        import subprocess
        params = {
            'per_page': 50
        }
        current_devices = self.manager.list_devices(project_id=self.project, params=params)
        basename="node"
        maxn = 0
        for d in current_devices:
            log.debug(f"Found device: {d['hostname']}")
            m = re.match(f"{basename}-(\d+)", d['hostname'])
            if m:
                maxn = max(maxn, int(m.group(1)))
                log.debug(f"{d['hostname']} matches pattern.  new max = {maxn}")
        hostname = f"{basename}-{maxn+1}"

        log.info(f"Creating host '{hostname}'")
        userdata = subprocess.check_output(['show_boot.sh']).decode("utf8")

        log.debug(f"Usedata: {userdata}")

        device = self.manager.create_device(project_id=self.project,
                                            hostname=hostname,
                                            plan='x1.small.x86', facility='any',
                                            operating_system='ubuntu_16_04',
                                            userdata=userdata)
        log.info(f"Created device {device}")


def main(argv=None):
    """
    This is lab runneer host managemen tool.
    """
    parser = argparse.ArgumentParser(description='Control runner hosts')
    parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")

    subparsers = parser.add_subparsers(help='sub-command help')

    PacketCreate(subparsers)
    PacketList(subparsers)
    PacketDelete(subparsers)
    
    if argv == None:
        argv = sys.argv[1:]
        
    args = parser.parse_args(argv)
    if not "func" in args:
        parser.print_help()
        sys.exit(1)
    
    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                    level=log.DEBUG if args.verbose else log.INFO)

    return args.func(args)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

