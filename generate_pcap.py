#!/usr/bin/env python3
"""
Realistic PCAP generator for DFIR challenge.

Generates a ~500MB PCAP file with:
- ~90k-110k packets
- Several hours of normal corporate TLS traffic
- ONE suspicious encrypted burst to paste.sh (104.21.67.185) at exact timestamp

Requirements:
    pip install scapy[tls]
"""

import argparse
import os
import random
import struct
from datetime import datetime, timedelta
from pathlib import Path

try:
    from scapy.all import Ether, IP, TCP, UDP, DNS, DNSQR, Raw, wrpcap
    from scapy.layers.tls.all import TLS, TLSClientHello, TLS_Ext_ServerName
    SCAPY_TLS = True
except ImportError:
    from scapy.all import Ether, IP, TCP, UDP, DNS, DNSQR, Raw, wrpcap
    SCAPY_TLS = False
    print("WARNING: scapy[tls] not installed. TLS SNI may not be properly encoded.")

# Configuration
OUT_DIR = Path("cases/001-the-disappearance/artifacts/network_capture")
OUT_FILENAME = "network_traffic.pcap"
SEED = 42

# Time range: Nov 13 18:00 to Nov 15 06:00 (36 hours)
START_TIME = datetime(2024, 11, 13, 18, 0, 0)
END_TIME = datetime(2024, 11, 15, 6, 0, 0)

# Suspicious connection details
SUSPICIOUS_TIME = datetime(2024, 11, 14, 23, 48, 12)  # Exact timestamp required
SUSPICIOUS_IP = "104.21.67.185"
SUSPICIOUS_PORT = 443
SUSPICIOUS_SNI = "paste.sh"
SUSPICIOUS_UPLOAD_SIZE = 847 * 1024  # ~847 KB
SUSPICIOUS_DURATION = 2.8  # seconds

# Normal traffic destinations (realistic IPs for these domains)
NORMAL_DESTS = [
    ("140.82.121.3", "github.com"),
    ("52.202.62.123", "slack.com"),
    ("142.250.190.78", "google.com"),
    ("54.239.28.85", "aws.amazon.com"),
    ("20.190.128.0", "microsoft.com"),
]

# Network configuration
SRC_IP = "192.168.1.105"
SRC_MAC = "00:16:3e:aa:bb:cc"
DST_MAC = "00:16:3e:dd:ee:ff"
DNS_SERVER = "8.8.8.8"

# Traffic generation parameters
TARGET_SIZE_MB = 500
TARGET_PACKETS = 100000  # Aim for ~100k packets
AVG_PACKET_SIZE = 5000  # Average packet size in bytes (including headers)


def pkt_time(dt):
    """Convert datetime to Unix timestamp."""
    return dt.timestamp()


