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

def send_command_to_hosts(command):
    from .GooglePubSub import ensure_topic, get_publisher, compute_topic_path
    topic = f"{os.environ['GOOGLE_RESOURCE_PREFIX']}-host-commands"        
    ensure_topic(topic)
    publisher = get_publisher()
    s = json.dumps(dict(command=command))
    log.debug(f"Sent command {s} on top {topic}")
    publisher.publish(compute_topic_path(topic), s.encode('utf8'))
    

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
        
    def run(self, args):
        current_devices = self.get_packet_hosts()
        
        rows=[["hostname","id", "IP"]]
        for h in current_devices:
            rows.append([f"{h['hostname']}",f"{h['id']}", f"{h['ip_addresses'][0]['address']}"])
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
        super(PacketCreate, self).__init__(parent_subparser=parent, name="create", help="Create hosts on packet.com")

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
        from .GooglePubSub import ensure_subscription_exists, get_subscriber, compute_subscription_path, delete_subscription
        from .GooglePubSub import ensure_topic, get_publisher, compute_topic_path
        from uuid import uuid4 as uuid
        import datetime
        import google.api_core

        class Host(object):
            def __init__(self,id, name, status, sw_hash, ipaddr):
                self.id=id
                self.name = name
                self.last_heart_beat = datetime.datetime.utcnow()
                self.status = status
                self.last_status_change = datetime.datetime.utcnow()
                self.sw_hash = sw_hash
                self.ipaddr = ipaddr

            def touch(self, when):
                self.last_heart_beat = max(when, self.last_heart_beat)

            def update_status(self, status):
                if self.status != status:
                    self.last_status_change = datetime.datetime.utcnow()
                    self. status = status

            def update_software(self, sw_hash):
                self.sw_hash = sw_hash

        if not args.verbose:
            os.system("clear")
            
        try:
            sub_name = f"top-listener-{uuid()}"
            ensure_subscription_exists(topic=f"{os.environ['GOOGLE_RESOURCE_PREFIX']}-host-events",
                                       subscription=sub_name,
                                       message_retention_duration=Duration(seconds=30*60),
                                       expiration_policy=ExpirationPolicy(ttl=Duration(seconds=24*3600)))

            subscriber = get_subscriber()
            sub_path = compute_subscription_path(sub_name)

            send_command_to_hosts("send-heartbeat")
            hosts = dict()
            while True:
                try:
                    r = subscriber.pull(sub_path, max_messages=5, timeout=3)
                except google.api_core.exceptions.DeadlineExceeded as e: 
                    log.debug(e)
                    pass
                else:
                    for r in r.received_messages:
                        log.debug(f"Got {r.message.data.decode('utf8')}")
                        d = json.loads(r.message.data.decode("utf8"))
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
                                                      sw_hash=d.get('sw_git_hash', " "*8),
                                                      ipaddr=ip_addr)
                            else:
                                host = hosts[d['id']]
                                stamp = eval(d['time'])
                                if stamp > host.last_heart_beat:
                                    host.touch(stamp)
                                    host.update_status(d['status'])
                                    host.update_software(d.get('sw_git_hash', " "*8))
                        except KeyError as e:
                            log.warning(f"Got strange message: {d} ({e})")
                            raise
                        subscriber.acknowledge(sub_path, [r.ack_id])
                rows = [["host", "IP", "server-ID", "MIA", "status", "for", "SW"]]
                for n, h in sorted(hosts.items(), key=lambda kv: kv[1].name):
                    rows.append([h.name, h.ipaddr, h.id[:8], datetime.datetime.utcnow()-h.last_heart_beat, h.status, datetime.datetime.utcnow()-h.last_status_change, h.sw_hash[:8]])

                if not args.verbose:
                    os.system("clear")
                sys.stdout.write(columnize(rows, divider=" "))
                sys.stdout.flush()
                if args.once:
                    break
        except KeyboardInterrupt:
            return 0
        finally:
            try:
                delete_subscription(sub_name)
            except:
                pass

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
                    level=log.DEBUG if args.verbose else log.INFO)

    return args.func(args)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

