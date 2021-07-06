import getpass
from ClientPI import ClientPI
from ClientUI import ClientUI

print("Welcome to FTP!! Please enter connection details.")
print("Leaving fields blank will enter values shown in brackets.")

serverAddress = input("Enter Server Address Default=>(127.0.0.1): ")    # The ip address of the server to connect to

# Set default ip and port number if it is not already entered
if serverAddress == "":
	serverAddress = "127.0.0.1"
serverPort = input("Port (9999): ") # port 9999 is normally a free unused port, > 1024
if serverPort == "":
	serverPort = "9999"

# The client PI interfaces with the serverPI for control connection=> commands and replies 
client = ClientPI(serverAddress, int(serverPort))

if client.is_CMD_active():
	userName = input("User Name: ")
	password = getpass.getpass(prompt = "Password: ")
	client.login(userName, password)

if client.is_user_valid():
	ui = ClientUI()
	ui.initilise_client(client)
	ui.cmdloop()