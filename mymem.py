#!/usr/bin/env python
#-*-coding:utf-8-*-

import socket
import json


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


def  mget_stats():
	"""
		@return: memcache stats dict
	"""
	c = Client((host,port), timeout=5)
	stat = c.get("stats")

	stats={}
	for i in stat:
		k=i.split()[1]
		v=i.split()[2]
		stats[k]=v
		
	data = []
	stats['usage'] = str(100 * float(stats['bytes']) / float(stats['limit_maxbytes']))
	try:
		stats['get_hit_ratio'] = str(100 * float(stats['get_hits']) / (float(stats['get_hits']) + float(stats['get_misses'])))
	except ZeroDivisionError:
		stats['get_hit_ratio'] = '0.0'
	for i in 'usage','get_hit_ratio','evictions':
		dict = {i:stats[i]}
		data.append(dict)
	return data


def  mget_slabs():
	"""
   	   @return: memcache slabs list
	"""
	c = Client((host,port), timeout=5)
	slabs = c.get("stats slabs")
	
	data = []
	num_slabs = int(slabs[-2].split()[2])
	for n in range(num_slabs):
		slabs_one = slabs[16*n:16*(n+1)]
		slab_name = slabs_one[0].split(':')[0]
		k = slabs_one[2].split()[1].split(':')[1]
		v = slabs_one[2].split()[-1]
		dict1 = {k:v}
		k1 = slabs_one[4].split()[1].split(':')[1]
		v1 = 100*(float(slabs_one[4].split()[-1]) / float(slabs_one[3].split()[-1]))
		dict1[k1 + '_percent'] = '%.2f' %v1  
		dict2 = {slab_name:dict1}
		data.append(dict2)
	return data



def main():
	data = mget_stats() + mget_slabs()
	print  json.dumps(data)


if __name__ == "__main__":

	host=''
	port = 11211

	main()
