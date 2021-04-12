import logging as log
import json
import platform
import argparse
import sys
import os

import re
from .SubCommand import SubCommand
import packet
from .Columnize import columnize, format_time_delta
from .PubSub import Publisher, Subscriber

def send_command_to_hosts(command):
    publisher = Publisher(os.environ['HOST_COMMAND_TOPIC'])
    s = json.dumps(dict(command=command))
    publisher.publish(s)
    
class HostControl(SubCommand):
    def __init__(self, parent):
        super(HostControl, self).__init__(parent_subparser=parent,
                                          name="cmd",
                                          help="Control build servers processes")
        
        self.parser.add_argument("command", help="Command to send")
        
    def run(self, args):
        send_command_to_hosts(args.command)
        

class PacketCommand(SubCommand):
    def __init__(self, *args, **kwargs):
        super(PacketCommand, self).__init__(*args, **kwargs)
        self.token = os.environ["PACKET_AUTH_TOKEN"]
        self.project = os.environ["PACKET_PROJECT_ID"]
        self.manager = packet.Manager(auth_token=self.token)


    def get_packet_hosts(self):
        params = {
            'per_page': 50
        }
        return self.manager.list_devices(project_id=self.project, params=params)

    
class PacketList(PacketCommand):
    def __init__(self, parent):
        super(PacketList, self).__init__(parent_subparser=parent, name="ls", help="List hosts")
        self.parser.add_argument("--ip", action='store_true', help="list ips")

    def run(self, args):
        current_devices = self.get_packet_hosts()

        if args.ip:
            for h in current_devices:
                sys.stdout.write(f"{h['ip_addresses'][0]['address']}\n")
            return
        
        rows=[["hostname","id", "IP"]]
        for h in current_devices:
            rows.append([f"{h['hostname']}",f"{h['id']}", f"{h['ip_addresses'][0]['address']}"])
        sys.stdout.write(columnize(rows))

        
class PacketDelete(PacketCommand):
    def __init__(self, parent):
        super(PacketDelete, self).__init__(parent_subparser=parent, name="rm", help="List hosts")
        self.parser.add_argument("device", nargs="+", help="Device id")

    def run(self, args):
        current_devices = self.get_packet_hosts()
        by_name = {x.hostname : x for x in current_devices}
        by_id = {x.id : x for x in current_devices}
        for id in args.device:
            log.info(f"Deleting '{id}'")
            try:
                if id in by_id:
                    device = self.manager.get_device(id)
                    device.delete()
                elif id in by_name:
                    device = self.manager.get_device(by_name[id].id)
                    device.delete()
            except packet.baseapi.Error as e:
                
                log.error(f"{e}")
                
                
class PacketCreate(PacketCommand):
    def __init__(self, parent):
        super(PacketCreate, self).__init__(parent_subparser=parent, name="create", help="Create hosts on packet.com")
        self.parser.add_argument("name", nargs="?", help="server name")
        
    def run(self, args):
        import subprocess
        params = {
            'per_page': 50
        }
        current_devices = self.manager.list_devices(project_id=self.project, params=params)
        if args.name:
            basename=args.name
            if basename in current_devices:
                raise Exception(f"Host '{basename}' already exists.")
            hostname = basename
        else:
            basename=os.environ['GOOGLE_RESOURCE_PREFIX']
            maxn = 0
            for d in current_devices:
                log.debug(f"Found device: {d['hostname']}")
                m = re.match(f"{basename}-(\d+)", d['hostname'])
                if m:
                    maxn = max(maxn, int(m.group(1)))
                    log.debug(f"{d['hostname']} matches pattern.  new max = {maxn}")
            hostname = f"{basename}-{maxn+1}"

        log.warn(f"Creating host '{hostname}':  {os.environ['IN_DEPLOYMENT']}")
        userdata = subprocess.check_output(['show_boot.sh']).decode("utf8")

        log.debug(f"Usedata: {userdata}")

        device = self.manager.create_device(project_id=self.project,
                                            hostname=hostname,
                                            plan='x1.small.x86', facility='any',
                                            operating_system='ubuntu_16_04',
                                            userdata=userdata)
        log.info(f"Created device {device}")
        log.warn(f"Created host '{hostname}':  {os.environ['IN_DEPLOYMENT']}")

