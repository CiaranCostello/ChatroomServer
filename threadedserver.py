import socket
import threading
import sys, argparse, os
from urllib.request import urlopen

std_ID = 13321463

# Message string generators
def joined_message(chatroom_name, room_ref, join_id):
	return "JOINED_CHATROOM: {0}\nSERVER_IP: {1}\nPORT: {2}\nROOM_REF: {3}\nJOIN_ID: {4}".format(chatroom_name, self.ip, self.port, room_ref, join_id)

def error_message(error_code, error_description):
	return "ERROR_CODE: {0}\nERROR_DESCRIPTION: {1}".format(error_code, error_description)

def left_message(room_ref, join_id):
	return "LEFT_CHATROOM: {0}\nJOIN_ID: {1}".format(room_ref, join_id)

def disconnect_message(client_name):
	return "DISCONNECT: 0\nPORT: 0\nCLIENT_NAME: {0}".format(client_name)

def chat_message_spread(room_ref, client_name, message):
	return "CHAT: {}\nCLIENT_NAME: {}\nMESSAGE: {}\n\n".format(room_ref, client_name, message)

#takes "SOMETHING: parameter" and returns " parameter"
def parameter(s):
	return s.split(':')[1]

class Server(object):

	max_workers = 16

	def __init__(self, host, port, ip):
		#bind to port and host specified
		self.host = host
		self.port = port
		self.socket = socket.socket()
		self.socket.bind((self.host, self.port))
		#create task list and initialise the number of workers
		self.tasks = []
		self.no_of_workers = 0
		self.lock = threading.Lock()
		self.ip = ip
		self.running = True
		self.room_ref_seed = 0
		self.rooms = {}
		self.roomsLock = threading.Lock()

	class chatroom(object):

		def __init__(self, chatroom_name, room_ref):
			self.lock = threading.Lock()
			self.chatroom_name = chatroom_name
			self.clients = {}
			self.join_id_seed = 0
			self.room_ref = room_ref

		def join(self, client_name, client):
			#generate join id and move on seed
			self.lock.aquire()
			join_id = self.join_id_seed
			self.join_id_seed += 1
			self.lock.release()
			#add client to clients dictionary
			self.clients[join_id] = (client_name, client)
			#send joined message
			packet = joined_message(self.chatroom_name, self.room_ref, join_id).encode("utf-8")
			client.send(packet)
			#notify chat that client has joined
			self.spread_message(client_name, "{} has joined the conversation.".format(client_name))

		def spread_message(self, sender, message):
			packet = chat_message_spread(self.room_ref, sender, message).encode("utf-8")
			self.send_packet(packet)

		def send_packet(self, packet):
			for k, (c_n, c) in self.clients:
				c.send(packet)		
				
		def leave(self, join_id, client):
			#send left message
			packet = left_message(self.room_ref, join_id).encode("utf-8")
			client.send(packet)
			#only if client is in the chat
			if join_id in self.clients:
				(client_name, _) = self.clients[join_id]
				del self.clients[join_id]
				#notify chat that the client has left
				message = "{} has left the conversation.".format(client_name)
				self.spread_message(client_name, message)




	def listen(self):
		self.socket.listen(5)
		while self.running:
			print("Waiting for connections")
			client, address = self.socket.accept()
			print("Received connection from {0}".format(address))
			#add connection to task list
			self.tasks.append((client, address))
			#if we aren't at max threads and there are a few tasks waiting in the queue start another worker
			self.lock.acquire()
			if(self.no_of_workers < self.max_workers and len(self.tasks) >= 0):
				print("Creating worker")
				self.no_of_workers +=1
				threading.Thread(target = self.Worker, daemon = True).start()
			self.lock.release()


	def Worker(self):
		print("Started worker. There are now {0} workers".format(self.no_of_workers))
		while len(self.tasks) > 0:
			(client, (host, port)) = self.tasks.pop(0)
			size = 1024
			while True:
				try:
					data = client.recv(size)
					data = data.decode("utf-8")
					if data:
						print("Received message: {0}".format(data))
						# Set the response to echo back the recieved data
						if "HELO" in data:
							print("Handling HELO message.")
							print("Adding student id.")
							response = "{3}IP:{0}\nPort:{1}\nStudentID:{2}\n".format(self.ip, self.port, std_ID, data)
							client.send(response.encode("utf-8"))
						elif data == "KILL_SERVICE\n":
							print("Calling Stop()")
							self.Stop()
						elif "JOIN_CHATROOM:" in data:
							#handle a request to join a chatroom
							print("Handling JOIN_CHATROOM message.")
							#parse
							chatroom_name = parameter(data.split("\n")[0])
							print(chatroom_name)
							client_name = parameter(data.split("\n")[3])
							print(client_name)
							#check if chatroom exists
							exists = False
							for k, v in self.rooms:
								#join
								if v.chatroom_name is chatroom_name:
									v.join(client_name, client)
									exists = True
							if not exists:
								#get room ref
								self.roomsLock.acquire()
								room_ref = self.room_ref_seed
								self.room_ref_seed += 1
								self.roomsLock.release()
								#create new chatroom
								cr = chatroom(chatroom_name, room_ref)
								self.rooms[room_ref] = cr
								#join the aforesaid chatroom
								cr.join(client_name, client)
							print("Joined chatroom.")

						elif "LEAVE_CHATROOM:" in data:
							print("Handling LEAVE_CHATROOM message.")
							#handle a request to leave a chatroom
							#parse
							room_ref = parameter(data.split('\n')[0])
							join_id = parameter(data.split('\n')[1])
							client_name = parameter(data.split('\n')[3])
							#leave chatroom
							self.rooms[room_ref].leave(join_id, client)

						elif "DISCONNECT:" in data:
							print("Handling DISCONNECT message.")
							#handle a request to disconnect from server ie. kill socket connection and worker thread
							#parse
							client_name = parameter(data.split('\n')[2])
							print("Calling Stop")
							self.Stop()
						elif "CHAT:" in data:
							print("Handling CHAT message.")
							#send chat message to all members of the chat
							#parse
							room_ref = parameter(data.split('\n')[0])
							join_id = parameter(data.split('\n')[1])
							client_name = parameter(data.split('\n')[2])
							message = parameter(data.split('\n')[3])
							#spread message
							self.rooms[room_ref].spread_message(client_name, message)
						print("Handled packet")
					else:
						raise error('Client disconnected')
				except e:
					print(e)
					client.close()
					print("Got to break")
					break
		print("Worker dying")
	
	def Stop(self):
		self.running = False
		print("Running set to false")
		socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((self.host, self.port))
		self.socket.close()

def clargs():
	parser = argparse.ArgumentParser(description='TCP thread pool server.')
	parser.add_argument('-p', '--port', type=int, required=True, help='Port to connect to')
	parser.add_argument('-o', '--host', required=False, help='Host name to send get request to')
	parser.add_argument('-i', '--ipAddress', required=True, help='IP address of host')
	return parser.parse_args()

if __name__ == '__main__':
	args = clargs()
	s = Server('', args.port, args.ipAddress)
	try:
		s.listen()
	except KeyboardInterrupt:
		print("Ctrl C - Stopping server")
		sys.exit(1)
	