import random

import socket

from threading import Thread



SERVER_IP = "10.0.2.100"  

SERVER_PORT = 5555  

P = 432020424503  

G = 5  

SERVER_PRIVATE_KEY = 49  



def handle_client(client_socket, address):

    try:

        print(f"Connection from {address} established.")




        entry_number = client_socket.recv(4096).decode().strip()

        print(f"Received entry number: {entry_number}")




        client_socket.sendall(f"{P},{G}".encode())

        print(f"Sent P = {P} and G = {G}")




        client_public_raw = client_socket.recv(4096).decode().strip()

        print(f"Received client's public key (A): {client_public_raw}")

        client_public = int(client_public_raw)




        server_public = pow(G, SERVER_PRIVATE_KEY, P)

        print(f"Server's public key (B = G^b mod P): {server_public}")




        client_socket.sendall(str(server_public).encode())

        print(f"Sent server's public key (B): {server_public}")




        shared_secret = pow(client_public, SERVER_PRIVATE_KEY, P)

        print(f"Computed shared secret (S = A^b mod P): {shared_secret}")



        print("Key exchange complete.")

    except Exception as e:

        print(f"An error occurred with client {address}: {e}")

    finally:

        client_socket.close()

        print(f"Connection with {address} closed.")



def start_server():

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:

        server_socket.bind((SERVER_IP, SERVER_PORT))

        server_socket.listen(5)

        print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")



        while True:

            client_socket, address = server_socket.accept()

            client_handler = Thread(target=handle_client, args=(client_socket, address))

            client_handler.start()



if __name__ == "__main__":

    start_server()

