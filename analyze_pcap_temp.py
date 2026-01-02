#!/usr/bin/env python3
"""
PCAP Analysis Script - Verify Challenge 2 Evidence
Checks for:
- IP address 104.21.67.185
- SNI: paste.sh
- Timestamp: 2024-11-14 23:48:12 UTC
- Large upload (847KB)
"""

from scapy.all import rdpcap, IP, TCP, Raw
from datetime import datetime
import sys

def analyze_pcap(filename):
    print(f"[*] Loading PCAP file: {filename}")
    try:
        packets = rdpcap(filename)
        print(f"[+] Loaded {len(packets)} packets")
    except Exception as e:
        print(f"[!] Error loading PCAP: {e}")
        return
    
    print("\n" + "="*80)
    print("ANALYSIS 1: Looking for IP 104.21.67.185")
    print("="*80)
    
    target_ip = "104.21.67.185"
    target_packets = []
    
    for i, pkt in enumerate(packets):
        if IP in pkt:
            if pkt[IP].dst == target_ip or pkt[IP].src == target_ip:
                target_packets.append((i, pkt))
    
    if target_packets:
        print(f"[+] Found {len(target_packets)} packets with IP {target_ip}")
        print(f"\nFirst 10 packets:")
        for idx, (pkt_num, pkt) in enumerate(target_packets[:10]):
            timestamp = datetime.fromtimestamp(float(pkt.time))
            src = pkt[IP].src if IP in pkt else "N/A"
            dst = pkt[IP].dst if IP in pkt else "N/A"
            proto = pkt[IP].proto if IP in pkt else "N/A"
            size = len(pkt)
            print(f"  Packet #{pkt_num}: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {src} -> {dst} | Size: {size} bytes")
    else:
        print(f"[!] NO packets found with IP {target_ip}")
    
    print("\n" + "="*80)
    print("ANALYSIS 2: Looking for timestamp around 2024-11-14 23:48:12")
    print("="*80)
    
    target_time = datetime(2024, 11, 14, 23, 48, 12)
    time_window = 60  # seconds
    
    time_matched = []
    for i, pkt in enumerate(packets):
        pkt_time = datetime.fromtimestamp(float(pkt.time))
        time_diff = abs((pkt_time - target_time).total_seconds())
        if time_diff <= time_window:
            time_matched.append((i, pkt, pkt_time))
    
    if time_matched:
        print(f"[+] Found {len(time_matched)} packets within {time_window}s of target time")
        print(f"\nPackets near target timestamp:")
        for idx, (pkt_num, pkt, pkt_time) in enumerate(time_matched[:10]):
            src = pkt[IP].src if IP in pkt else "N/A"
            dst = pkt[IP].dst if IP in pkt else "N/A"
            size = len(pkt)
            print(f"  Packet #{pkt_num}: {pkt_time.strftime('%Y-%m-%d %H:%M:%S')} | {src} -> {dst} | Size: {size}")
    else:
        print(f"[!] NO packets found near target timestamp")
    
    print("\n" + "="*80)
    print("ANALYSIS 3: Looking for TLS/SNI data (paste.sh)")
    print("="*80)
    
    sni_packets = []
    for i, pkt in enumerate(packets):
        if Raw in pkt:
            payload = bytes(pkt[Raw].load)
            # Look for SNI extension in TLS ClientHello
            if b'paste.sh' in payload or b'paste' in payload:
                sni_packets.append((i, pkt))
    
    if sni_packets:
        print(f"[+] Found {len(sni_packets)} packets with 'paste' in payload")
        for idx, (pkt_num, pkt) in enumerate(sni_packets[:5]):
            timestamp = datetime.fromtimestamp(float(pkt.time))
            src = pkt[IP].src if IP in pkt else "N/A"
            dst = pkt[IP].dst if IP in pkt else "N/A"
            print(f"  Packet #{pkt_num}: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {src} -> {dst}")
    else:
        print(f"[!] NO packets found with 'paste' in payload")
    
    print("\n" + "="*80)
    print("ANALYSIS 4: Large uploads (>500KB)")
    print("="*80)
    
    # Group by TCP stream and calculate total bytes
    streams = {}
    for i, pkt in enumerate(packets):
        if TCP in pkt and IP in pkt:
            stream_key = (pkt[IP].src, pkt[TCP].sport, pkt[IP].dst, pkt[TCP].dport)
            if stream_key not in streams:
                streams[stream_key] = {'packets': [], 'total_bytes': 0}
            streams[stream_key]['packets'].append((i, pkt))
            streams[stream_key]['total_bytes'] += len(pkt)
    
    large_streams = [(k, v) for k, v in streams.items() if v['total_bytes'] > 500000]
    large_streams.sort(key=lambda x: x[1]['total_bytes'], reverse=True)
    
    if large_streams:
        print(f"[+] Found {len(large_streams)} TCP streams with >500KB data")
        for idx, (stream_key, stream_data) in enumerate(large_streams[:5]):
            src_ip, src_port, dst_ip, dst_port = stream_key
            total_kb = stream_data['total_bytes'] / 1024
            pkt_count = len(stream_data['packets'])
            first_pkt = stream_data['packets'][0][1]
            timestamp = datetime.fromtimestamp(float(first_pkt.time))
            print(f"  Stream {idx+1}: {src_ip}:{src_port} -> {dst_ip}:{dst_port}")
            print(f"    Total: {total_kb:.2f} KB | Packets: {pkt_count} | Start: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"[!] NO large streams found")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total packets: {len(packets)}")
    print(f"Packets with target IP (104.21.67.185): {len(target_packets)}")
    print(f"Packets near target time: {len(time_matched)}")
    print(f"Packets with 'paste' in payload: {len(sni_packets)}")
    print(f"Large TCP streams (>500KB): {len(large_streams)}")

if __name__ == "__main__":
    analyze_pcap("network_traffic.pcap")
