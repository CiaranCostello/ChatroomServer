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
