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
		self.spread_message(client_name, "{} has joined the conversation.".format(client_name))

	def spread_message(self, client_name, message):	
		print("Spread to group:\n{}".format(message))
		m = chat_message_spread(self.room_ref, client_name, message)
		print(m)
		print("Sent to:")
		for k, (c_n, c) in self.clients.items():
			print(c_n)
			packet = m.encode("utf-8")
			c.send(packet)
			
	def leave(self, join_id, client, client_name):
		#send left message
		message = left_message(self.room_ref, join_id)
		packet = message.encode("utf-8")
		client.send(packet)
		print("Relied: {}".format(message))
		#notify chat that the client has left
		message = "{} has left the conversation.".format(client_name)
		self.spread_message(client_name, message)
		#only if client is in the chat
		self.clients.pop(join_id, None)