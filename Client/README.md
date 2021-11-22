Client connects to the given server (currently has the IP address of 192.168.43.59)

After it is connected, it starts to send the readings from the circuit connected to the pi

This continues to send unless the sending has been deactivated by the server

The client recieves messages from the server which informs the client on its respective actions
    This includes
        -> Exit
        -> Turning the sensors on
        -> Turning the sensors off
        -> Recieving the status