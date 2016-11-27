from mess_gen import *
import socket, threading


#chatroom object
class Chatroom(object):

	def __init__(self, chatroom_name, room_ref):
		self.lock = threading.Lock()
		self.chatroom_name = chatroom_name
		self.clients = {}
		self.join_id_seed = 0
		self.room_ref = room_ref

	def join(self, client_name, client, ip, port):
		#generate join id and move on seed
		self.lock.acquire()
		join_id = self.join_id_seed
		self.join_id_seed += 1
		self.lock.release()
		#add client to clients dictionary
		self.clients[join_id] = (client_name, client)
		#send joined message
		message = joined_message(self.chatroom_name, ip, port, self.room_ref, join_id)
		packet = message.encode("utf-8")
		client.send(packet)
		print("Replied: {}".format(message))
		#notify chat that client has joined
		self.spread_message("{} has joined the conversation.".format(client_name))

	def spread_message(self, message):	
		print("Spread to group:\n{}".format(message))
		for k, (c_n, c) in self.clients.items():
			message = chat_message_spread(self.room_ref, c_n, message)
			print(message++"\n")
			packet = message.encode("utf-8")
			c.send(packet)
			
	def leave(self, join_id, client, client_name):
		#send left message
		message = left_message(self.room_ref, join_id)
		packet = message.encode("utf-8")
		client.send(packet)
		print("Relied: {}".format(message))
		#notify chat that the client has left
		message = "{} has left the conversation.".format(client_name)
		self.spread_message(message)
		#only if client is in the chat
		if join_id in self.clients:
			#remove client from chat
			del self.clients[join_id]