def build_tls_client_hello(sni_name):
    """
    Build a proper TLS 1.2 ClientHello with SNI extension.
    Returns bytes that Wireshark will recognize.
    """
    sni_bytes = sni_name.encode('utf-8')
    
    # TLS Record Header: Content Type (0x16 = Handshake), Version (0x0303 = TLS 1.2), Length
    # Handshake Header: Type (0x01 = ClientHello), Length (3 bytes)
    # ClientHello: Version, Random (32 bytes), SessionID length + SessionID, CipherSuites length + CipherSuites
    # Compression methods length + compression methods, Extensions length + Extensions
    
    # Random (32 bytes)
    random_bytes = os.urandom(32)
    
    # Session ID (empty)
    session_id_len = 0
    
    # Cipher Suites (common ones)
    cipher_suites = [
        0x1301, 0x1302, 0x1303,  # TLS 1.3
        0xc02b, 0xc02f, 0xc02c, 0xc030,  # ECDHE
        0x009e, 0x009f, 0xcca8, 0xcca9,  # DHE
    ]
    cipher_suites_bytes = b''.join([cs.to_bytes(2, 'big') for cs in cipher_suites])
    
    # Compression methods (null only)
    compression = b'\x01\x00'
    
    # SNI Extension (0x0000)
    # Extension type (2 bytes) + Extension length (2 bytes)
    # ServerNameList length (2 bytes) + ServerName entry
    # ServerName type (1 byte, 0x00 = host_name) + ServerName length (2 bytes) + ServerName
    sni_extension = (
        struct.pack('>H', 0x0000) +  # Extension type: server_name
        struct.pack('>H', 2 + 3 + len(sni_bytes)) +  # Extension length
        struct.pack('>H', 1 + 2 + len(sni_bytes)) +  # ServerNameList length
        b'\x00' +  # ServerName type: host_name
        struct.pack('>H', len(sni_bytes)) +  # ServerName length
        sni_bytes  # ServerName
    )
    
    # Other common extensions
    # Supported Versions (0x002b)
    supported_versions = (
        struct.pack('>H', 0x002b) +
        struct.pack('>H', 3) +
        b'\x02' +  # Length of version list
        b'\x03\x04'  # TLS 1.3
    )
    
    # Signature Algorithms (0x000d)
    sig_algs = (
        struct.pack('>H', 0x000d) +
        struct.pack('>H', 32) +
        b'\x20' +  # Length
        b'\x04\x03\x08\x04\x04\x01\x05\x03\x08\x05\x05\x01\x08\x06\x06\x01'
        b'\x02\x01\x04\x02\x05\x02\x06\x02\x02\x02\x04\x01\x05\x01\x06\x01'
    )
    
    # Supported Groups (0x000a)
    supported_groups = (
        struct.pack('>H', 0x000a) +
        struct.pack('>H', 4) +
        b'\x02' +  # Length
        b'\x00\x1d\x00\x17'  # x25519, secp256r1
    )
    
    # Key Share (0x0033) - empty for now
    key_share = (
        struct.pack('>H', 0x0033) +
        struct.pack('>H', 2) +
        b'\x00\x00'  # Empty
    )
    
    # All extensions
    all_extensions = sni_extension + supported_versions + sig_algs + supported_groups + key_share
    extensions_length = len(all_extensions)
    
    # ClientHello message
    client_hello = (
        struct.pack('>H', 0x0303) +  # Version: TLS 1.2
        random_bytes +  # Random (32 bytes)
        struct.pack('B', session_id_len) +  # SessionID length
        struct.pack('>H', len(cipher_suites_bytes)) +  # CipherSuites length
        cipher_suites_bytes +  # CipherSuites
        compression +  # Compression methods
        struct.pack('>H', extensions_length) +  # Extensions length
        all_extensions  # Extensions
    )
    
    # Handshake message
    handshake = (
        b'\x01' +  # Type: ClientHello
        struct.pack('>I', len(client_hello))[1:] +  # Length (3 bytes)
        client_hello
    )
    
    # TLS Record
    record = (
        b'\x16' +  # Content Type: Handshake
        b'\x03\x03' +  # Version: TLS 1.2
        struct.pack('>H', len(handshake)) +  # Length
        handshake
    )
    
    return record


def make_syn(src_ip, dst_ip, sport, dport, seq, ts):
    """Create TCP SYN packet."""
    pkt = Ether(src=SRC_MAC, dst=DST_MAC) / IP(src=src_ip, dst=dst_ip) / TCP(sport=sport, dport=dport, flags="S", seq=seq)
    pkt.time = pkt_time(ts)
    return pkt


def make_synack(src_ip, dst_ip, sport, dport, seq, ack, ts):
    """Create TCP SYN-ACK packet."""
    pkt = Ether(src=DST_MAC, dst=SRC_MAC) / IP(src=dst_ip, dst=src_ip) / TCP(sport=dport, dport=sport, flags="SA", seq=seq, ack=ack)
    pkt.time = pkt_time(ts)
    return pkt


