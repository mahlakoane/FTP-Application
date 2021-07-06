import socket
from ServerDTP import ServerDTP

class ServerPI():
	def __init__(self, serverName, serverPort):
		self.serverDTP = ServerDTP()
		self.user = ""
		self.validUser = False
		self.cmdConn = None
		self.serverName = serverName 
		self.cmdPort = serverPort
		self.isCmdActive = True
		self.supported_commands = ["USER","PASS","PASV","PORT","SYST","RETR","STOR","QUIT",
		"NOOP","TYPE","STRU","MODE","PWD","CWD","LIST"]
		self.noUserCommands = ["USER","NOOP","QUIT","PASS"]
		self.possibleUsers = ["Bohlale","Shaun"]
		self.current_mode = "S"
		self.current_type = "I"   #Image type

#The serverPI is responsible for communicating control FTP replies to client and being able to respond to commands from client.  

	# Functionality to send server replies
	def __send(self, message):
		print(message)
		self.cmdConn.send(message.encode())

	#Functionality to interpret commands from the client using function attributes to attribute commands 
	#to existing functions where they are implemented
	def __execute_command(self, command, argument):
		ftpFunction = getattr(self, command)
		if argument == "":
			ftpFunction()
		else:
			ftpFunction(argument)

	# This function helps determine the length of the command from the incoming client message accurately, 
	# to allow for accurate identification and interpretation.
	def __command_length(self, clientMessage):
		space_pos = clientMessage.find(" ")
		messageSize = 0
		if space_pos == -1:
			messageSize = len(clientMessage) - 2
		else:
			messageSize = space_pos

		return messageSize

