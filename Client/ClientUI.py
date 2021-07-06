from ClientPI import ClientPI
from cmd import Cmd

class ClientUI(Cmd):
	def initilise_client(self, client):
		self.client = client
		# The client must have the following already set up for successful interaction with a standard ftp application- fileZilla
		self.client.SYST()
		self.client.MODE()
		self.client.STRU()
		self.client.TYPE()
		self.client.PWD()
		self.client.LIST()
		self.__print_directory_list()
		print("Type \'help\' to see the list of available commands and \'quit\' to exit\r\n")

	def do_NOOP(self, inp):
		self.client.NOOP()

	def help_NOOP(self):
		print("Check the control connection.\r\n")

	def do_data_mode(self, inp):
		self.client.data_mode(inp)

	def help_data_mode(self):
		print("data_mode <mode>\r\n")
		print("Set files to be transfered either actively or passively.")
		print("Arguments: \'active\' or \'passive\' (case sensetive).\r\n")

	def do_quit(self, inp):
		self.client.close_connections()
		return True

	def help_quit(self):
		print("Close all connections and logout the user.\r\n")

	def do_LIST(self, inp):
		self.__print_directory_list()

	def help_LIST(self):
		print("Show all available files on the server.\r\n")

	def do_RETR(self, inp):
		self.client.RETR(inp)
		self.__print_directory_list()

	def help_RETR(self):
		print("RETR <filename.extention>\r\n")
		print("Download a file from the server")
		print("Files will be stored in the \"FromServer\" directory.\r\n")

	def do_STOR(self, inp):
		self.client.STOR(inp)
		self.client.LIST()
		self.__print_directory_list()

	def help_STOR(self):
		print("file_upload <filename.extention>\r\n")
		print("Upload a file to the server")
		print("Files must be in the \"ToServer\" directory prior to upload.\r\n")

	def __print_directory_list(self):
		data = self.client.get_remote_directory_list()
		dash = "-" * 80
		print(dash)
		print("{:<20s}{:<20s}{:<20s}{:<20s}".format("Name", "Size", "Date Modified", "Type"))
		print(dash)
		for i in range(len(data)):
			if data[i][3][0] == "d":
				data[i][3] = "directory"
			else:
				data[i][3] = "file"
			print("{:<20s}{:<20s}{:<20s}{:<20s}".format(data[i][0],data[i][1],data[i][2],data[i][3]))
		print("\r\n")