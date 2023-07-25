It allows you to make your tasks distributed without resorting to
external message brokers.

The basic idea of TCP broker implementation is that in terms of
performing tasks, there is no difference between them, it is just
a way to establish a connection, both the server and the client can
be the one who performs tasks and the one who sets them, and it is
also possible in a mixed mode.

In other words, deciding who will be the server and who will be the
client in your system is just a way to connect and find each other
in your distributed system.

Here are the ways of organizing communication between the server
and the clients.
