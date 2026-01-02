#!/usr/bin/env python3
"""Detailed stream analysis for paste.sh traffic"""

from scapy.all import rdpcap, IP, TCP
from datetime import datetime

packets = rdpcap("network_traffic.pcap")
print(f"Total packets: {len(packets)}")

# Find all packets with target IP
target_ip = "104.21.67.185"
target_packets = [(i, pkt) for i, pkt in enumerate(packets) if IP in pkt and (pkt[IP].dst == target_ip or pkt[IP].src == target_ip)]

print(f"\nFound {len(target_packets)} packets with IP {target_ip}")

if target_packets:
    # Get the stream details
    first_idx, first_pkt = target_packets[0]
    last_idx, last_pkt = target_packets[-1]
    
    print(f"\nStream range: Packet #{first_idx} to #{last_idx}")
    print(f"Total packets in stream: {len(target_packets)}")
    
    # Calculate total bytes
    total_bytes = sum(len(pkt) for _, pkt in target_packets)
    total_kb = total_bytes / 1024
    
    print(f"Total bytes: {total_bytes:,} ({total_kb:.2f} KB)")
    
    # Show first 10 packets
    print(f"\nFirst 10 packets in stream:")
    for idx, (pkt_num, pkt) in enumerate(target_packets[:10]):
        timestamp = datetime.fromtimestamp(float(pkt.time))
        src = pkt[IP].src
        dst = pkt[IP].dst
        size = len(pkt)
        flags = pkt[TCP].flags if TCP in pkt else "N/A"
        print(f"  #{pkt_num}: {timestamp.strftime('%H:%M:%S.%f')} | {src} -> {dst} | {size} bytes | Flags: {flags}")
    
    # Check for upload direction (workstation -> paste.sh)
    upload_packets = [(i, pkt) for i, pkt in target_packets if pkt[IP].dst == target_ip]
    upload_bytes = sum(len(pkt) for _, pkt in upload_packets)
    upload_kb = upload_bytes / 1024
    
    print(f"\nUpload packets (to {target_ip}): {len(upload_packets)}")
    print(f"Upload bytes: {upload_bytes:,} ({upload_kb:.2f} KB)")
    
    # Check for download direction
    download_packets = [(i, pkt) for i, pkt in target_packets if pkt[IP].src == target_ip]
    download_bytes = sum(len(pkt) for _, pkt in download_packets)
    download_kb = download_bytes / 1024
    
    print(f"\nDownload packets (from {target_ip}): {len(download_packets)}")
    print(f"Download bytes: {download_bytes:,} ({download_kb:.2f} KB)")
    
    # Time duration
    start_time = datetime.fromtimestamp(float(first_pkt.time))
    end_time = datetime.fromtimestamp(float(last_pkt.time))
    duration = (end_time - start_time).total_seconds()
    
    print(f"\nStream duration: {duration:.2f} seconds")
    print(f"Start: {start_time}")
    print(f"End: {end_time}")
