from logger import LOG
import sys
import time
import serial_client
import socket
import settings
import threading

lock = threading.Lock()

def service(schedule, id):
	import sys
	import os
	import signal
	try:
		LOG.info('Starting schedule[' + str(id) + ']: ' + str(schedule))
		while run:
			time1 = int(time.time())
			
			with open(schedule['request_file'], mode='rb') as file:
				data_in = file.read()	
			data_out = serial_client.RequestDNP3(data_in, 'Schedule[' + str(id) + ']: request')
			if not data_out:
				continue
			global lock
			with lock:
				if not run:
					return
				global socket_
				socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				server_address = (settings.REMOTE_HOST['ip'], settings.REMOTE_HOST['port'])
				LOG.info('Schedule[' + str(id) + ']: replying to: ' + str(server_address))
				try:
					if schedule['tcp']:
						socket_.connect(server_address)
						sent = socket_.send(data_out)						
					else:
						socket_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
						sent = socket_.sendto(data_out, server_address)	
					if sent != len(data_out):
						raise Exception('Schedule[' + str(id) + ']: not all data sent.')	
				except:
					LOG.exception(sys.exc_info()[0])	
				finally:
					#socket_.shutdown(socket.SHUT_RDWR)
					socket_.close()	
					socket_ = None
			
			period1 = time1 + schedule['period'] - int(time.time())
			if period1 < 0: 
				period1 = 0
			time.sleep(period1) 
	except:
		LOG.exception(sys.exc_info()[0])
		#thread.interrupt_main()
		os.kill(os.getpid(), signal.SIGINT)

run = False
socket_ = None

request_files2thread = {}
	
def start_schedule(schedule):	
	global request_files2thread	
	if schedule['request_file'] in request_files2thread:
		return
	t = threading.Thread(target = service, args = (schedule, len(request_files2thread)))
	t.daemon = True
	t.start()
	request_files2thread[schedule['request_file']] = t
	
def Stop():
	global run
	run = False
	global socket_
	if socket_:
		#socket_.shutdown(socket.SHUT_RDWR)
		socket_.close()	
		socket_ = None
				
def Start():
	global run
	run = True
	for schedule in settings.SCHEDULES:
		start_schedule(schedule)