def make_ack(src_ip, dst_ip, sport, dport, seq, ack, ts, payload=None):
    """Create TCP ACK packet, optionally with payload."""
    if payload:
        pkt = Ether(src=SRC_MAC, dst=DST_MAC) / IP(src=src_ip, dst=dst_ip) / TCP(sport=sport, dport=dport, flags="PA", seq=seq, ack=ack) / Raw(payload)
    else:
        pkt = Ether(src=SRC_MAC, dst=DST_MAC) / IP(src=src_ip, dst=dst_ip) / TCP(sport=sport, dport=dport, flags="A", seq=seq, ack=ack)
    pkt.time = pkt_time(ts)
    return pkt


def make_tls_client_hello_packet(src_ip, dst_ip, sport, dport, sni, seq, ack, ts):
    """Create packet containing TLS ClientHello with SNI."""
    client_hello = build_tls_client_hello(sni)
    return make_ack(src_ip, dst_ip, sport, dport, seq, ack, ts, payload=client_hello)


def make_tls_app_data(src_ip, dst_ip, sport, dport, seq, ack, ts, data_len, direction="c2s"):
    """Create TLS Application Data record."""
    # TLS Record: Content Type (0x17 = Application Data), Version (0x0303 = TLS 1.2), Length
    payload = os.urandom(data_len)
    tls_record = b"\x17\x03\x03" + struct.pack('>H', len(payload)) + payload
    
    if direction == "c2s":
        pkt = Ether(src=SRC_MAC, dst=DST_MAC) / IP(src=src_ip, dst=dst_ip) / TCP(sport=sport, dport=dport, flags="PA", seq=seq, ack=ack) / Raw(tls_record)
    else:
        pkt = Ether(src=DST_MAC, dst=SRC_MAC) / IP(src=dst_ip, dst=src_ip) / TCP(sport=dport, dport=sport, flags="PA", seq=seq, ack=ack) / Raw(tls_record)
    pkt.time = pkt_time(ts)
    return pkt


def make_dns_query(src_ip, dst_ip, sport, dport, qname, ts):
    """Create DNS query packet."""
    pkt = Ether(src=SRC_MAC, dst=DST_MAC) / IP(src=src_ip, dst=dst_ip) / UDP(sport=sport, dport=dport) / DNS(id=random.randint(0, 65535), qr=0, qd=DNSQR(qname=qname))
    pkt.time = pkt_time(ts)
    return pkt


def make_dns_response(src_ip, dst_ip, sport, dport, qname, answer_ip, ts):
    """Create DNS response packet."""
    from scapy.layers.dns import DNSRR
    pkt = Ether(src=DST_MAC, dst=SRC_MAC) / IP(src=dst_ip, dst=src_ip) / UDP(sport=dport, dport=sport) / DNS(
        id=random.randint(0, 65535), qr=1, qd=DNSQR(qname=qname), an=DNSRR(rrname=qname, rdata=answer_ip, ttl=300)
    )
    pkt.time = pkt_time(ts)
    return pkt


