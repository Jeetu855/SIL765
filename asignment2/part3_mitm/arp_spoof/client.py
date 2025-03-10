import socket

import random



SERVER_IP = "10.0.2.100"  

SERVER_PORT = 5555

ENTRY_NUMBER = "2024JCS2043"  

def parse_pg(response):

    

    try:

        parts = response.split(',')

        P = int(parts[0].strip())  

        G = int(parts[1].strip())  

        return P, G

    except Exception as e:

        print("Error parsing P and G:", e)

        return None, None



def deduce_server_private_key(P, G, B, max_attempts=1000000):

    

    print("Starting brute force to deduce server's private key...")

    for potential_b in range(1, max_attempts):

  

        if pow(G, potential_b, P) == B:

            print(f"Server's private key deduced: b = {potential_b} (where B = G^b mod P)")



            return potential_b

        

        else:

            print(f"failed at b = {potential_b}")



    print("Failed to deduce server's private key within given range.")

    return None



def diffie_hellman_client():

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        try:

            s.connect((SERVER_IP, SERVER_PORT))

            print(f"Connected to {SERVER_IP}:{SERVER_PORT}")

            

            s.sendall(ENTRY_NUMBER.encode())

            print(f"Sent entry number: {ENTRY_NUMBER}")

            

            response = s.recv(4096).decode().strip()

            print("Received response:", response)



            P, G = parse_pg(response)

            if not P or not G:

                print("Failed to parse P and G.")

                return



            print(f"Parsed parameters:\nP (prime) = {P}\nG (generator) = {G}")





            private_key = random.randint(2, 1000)

            print(f"Client's private key (a): {private_key}")



            client_public = pow(G, private_key, P)

            print(f"Client's public key (A = G^a mod P): {client_public}")



            s.sendall(str(client_public).encode())

            print(f"Sent public key A: {client_public}")



            server_public_raw = s.recv(4096).decode().strip()

            print(f"Received server's public key (B): {server_public_raw}")

            server_public = int(server_public_raw)



            shared_secret = pow(server_public, private_key, P)

            print(f"Computed shared secret (S = B^a mod P): {shared_secret}")



            # --- Attempt to deduce server's private key ---

            #server_private_key = deduce_server_private_key(P, G, server_public)

            #if server_private_key is not None:

                # Optionally, verify by computing the shared secret using b and client_public

            #    deduced_shared_secret = pow(client_public, server_private_key, P)

            #    print(f"Shared secret computed using deduced server key (S = A^b mod P): {deduced_shared_secret}")

            #else:

            #    print("Could not deduce the server's private key.")



        except Exception as e:

            print(f"An error occurred: {e}")



if __name__ == "__main__":

    diffie_hellman_client()

