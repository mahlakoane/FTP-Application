import socket
import random
import os
import datetime
import stat

class ServerDTP():
	def __init__(self):
		self.dataConn = None
		self.dataSocket = None
		self.files = None
		self.user = None
		self.rootDirectory = None
		self.dataPort = None
		self.dataPortUpper = None
		self.dataportLower = None
		self.isConnOpen = False
		self.isConnPassive = False
		self.bufferSize = 1024

	# Function to generate the necessary port number for a passive data connection : This port number can be randomly allocated.
	def __generate_data_port_passive(self): 
		self.dataPortUpper = str(random.randint(20,30))
		self.dataportLower = str(random.randint(0,255))
		self.dataPort = (int(self.dataPortUpper) * 256) + int(self.dataportLower) # randomly assigned data port stored here

	#This function allows the server DTP to format and return the address that will be sent to the clientPI after a user requests 
	# a passive data connection. 
	def server_address_passive(self, hostName):
		serverAddress = hostName.split(".")
		serverAddress = ",".join(serverAddress)
		serverAddress = "(" + serverAddress + "," + self.dataPortUpper + "," + self.dataportLower + ")"
		return serverAddress

	# This function generates a random port number and binds it to a socket(data socket) on the server side -
	# if client and server are on the same machine then the server name will be the local host)
	def listen_passive(self, hostName):
		self.__generate_data_port_passive()
		self.dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.dataSocket.bind((hostName,self.dataPort))
		self.dataSocket.listen(1) # Listen to clientDTP, for a connection on the port sent to it after requesting the passive mode

	# Accept passive data connection from client trying to establish a passive data connection
	def accept_connection_passive(self):
		self.dataConn,dataAddr = self.dataSocket.accept()
		self.isConnOpen = True
		self.isConnPassive = True
		print("Successful passive data connection\r\n")


	#DTP supporting functionality for an active data connection 
	# During an active connection, the client sends the port and ip address the server should connect to
	# The following  function extracts the ip address of the client from the sent message. 
	def __extract_client_ip_active(self, dataAddr):
		splitAddr = dataAddr.split(',')
		clientIP = '.'.join(splitAddr[:4])
		return clientIP

	# This function proceeds to extract the data port number that the server should connect to back at the client
	def __extract_client_port_active(self, dataAddr):
		splitAddr = dataAddr.split(',')
		portNumber = splitAddr[-2:]
		self.dataPort = (int(portNumber[0]) * 256) + int(portNumber[1])
		return self.dataPort

	# This function establishes an active data connection back to the Client's specified data port [Passive]
	def make_connection_active(self, dataAddr):
		ip = self.__extract_client_ip_active(dataAddr)
		port = self.__extract_client_port_active(dataAddr)
		self.dataConn = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP protocol for the data transmission
		self.dataConn.connect((ip,port))  # The client must accept this data connection at the same port.
		self.isConnOpen = True
		self.isConnPassive = False

	# Allow for setting the internal server data connection-in case the server has to accept a data connection from the client
	# This would be the case for an active data connection. [Active]
	def data_connection(self, dataConn): 
		self.isConnOpen = True
		self.dataConn = dataConn

	# Allow for closing the data connection after data transfer is completed or any point when a data connection should not be open.
	# It operates on the internal data connection variable so it can be used to close both a passive or an active data connection at the server.
	def close_data(self):
		if self.isConnOpen and self.dataConn != None:
			self.dataConn.close()
			print("Terminating data connection\r\n")

	# Functions that the serverDTP has to interact with the server's file system. 
	# These functions offer a small amount of management of the server file system from a clientDTP

	# Function checks the existence of a file by checking if the path to it exists in the server. 
	def does_file_exist(self, filePath):
		filePath = self.rootDirectory + filePath
		if os.path.isfile(filePath):
			return True
		return False
	
	def current_directory(self):
		return "/"

	# This function takes the password entered by the client trying to login and compares it to the internally stored passwords
	# on the server database for authorized clients.
	def is_password_valid(self, password):

		# the correct/valid user folder is accessed through the self.user variable that stores the validated username 
		passwordPath = "ServerDataBase/" + self.user + "/Phrase.txt"  # only the password is stored in the text file
		file = open(passwordPath,"r")
		data = file.readlines()
		file.close()
		if password in data:
			return True
		else:
			return False


	# set server user- take the incoming, validated user and set it to be a server validated user
	def set_user(self, userName):
		self.user = userName
		self.rootDirectory = "ServerDataBase/" + self.user + "/Files/"

	# send file from server => this involves reading local server files and sending them to client data socket
	# File information is read/retrieved from the server folder => client will create a new file(filename.ext) to write information to. 
	def begin_download(self, fileName):
		fileName = self.rootDirectory + fileName    # there are no layers of folders, all files are in the root directory of the server.
		
		file = open(fileName,"rb") # read bytes mode to allow reading the file data in bytes that are ready to send over communication channel
		readingFile = file.read(self.bufferSize)

		#Because of the relatively low buffersize used, keep reading and sending file bytes until entire file has been sent to downloading client.
		# This way it does not matter the size of the file.
		while readingFile:
			self.dataConn.send(readingFile) # send file data in bytes over the communication channel to client
			readingFile = file.read(self.bufferSize)
		file.close()


	#receive file from client => server is receiving file information from the client through the server data socket
	def begin_upload(self, fileName):
		fileName = self.rootDirectory + fileName #create file with name filename if it does not exist=>in the root directory
		file = open(fileName,"wb") # Allow for writing to the file in write bytes mode. 
		writingFile = self.dataConn.recv(self.bufferSize)  # receive file from client
		
		#keep receiving until the entire file is received
		while writingFile:
			file.write(writingFile)
			writingFile = self.dataConn.recv(self.bufferSize)
		file.close()

	# This function creates a an array list that has all the files available in the root directory and file related details
	# for each file, this list is sent over the data connection to the client upon the client's request to see the files in the 
	# server
	def send_list(self, dirPath):
		dirList = []
		currentDirectory = self.rootDirectory  # the root directory is the only existing directory as there is no functionality to create and manage other directories yet
		items = os.listdir(currentDirectory)
		for file in items:
			newPath = os.path.join(currentDirectory,file)
			dateModified = datetime.datetime.fromtimestamp(os.path.getmtime(newPath)).strftime("%b %d %H:%M")
			fileStats = os.stat(newPath)
			linkNum = fileStats.st_nlink
			userID = fileStats.st_uid
			groupID = fileStats.st_gid
			fileSize = os.path.getsize(newPath)
			fileData = str(stat.filemode(os.stat(newPath).st_mode)) + "\t" + str(linkNum) + "\t" + str(userID) + "\t" + str(groupID) + "\t\t" + str(fileSize) + "\t" + str(dateModified) + "\t" + file 
			dirList.append(fileData)
		for item in dirList:
			self.dataConn.send((item + "\r\n").encode()) # send list of available files and file details to the client.