def build_normal_tls_flow(src_ip, dst_ip, sni, start_ts, flow_bytes=5000):
    """
    Build a normal TLS flow with handshake and application data.
    Returns list of packets.
    """
    packets = []
    sport = random.randint(32768, 61000)
    dport = 443
    client_seq = random.randint(1000, 2**31 - 1)
    server_seq = random.randint(1000, 2**31 - 1)
    ts = start_ts
    
    # TCP 3-way handshake
    packets.append(make_syn(src_ip, dst_ip, sport, dport, client_seq, ts))
    ts += timedelta(milliseconds=random.randint(20, 150))
    
    packets.append(make_synack(src_ip, dst_ip, sport, dport, server_seq, client_seq + 1, ts))
    ts += timedelta(milliseconds=random.randint(5, 50))
    
    packets.append(make_ack(src_ip, dst_ip, sport, dport, client_seq + 1, server_seq + 1, ts))
    ts += timedelta(milliseconds=random.randint(10, 100))
    
    # TLS ClientHello
    packets.append(make_tls_client_hello_packet(src_ip, dst_ip, sport, dport, sni, client_seq + 1, server_seq + 1, ts))
    ts += timedelta(milliseconds=random.randint(20, 200))
    
    # Server response (ServerHello, Certificate, etc.) - small
    server_response_size = random.randint(200, 1500)
    packets.append(make_tls_app_data(src_ip, dst_ip, sport, dport, server_seq + 1, client_seq + 1, ts, server_response_size, direction="s2c"))
    ts += timedelta(milliseconds=random.randint(10, 100))
    packets.append(make_ack(src_ip, dst_ip, sport, dport, client_seq + 1, server_seq + 1 + server_response_size, ts))
    ts += timedelta(milliseconds=random.randint(10, 50))
    
    # Application data (client upload/download)
    remaining = flow_bytes
    client_seq_offset = 1
    server_seq_offset = 1 + server_response_size
    
    # Mix of upload and download
    while remaining > 0:
        chunk_size = min(random.randint(500, 1400), remaining)
        direction = "c2s" if random.random() < 0.6 else "s2c"  # 60% upload
        
        if direction == "c2s":
            packets.append(make_tls_app_data(src_ip, dst_ip, sport, dport, client_seq + client_seq_offset, server_seq + server_seq_offset, ts, chunk_size, direction="c2s"))
            client_seq_offset += chunk_size
        else:
            packets.append(make_tls_app_data(src_ip, dst_ip, sport, dport, server_seq + server_seq_offset, client_seq + client_seq_offset, ts, chunk_size, direction="s2c"))
            server_seq_offset += chunk_size
        
        remaining -= chunk_size
        ts += timedelta(milliseconds=random.randint(5, 100))
        
        # Occasional ACK
        if random.random() < 0.3:
            if direction == "c2s":
                packets.append(make_ack(src_ip, dst_ip, sport, dport, server_seq + server_seq_offset, client_seq + client_seq_offset, ts))
            else:
                packets.append(make_ack(src_ip, dst_ip, sport, dport, client_seq + client_seq_offset, server_seq + server_seq_offset, ts))
            ts += timedelta(milliseconds=random.randint(5, 30))
    
    # FIN
    ts += timedelta(milliseconds=random.randint(50, 500))
    packets.append(Ether(src=SRC_MAC, dst=DST_MAC) / IP(src=src_ip, dst=dst_ip) / TCP(sport=sport, dport=dport, flags="FA", seq=client_seq + client_seq_offset, ack=server_seq + server_seq_offset))
    packets[-1].time = pkt_time(ts)
    
    return packets