#The control connection main function:
	def running(self):
		try:
			while self.isCmdActive:
				clientMessage = self.cmdConn.recv(1024).decode()  # receive control information continuously
				print(clientMessage)
				cmdLen = self.__command_length(clientMessage) # find the length of the command in the message

				#strip the client message to extract the pieces of information carried=> commands and any possible arguments
				command = clientMessage[:cmdLen].strip().upper() 
				argument = clientMessage[cmdLen:].strip()

				if not self.validUser and command not in self.noUserCommands:
					self.__send("530 Please log in\r\n")
					continue
				if command in self.supported_commands:
					self.__execute_command(command, argument)
				else:
					self.__send("502 Command not implemented\r\n")
		except socket.error:
			print("Terminating control connection\r\n")
			self.isCmdActive = False
			self.cmdConn.close()
			self.serverDTP.close_data()

	#This function is responsible for creating the control socket to accept commands and send replies from and to the clientPI
	def open_connection(self):
		cmdSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		cmdSocket.bind((self.serverName,self.cmdPort))
		cmdSocket.listen(1)
		print("Server is listening for client")
		self.cmdConn, addr = cmdSocket.accept()  #on runnning this function, execution will not go past this line if no connections from clients are made.
		print("Connected to: " + str(addr))
		self.isCmdActive = True
		self.__send("220 Successful control connection\r\n")

	# Server functionality for handling FTP commands that come from the client

	# username handler
	def USER(self, userName):
		if userName in self.possibleUsers: # user is validated here
			self.user = userName
			self.serverDTP.set_user(self.user) 
			self.__send("331 Please enter password " + userName + "\r\n")
		else:
			self.validUser = False
			self.__send("332 Invalid user\r\n")

	#password handler
	def PASS(self, password = "IdeallySecurePassword"):
		if self.user == "":
			self.__send("530 Please log in\r\n")
			return
		if self.serverDTP.is_password_valid(password):
			self.validUser = True
			self.__send("230 Welcome " + self.user + "\r\n")
		else:
			self.validUser = False
			self.__send("501 Invalid password\r\n")

	# Handling the command to create a passive data connection between server and client.
	def PASV(self):
		try:
			self.serverDTP.listen_passive(self.serverName)
			self.__send("227 Entering Passive connection mode " + self.serverDTP.server_address_passive(self.serverName) + "\r\n")
			self.serverDTP.accept_connection_passive()
		except:
			self.__send("425 Cannot open PASV data connection \r\n")
			self.serverDTP.close_data()

	# 
	def PORT(self, dataAddr):
		try:
			self.serverDTP.make_connection_active(dataAddr)
			self.__send("225 Active data connection established\r\n")
		except:
			self.__send("425 Unable to establish active data connection\r\n")
			self.serverDTP.close_data()

	def SYST(self):
		self.__send("215 UNIX\r\n")

	# Handling the file functionality to download/retrieve files from the server.  
	def RETR(self, fileName):
		if self.serverDTP.does_file_exist(fileName):
			try:
				self.__send("125 Sending " + fileName + " to client\r\n")
				self.serverDTP.begin_download(fileName)
				self.serverDTP.close_data()
				self.__send("226 Data transfer complete " + fileName + " sent to client\r\n")
			except:
				self.serverDTP.close_data()
				self.__send("426 Unable to send file to client\r\n")
		else:
			self.__send("450 Invalid file\r\n")
			self.serverDTP.close_data()

	# Handling the functionality to upload/store files to server
	def STOR(self, fileName):
		try:
			self.__send("125 Receiving " + fileName + " from client\r\n")
			self.serverDTP.begin_upload(fileName)
			self.serverDTP.close_data()
			self.__send("226 Data transfer complete " + fileName + " sent to server\r\n")
		except:
			self.serverDTP.close_data()
			self.__send("426 Unable to send file to server\r\n")

	# Handling the quit command from the client 
	def QUIT(self):
		self.__send("221 Terminating control connection\r\n")
		self.isCmdActive = False
		self.cmdConn.close()
		self.serverDTP.close_data()

	#Check if the contol connection is active
	def NOOP(self):
		if self.isCmdActive:
			self.__send("200 Control connection OK\r\n")

	def CWD(self):
		self.serverDTP.current_directory()

	#Handling functionality to select data type in the server, using an argument specifying the desired data type from the client message.
	def TYPE(self, argument):
		argument = argument.upper()
		ValidDataTypes = ["A","I"]
		if argument in ValidDataTypes:
			if argument == "I":
				self.current_type = "I"
				self.__send("200 Binary (I) Type selected\r\n")
			else:
				self.current_type = "A"
				self.__send("200 ASCII (A) Type selected\r\n")
		else:
			self.__send("501 Invalid Type selected\r\n")

	#handling the specification of the file structure to be used from the received client message file structure argument
	def STRU(self, argument):
		argument = argument.upper()
		possibleArguments = ["F","R","P"]
		if argument in possibleArguments:
			if argument == "F":
				self.__send("200 File structure selected\r\n")
			else:
				self.__send("504 Only file structure supported\r\n")
		else:
			self.__send("501 Not a possible file structure\r\n")

	# Handling the specification of the data transfer mode from the received client message data transfer argument
	def MODE(self, argument):
		argument = argument.upper()
		possibleArguments = ["S","B","C"]
		if argument in possibleArguments:
			self.current_mode = "S"
			if argument == "S":
				self.__send("200 Stream mode selected\r\n")
			else:
				self.__send("504 Only stream mode supported\r\n")
		else:
			self.__send("501 Not a possible mode\r\n")

	#Handling the Print the current working directory command from the client
	#This is not so useful because there exists only the root directory on the server.
	def PWD(self):
		directory = "\"" + self.serverDTP.current_directory() + "\""
		self.__send("200 " + "Current working directory: " + directory + "\r\n")

	#opens file system to check information about file in folder
	#open files dir
	#make array=> for each file element,list name,size,date of creation
	def LIST(self, dirPath = ""):
		try:
			self.__send("125 Sending file list\r\n")
			self.serverDTP.send_list(dirPath)
			self.serverDTP.close_data()
			self.__send("226 List successfully sent\r\n")
		except:
			self.serverDTP.close_data()
			self.__send("426 Unable to send list to client\r\n")
