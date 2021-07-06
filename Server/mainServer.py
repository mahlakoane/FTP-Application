from ServerPI import ServerPI

server = ServerPI("127.0.0.1", 9999)
server.open_connection() # This is the control connection necessary to exchange commands.
server.running() # The function to wait for commands and interpret them.