def build_suspicious_flow(src_ip, dst_ip, sni, start_ts):
    """
    Build the suspicious high-bandwidth TLS upload to paste.sh.
    Returns list of packets.
    """
    packets = []
    sport = random.randint(32768, 61000)
    dport = SUSPICIOUS_PORT
    client_seq = random.randint(1000, 2**31 - 1)
    server_seq = random.randint(1000, 2**31 - 1)
    
    # TCP 3-way handshake (slightly before the burst)
    handshake_start = start_ts - timedelta(milliseconds=100)
    packets.append(make_syn(src_ip, dst_ip, sport, dport, client_seq, handshake_start))
    packets.append(make_synack(src_ip, dst_ip, sport, dport, server_seq, client_seq + 1, handshake_start + timedelta(milliseconds=30)))
    packets.append(make_ack(src_ip, dst_ip, sport, dport, client_seq + 1, server_seq + 1, handshake_start + timedelta(milliseconds=50)))
    
    # TLS ClientHello
    packets.append(make_tls_client_hello_packet(src_ip, dst_ip, sport, dport, sni, client_seq + 1, server_seq + 1, handshake_start + timedelta(milliseconds=60)))
    
    # Small server response
    server_response_ts = handshake_start + timedelta(milliseconds=150)
    packets.append(make_tls_app_data(src_ip, dst_ip, sport, dport, server_seq + 1, client_seq + 1, server_response_ts, 500, direction="s2c"))
    packets.append(make_ack(src_ip, dst_ip, sport, dport, client_seq + 1, server_seq + 1 + 500, server_response_ts + timedelta(milliseconds=10)))
    
    # High-bandwidth upload burst
    # First large packet must be at exactly SUSPICIOUS_TIME
    total_upload = SUSPICIOUS_UPLOAD_SIZE
    chunk_size = 1440  # Typical MSS
    num_chunks = (total_upload + chunk_size - 1) // chunk_size
    
    client_seq_offset = 1
    server_seq_offset = 1 + 500
    
    # First packet at exact timestamp
    first_packet_ts = SUSPICIOUS_TIME
    packets.append(make_tls_app_data(src_ip, dst_ip, sport, dport, client_seq + client_seq_offset, server_seq + server_seq_offset, first_packet_ts, chunk_size, direction="c2s"))
    client_seq_offset += chunk_size
    total_upload -= chunk_size
    
    # Remaining packets spread over SUSPICIOUS_DURATION
    time_per_chunk = SUSPICIOUS_DURATION / max(1, num_chunks - 1)
    current_ts = first_packet_ts
    
    while total_upload > 0:
        current_ts += timedelta(seconds=time_per_chunk)
        chunk = min(chunk_size, total_upload)
        packets.append(make_tls_app_data(src_ip, dst_ip, sport, dport, client_seq + client_seq_offset, server_seq + server_seq_offset, current_ts, chunk, direction="c2s"))
        client_seq_offset += chunk
        total_upload -= chunk
        
        # Occasional ACK from server
        if random.random() < 0.2:
            packets.append(make_ack(src_ip, dst_ip, sport, dport, server_seq + server_seq_offset, client_seq + client_seq_offset, current_ts + timedelta(milliseconds=10)))
    
    # FIN
    packets.append(Ether(src=SRC_MAC, dst=DST_MAC) / IP(src=src_ip, dst=dst_ip) / TCP(sport=sport, dport=dport, flags="FA", seq=client_seq + client_seq_offset, ack=server_seq + server_seq_offset))
    packets[-1].time = pkt_time(current_ts + timedelta(milliseconds=200))
    
    return packets


