#!/usr/bin/env python
# -*-coding:utf-8-*-

import socket
import json
import time
import sys

RECV_SIZE = 4096


class Client(object):
    def __init__(self,
                 server,
                 timeout=None):
        self.sock = None
        self.server = server
        self.timeout = timeout

    def _connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(self.server)
        sock.settimeout(self.timeout)
        self.sock = sock

    def _close(self):
        if self.sock:
            self.sock.close()
        self.sock = None

    def get(self, name):
        name += b''
        cmd = name + b'\r\n'
        if not self.sock:
            self._connect()
        self.sock.sendall(cmd)

        buf = b''
        result = []
        while True:
            buf, line = parseline(self.sock, buf)
            if line == b'END':
                self._close()
                return result
            result.append(line)


def parseline(sock, buf):
    chunks = []
    last_char = b''

    while True:
        if last_char == b'\r' and buf[0:1] == b'\n':
            # Strip the last character from the last chunk.
            chunks[-1] = chunks[-1][:-1]
            return buf[1:], b''.join(chunks)
        elif buf.find(b'\r\n') != -1:
            before, sep, after = buf.partition(b"\r\n")
            chunks.append(before)
            return after, b''.join(chunks)

        if buf:
            chunks.append(buf)
            last_char = buf[-1:]

        try:
            buf = sock.recv(RECV_SIZE)
        except IOError as e:
            raise e


def mget_stats():
    """
        @return: memcache stats dict
    """
    c = Client((host, port), timeout=5)
    stat = c.get("stats")

    stats = {}
    for i in stat:
        stat_name = i.split()[1]
        stat_value = i.split()[2]
        stats[stat_name] = stat_value
    data = []
    stats['usage'] = '%.2f' % float(100 * float(stats['bytes']) / float(stats['limit_maxbytes']))
    ###服务刚起是，访问可能为0##
    if (float(stats['get_hits']) + float(stats['get_misses'])) != 0:
        stats['get_hit_ratio'] = '%.2f' % float(100 * float(stats['get_hits']) /
                                                (float(stats['get_hits']) + float(stats['get_misses'])))
    else:
        stats['get_hit_ratio'] = '0.0'
    stats_list = ['usage', 'get_hit_ratio', 'evictions']
    for key in stats_list:
        stats_dict = {
            'metric': '%s.total.%s' % (metric, key),
            'endpoint': endpoint,
            'timestamp': timestamp,
            'step': step,
            'value': stats[key],
            'counterType': 'GAUGE',
            'tags': 'port=11211,metric=memcache'
        }
    data.append(stats_dict)
    return data


def mget_slabs():
    """
          @return: memcache slabs list
    """
    c = Client((host, port), timeout=5)
    slabs = c.get("stats slabs")

    data = []
    ##slabs返回值倒数第二个是
    num_slabs = int(slabs[-2].split()[2])
    ###每个slab有16个元素的返回值，循环处理
    for n in range(num_slabs):
        slabs_one = slabs[16 * n:16 * (n + 1)]
        slab_name = slabs_one[0].split(':')[0].split()[-1]
        slab_pages_k = slabs_one[2].split()[1].split(':')[1]
        slab_pages_v = slabs_one[2].split()[-1]
        slab_pages_dict = {
            'metric': '%s.slabs.slab_%s.%s' % (metric, slab_name, slab_pages_k),
            'endpoint': endpoint,
            'timestamp': timestamp,
            'step': step,
            'value': slab_pages_v,
            'counterType': 'GAUGE',
            'tags': 'port=11211,metric=memcache'
        }
        slab_used_percent_name = slabs_one[4].split()[1].split(':')[1]
        slab_used_percent_value = 100 * (float(slabs_one[4].split()[-1]) / float(slabs_one[3].split()[-1]))
        slab_used_percent_dict = {
            'metric': '%s.slabs.slab_%s.%s_percent' % (metric, slab_name, slab_used_percent_name),
            'endpoint': endpoint,
            'timestamp': timestamp,
            'step': step,
            'value': '%.2f' % slab_used_percent_value,
            'counterType': 'GAUGE',
            'tags': 'port=11211,metric=memcache'
        }

        data.append(slab_pages_dict)
        data.append(slab_used_percent_dict)
    return data


def main():
    mem_data = mget_stats() + mget_slabs()
    json.dump(mem_data, sys.stdout)

if __name__ == "__main__":
    host = ''
    port = 11211

    timestamp = int(time.time())
    step = 60
    endpoint = 'memcache-monitor'
    metric = 'memcache'
    main()
