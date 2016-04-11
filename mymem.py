#!/usr/bin/env python
#-*-coding:utf-8-*-
import socket
import re,json

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
	c = Client((host,port), timeout=5)
	#print c.get("stats slabs")
	_stat_regex = re.compile(ur"STAT (.*) ([0-9]+\.?[0-9]*)")
	stat = c.get("stats")
	stats={}
	for i in stat:
		k=re.compile(ur"STAT (.*) ([0-9]+\.?[0-9]*)").findall(i)[0][0]
		v=re.compile(ur"STAT (.*) ([0-9]+\.?[0-9]*)").findall(i)[0][1]
		stats[k]=v
		
	return stats



def  mget_slabs():
	c = Client((host,port), timeout=5)
	#print c.get("stats slabs")
	_stat_regex = re.compile(ur"STAT (.*) ([0-9]+\.?[0-9]*)")
	slab = c.get("stats slabs")
	slabs={}
	slabs_num=slab.count('total_pages')
	for i in slab:
		kv=re.compile(ur'(STAT \d+:\w+) (\d+)').findall(i)
		for j in 'total_page','total_chunks','used_chunks' :
			if str(kv).count(j):
				k=re.compile(ur'(STAT \d+:\w+) (\d+)').findall(i)[0][0]
				slabs[k]=re.compile(ur'(STAT \d+:\w+) (\d+)').findall(i)[0][1]
	return slabs


def main():
	data=[]
	stats=Mget_stats()
	stats['usage'] = str(100 * float(stats['bytes']) / float(stats['limit_maxbytes']))
	try:
		stats['get_hit_ratio'] = str(100 * float(stats['get_hits']) / (float(stats['get_hits']) + float(stats['get_misses'])))
	except ZeroDivisionError:
		stats['get_hit_ratio'] = '0.0'
	#print stats['get_hit_ratio']
	i={'get_hit_ratio':stats['get_hit_ratio']}
	data.append(i)
	slabs=Mget_slabs()
	print slabs
	print  json.dumps(data)
if __name__ == "__main__":
	port = 11211
	main()
