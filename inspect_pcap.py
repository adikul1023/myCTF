#!/usr/bin/env python3
"""Quick PCAP inspection - what's actually in the file?"""

from scapy.all import rdpcap, IP, TCP
from datetime import datetime
from collections import Counter

packets = rdpcap("network_traffic.pcap")
print(f"Total packets: {len(packets)}")

# Get time range
times = [datetime.fromtimestamp(float(pkt.time)) for pkt in packets if hasattr(pkt, 'time')]
if times:
    print(f"\nTime range:")
    print(f"  First packet: {min(times)}")
    print(f"  Last packet: {max(times)}")

# Get unique IPs
dst_ips = [pkt[IP].dst for pkt in packets if IP in pkt]
src_ips = [pkt[IP].src for pkt in packets if IP in pkt]

print(f"\nTop 10 destination IPs:")
for ip, count in Counter(dst_ips).most_common(10):
    print(f"  {ip}: {count} packets")

print(f"\nTop 10 source IPs:")
for ip, count in Counter(src_ips).most_common(10):
    print(f"  {ip}: {count} packets")

# Check for any Cloudflare IPs (104.x.x.x range)
cloudflare_packets = [pkt for pkt in packets if IP in pkt and (pkt[IP].dst.startswith('104.') or pkt[IP].src.startswith('104.'))]
print(f"\nPackets with 104.x.x.x IPs: {len(cloudflare_packets)}")
if cloudflare_packets:
    cf_ips = set([pkt[IP].dst if pkt[IP].dst.startswith('104.') else pkt[IP].src for pkt in cloudflare_packets])
    print(f"Unique 104.x.x.x IPs: {cf_ips}")

# Check TCP streams
print(f"\nTCP stream analysis:")
tcp_packets = [pkt for pkt in packets if TCP in pkt and IP in pkt]
print(f"  Total TCP packets: {len(tcp_packets)}")

# Sample some packets
print(f"\nFirst 5 packets:")
for i, pkt in enumerate(packets[:5]):
    timestamp = datetime.fromtimestamp(float(pkt.time))
    if IP in pkt:
        print(f"  {i}: {timestamp} | {pkt[IP].src} -> {pkt[IP].dst} | {len(pkt)} bytes")
    else:
        print(f"  {i}: {timestamp} | Non-IP packet | {len(pkt)} bytes")
