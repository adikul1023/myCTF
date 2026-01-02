from scapy.all import *
import binascii

pkts = rdpcap('network_traffic.pcap')
for i, p in enumerate(pkts):
    if Raw in p:
        payload = p[Raw].load
        if b'paste.sh' in payload:
            print(f"Packet #{i+1} found.")
            idx = payload.find(b'paste.sh')
            # Print 10 bytes before and 10 bytes after
            start = max(0, idx-10)
            end = min(len(payload), idx+18)
            chunk = payload[start:end]
            print(f"Hex: {binascii.hexlify(chunk)}")
            print(f"ASCII: {chunk}")
            break