class HostTop(PacketCommand):
    def __init__(self, parent):
        super(HostTop, self).__init__(parent_subparser=parent,
                                      name="top",
                                      help="Track hosts")
        self.parser.add_argument('--once', action='store_true', default=False, help="Just collect stats once and exit")

    def run(self, args):
        log.debug(f"Running hosts with {args}")
        from google.cloud.pubsub_v1.types import Duration
        from google.cloud.pubsub_v1.types import ExpirationPolicy
        from uuid import uuid4 as uuid
        import datetime
        import google.api_core

        
        class Host(object):
            def __init__(self,id, name, status, git_hash, ipaddr, docker_image, load):
                self.id=id
                self.name = name
                self.last_heart_beat = datetime.datetime.utcnow()
                self.status = status
                self.last_status_change = datetime.datetime.utcnow()
                self.git_hash = git_hash
                self.ipaddr = ipaddr
                self.docker_image =docker_image
                self.load =load

            def touch(self, when):
                self.last_heart_beat = max(when, self.last_heart_beat)

            def update_status(self, status):
                if self.status != status:
                    self.last_status_change = datetime.datetime.utcnow()
                    self.status = status

            def update_software(self, git_hash, docker_image):
                self.git_hash = git_hash
                self.docker_image = docker_image

        countdown = 3
            
        if not args.verbose:
            os.system("clear")

        try:
            with Subscriber(topic=os.environ['HOST_EVENTS_TOPIC'], prefix=os.environ["TESTING_GOOGLE_RESOURCE_PREFIX"]) as testing_subscriber:
                with Subscriber(topic=os.environ['HOST_EVENTS_TOPIC'], prefix=os.environ["DEPLOYED_GOOGLE_RESOURCE_PREFIX"]) as deployed_subscriber:
                    send_command_to_hosts("send-heartbeat")
                    hosts = dict()
                    while True:
                        messages = []
                        
                        try:
                            messages += testing_subscriber.pull(max_messages=5, timeout=3)
                        except google.api_core.exceptions.DeadlineExceeded as e: 
                            log.debug(e)
                            pass
                        
                        try:
                            messages += deployed_subscriber.pull(max_messages=5, timeout=3)
                        except google.api_core.exceptions.DeadlineExceeded as e: 
                            log.debug(e)
                            pass
                        
                        else:
                            for r in messages:
                                d = json.loads(r)
                                try:
                                    if d['id'] not in hosts:
                                        current_devices = self.get_packet_hosts()
                                        device_map = {x.hostname : x for x in current_devices}

                                        if d['node'] in device_map:
                                            ip_addr = device_map[d['node']]['ip_addresses'][0]['address']
                                        else:
                                            ip_addr = "unknown"
                                        hosts[d['id']] = Host(id=d['id'],
                                                              name=d['node'],
                                                              status=d['status'],
                                                              git_hash=d.get('sw_git_hash', " "*8),
                                                              ipaddr=ip_addr,
                                                              docker_image=d.get('docker_image', "unknown"),
                                                              load=d.get("load", "unknown"))
                                    else:
                                        host = hosts[d['id']]
                                        stamp = eval(d['time'])
                                        if stamp > host.last_heart_beat:
                                            host.touch(stamp)
                                            host.update_status(d['status'])
                                            host.update_software(git_hash=d.get('sw_git_hash', " "*8),
                                                                 docker_image=d.get('docker_image', "unknown"))
                                            host.load = d.get("load", "unknown")
                                except KeyError as e:
                                    log.warning(f"Got strange message: {d} ({e})")
                                    raise
                        for n, h in list(hosts.items()):
                            if datetime.datetime.utcnow() - h.last_heart_beat > datetime.timedelta(minutes=30):
                                del hosts[n]

                        rows = [["host", "IP", "server-ID", "MIA", "status", "for", "SW", "Docker", "load"]]
                        for n, h in sorted(hosts.items(), key=lambda kv: kv[1].name):
                            rows.append([h.name, h.ipaddr, h.id[:8],
                                         format_time_delta(datetime.datetime.utcnow()-h.last_heart_beat),
                                         h.status,
                                         format_time_delta(datetime.datetime.utcnow()-h.last_status_change),
                                         h.git_hash[:8],
                                         h.docker_image,
                                         h.load
                            ])

                        if not args.verbose:
                            os.system("clear")
                        sys.stdout.write(f"Namespace: {os.environ['GOOGLE_RESOURCE_PREFIX']}; {os.environ['IN_DEPLOYMENT']} in {os.environ['CLOUD_MODE']}; DOCKER: {os.environ.get('THIS_DOCKER_IMAGE', 'unknown')}\n")
                        sys.stdout.write(columnize(rows, divider=" "))
                        sys.stdout.flush()
                        countdown -= 1
                        if args.once and countdown == 0:
                            break
        except KeyboardInterrupt:
            return 0


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

    HostControl(subparsers)
    HostTop(subparsers)

    if argv == None:
        argv = sys.argv[1:]
        
    args = parser.parse_args(argv)
    if not "func" in args:
        parser.print_help()
        sys.exit(1)
    
    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                    level=log.DEBUG if args.verbose else log.WARN)

    return args.func(args)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