def generate_pcap(out_file, target_mb=TARGET_SIZE_MB, target_packets=TARGET_PACKETS):
    """Generate the complete PCAP file."""
    print(f"Generating PCAP: {out_file}")
    print(f"Target size: ~{target_mb} MB")
    print(f"Target packets: ~{target_packets}")
    
    packets = []
    random.seed(SEED)
    
    # Generate background traffic over time range
    current_time = START_TIME
    time_range = (END_TIME - START_TIME).total_seconds()
    flows_generated = 0
    
    print("Generating background traffic...")
    
    # Generate normal TLS flows throughout the time range
    target_size_bytes = target_mb * 1024 * 1024
    
    while current_time < END_TIME:
        # Check if we've reached target size
        current_size = sum(len(bytes(p)) for p in packets)
        if current_size >= target_size_bytes * 0.95:
            break
        
        # Random interval between flows (shorter intervals for more traffic)
        current_time += timedelta(seconds=random.uniform(0.05, 2.0))
        
        # Occasional DNS query
        if random.random() < 0.03:
            dest_ip, sni = random.choice(NORMAL_DESTS)
            dns_sport = random.randint(1024, 65535)
            packets.append(make_dns_query(SRC_IP, DNS_SERVER, dns_sport, 53, sni, current_time))
            packets.append(make_dns_response(SRC_IP, DNS_SERVER, dns_sport, 53, sni, dest_ip, current_time + timedelta(milliseconds=random.randint(10, 100))))
            current_time += timedelta(milliseconds=random.randint(50, 200))
        
        # TLS flow - vary sizes more to reach target
        dest_ip, sni = random.choice(NORMAL_DESTS)
        # Use larger flows more often to reach 500MB
        if random.random() < 0.3:
            flow_bytes = int(random.expovariate(1.0 / 20000) + 1000)  # Larger flows
            flow_bytes = min(flow_bytes, 100000)  # Cap at 100KB
        else:
            flow_bytes = int(random.expovariate(1.0 / 8000) + 500)  # Normal flows
            flow_bytes = min(flow_bytes, 50000)  # Cap at 50KB
        
        flow_packets = build_normal_tls_flow(SRC_IP, dest_ip, sni, current_time, flow_bytes)
        packets.extend(flow_packets)
        
        # Update time to end of flow
        if flow_packets:
            current_time = datetime.fromtimestamp(flow_packets[-1].time) + timedelta(seconds=random.uniform(0.1, 1.5))
        
        flows_generated += 1
        
        # Progress indicator
        if flows_generated % 1000 == 0:
            est_size_mb = sum(len(bytes(p)) for p in packets) / (1024 * 1024)
            print(f"  Generated {flows_generated} flows, {len(packets)} packets, ~{est_size_mb:.1f} MB")
    
    print(f"Background traffic: {len(packets)} packets")
    
    # Insert suspicious flow at exact timestamp
    print(f"Inserting suspicious flow at {SUSPICIOUS_TIME}...")
    suspicious_packets = build_suspicious_flow(SRC_IP, SUSPICIOUS_IP, SUSPICIOUS_SNI, SUSPICIOUS_TIME)
    packets.extend(suspicious_packets)
    print(f"Suspicious flow: {len(suspicious_packets)} packets")
    
    # Generate more traffic after the suspicious flow to fill remaining time
    post_time = SUSPICIOUS_TIME + timedelta(seconds=10)
    while post_time < END_TIME:
        current_size = sum(len(bytes(p)) for p in packets)
        if current_size >= target_size_bytes * 0.98:
            break
        
        dest_ip, sni = random.choice(NORMAL_DESTS)
        flow_bytes = int(random.expovariate(1.0 / 10000) + 500)
        flow_bytes = min(flow_bytes, 80000)
        flow_packets = build_normal_tls_flow(SRC_IP, dest_ip, sni, post_time, flow_bytes)
        packets.extend(flow_packets)
        if flow_packets:
            post_time = datetime.fromtimestamp(flow_packets[-1].time) + timedelta(seconds=random.uniform(0.2, 2.0))
    
    # Sort all packets by timestamp
    print("Sorting packets by timestamp...")
    packets.sort(key=lambda p: p.time)
    
    # Write PCAP
    print(f"Writing PCAP file...")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    wrpcap(str(out_file), packets)
    
    # Statistics
    total_size = sum(len(bytes(p)) for p in packets)
    size_mb = total_size / (1024 * 1024)
    
    print(f"\nPCAP generation complete!")
    print(f"  File: {out_file}")
    print(f"  Packets: {len(packets)}")
    print(f"  Size: {size_mb:.2f} MB")
    print(f"  Time range: {datetime.fromtimestamp(packets[0].time)} to {datetime.fromtimestamp(packets[-1].time)}")
    print(f"  Suspicious flow timestamp: {SUSPICIOUS_TIME}")
    print(f"  Suspicious IP: {SUSPICIOUS_IP}")
    print(f"  Suspicious SNI: {SUSPICIOUS_SNI}")
    
    return out_file, len(packets), size_mb


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate realistic PCAP for DFIR challenge")
    parser.add_argument("--size-mb", type=int, default=TARGET_SIZE_MB, help=f"Target PCAP size in MB (default: {TARGET_SIZE_MB})")
    parser.add_argument("--packets", type=int, default=TARGET_PACKETS, help=f"Target packet count (default: {TARGET_PACKETS})")
    parser.add_argument("--out", type=str, default=str(OUT_DIR / OUT_FILENAME), help="Output PCAP file path")
    parser.add_argument("--seed", type=int, default=SEED, help=f"Random seed (default: {SEED})")
    
    args = parser.parse_args()
    
    SEED = args.seed
    random.seed(SEED)
    
    out_path = Path(args.out)
    generate_pcap(out_path, target_mb=args.size_mb, target_packets=args.packets)
