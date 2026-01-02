from scapy.all import *
import struct

pcap_file = "network_traffic.pcap"
print(f"Auditing {pcap_file}...")
pkts = rdpcap(pcap_file)

snis = {}
total_tls = 0

for i, pkt in enumerate(pkts):
    if Raw in pkt:
        load = pkt[Raw].load
        # Quick check for TLS Handshake (0x16) and ClientHello (0x01)
        if len(load) > 5 and load[0] == 0x16 and load[5] == 0x01:
            total_tls += 1
            # Try to extract SNI manually to be robust
            # Skip Record Header (5) + Handshake Header (4) + Version (2) + Random (32) + 
            # SessionIDLen (1) + SessionID (X) + CipherLen (2) + Ciphers (Y) + CompLen (1) + Comp (Z) + ExtLen (2)
            try:
                # Naive search for known domains to verify existence
                for domain in ["paste.sh", "cloudflare.com", "google.com", "slack.com", "github.com", "aws.amazon.com", "microsoft.com"]:
                    if domain.encode() in load:
                        snis[domain] = snis.get(domain, 0) + 1
            except:
                pass

print(f"Total TLS ClientHellos: {total_tls}")
print("Found domains (grep match):")
for domain, count in snis.items():
    print(f"  {domain}: {count}")

# Check specifically for paste.sh packet
for i, pkt in enumerate(pkts):
    if Raw in pkt and b"paste.sh" in pkt[Raw].load:
        print(f"\n[!] paste.sh found in packet #{i+1}")
        print(f"    Timestamp: {datetime.fromtimestamp(float(pkt.time))}")
        break
