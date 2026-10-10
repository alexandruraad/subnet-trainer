"""Question generators. Each returns a Question with its own answer checker."""

from __future__ import annotations

import ipaddress
import random
from dataclasses import dataclass, field
from typing import Callable

from . import core


@dataclass
class Question:
    topic: str
    prompt: str
    answer: str
    explanation: str
    checker: Callable[[str], bool] = field(repr=False)

    def check(self, response: str) -> bool:
        try:
            return self.checker(response.strip())
        except (ValueError, TypeError):
            return False


# ---------- answer checkers ----------

def _ip_equals(expected: str) -> Callable[[str], bool]:
    target = ipaddress.IPv4Address(expected)
    return lambda r: ipaddress.IPv4Address(r) == target


def _int_equals(expected: int) -> Callable[[str], bool]:
    return lambda r: int(r.replace(",", "").replace("_", "")) == expected


def _prefix_equals(expected: int) -> Callable[[str], bool]:
    def check(r: str) -> bool:
        r = r.lstrip("/")
        if "." in r:  # accept a dotted mask too
            return ipaddress.IPv4Network(f"0.0.0.0/{r}").prefixlen == expected
        return int(r) == expected
    return check


def _one_of(*accepted: str) -> Callable[[str], bool]:
    options = {a.lower() for a in accepted}
    return lambda r: r.lower() in options


# ---------- random addresses ----------

def _random_host(rng: random.Random, prefix: int) -> str:
    """Random address in a private range, paired with a prefix that fits it."""
    first = rng.choice([10, 172, 192])
    if first == 10:
        ip = f"10.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"
    elif first == 172:
        ip = f"172.{rng.randint(16, 31)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"
    else:
        ip = f"192.168.{rng.randint(0, 255)}.{rng.randint(1, 254)}"
    return f"{ip}/{prefix}"


def _prefix(rng: random.Random, difficulty: str) -> int:
    ranges = {"easy": (24, 30), "medium": (16, 30), "hard": (9, 30)}
    lo, hi = ranges[difficulty]
    return rng.randint(lo, hi)


# ---------- subnet questions ----------

def network_q(rng, difficulty):
    cidr = _random_host(rng, _prefix(rng, difficulty))
    i = core.analyse(cidr)
    return Question("network", f"Network address of {cidr}?",
                    str(i.network.network_address), core.block_size_explanation(cidr),
                    _ip_equals(str(i.network.network_address)))


def broadcast_q(rng, difficulty):
    cidr = _random_host(rng, _prefix(rng, difficulty))
    i = core.analyse(cidr)
    return Question("broadcast", f"Broadcast address of {cidr}?",
                    str(i.broadcast), core.block_size_explanation(cidr),
                    _ip_equals(str(i.broadcast)))


def first_host_q(rng, difficulty):
    cidr = _random_host(rng, _prefix(rng, difficulty))
    i = core.analyse(cidr)
    return Question("first-host", f"First usable host in {cidr}?",
                    str(i.first_host),
                    core.block_size_explanation(cidr) + " First host = network + 1.",
                    _ip_equals(str(i.first_host)))


def last_host_q(rng, difficulty):
    cidr = _random_host(rng, _prefix(rng, difficulty))
    i = core.analyse(cidr)
    return Question("last-host", f"Last usable host in {cidr}?",
                    str(i.last_host),
                    core.block_size_explanation(cidr) + " Last host = broadcast - 1.",
                    _ip_equals(str(i.last_host)))


def hosts_q(rng, difficulty):
    p = _prefix(rng, difficulty)
    n = core.usable_hosts(p)
    return Question("hosts", f"How many usable hosts in a /{p}?", str(n),
                    f"Host bits = 32 - {p} = {32 - p}. 2^{32 - p} - 2 = {n} "
                    "(minus the network and broadcast addresses).",
                    _int_equals(n))


def mask_q(rng, difficulty):
    p = _prefix(rng, difficulty)
    mask = str(core.prefix_to_mask(p))
    return Question("mask", f"Write /{p} as a dotted-decimal subnet mask.", mask,
                    f"/{p} = {p} ones then {32 - p} zeros: {core.to_binary(mask)} = {mask}.",
                    _ip_equals(mask))


def wildcard_q(rng, difficulty):
    p = _prefix(rng, difficulty)
    mask = core.prefix_to_mask(p)
    wc = str(ipaddress.IPv4Network(f"0.0.0.0/{p}").hostmask)
    return Question("wildcard", f"Wildcard mask for /{p} (as used in ACLs)?", wc,
                    f"Subtract each mask octet from 255: 255.255.255.255 - {mask} = {wc}.",
                    _ip_equals(wc))


def cidr_for_hosts_q(rng, difficulty):
    top = {"easy": 250, "medium": 4000, "hard": 60000}[difficulty]
    hosts = rng.randint(2, top)
    p = core.smallest_prefix_for_hosts(hosts)
    bits = 32 - p
    return Question("size", f"Smallest subnet (as /prefix) that fits {hosts:,} hosts?", f"/{p}",
                    f"Need 2^h - 2 >= {hosts:,}. h = {bits} gives {core.usable_hosts(p):,} usable, "
                    f"so the prefix is 32 - {bits} = /{p}.",
                    _prefix_equals(p))


def same_subnet_q(rng, difficulty):
    p = _prefix(rng, difficulty)
    a = core.analyse(_random_host(rng, p))
    if rng.random() < 0.5:  # pick a second host from the same subnet
        offset = rng.randint(1, max(1, a.usable_hosts))
        b = a.network.network_address + min(offset, a.total_addresses - 1)
    else:  # or from a neighbouring one
        step = a.total_addresses * rng.choice([-1, 1])
        b = a.network.network_address + rng.randint(1, max(1, a.usable_hosts))
        b = ipaddress.IPv4Address((int(b) + step) % 2**32)
    same = ipaddress.IPv4Address(b) in a.network
    other = core.analyse(f"{b}/{p}")
    ans = "yes" if same else "no"
    return Question("same-subnet", f"Are {a.address} and {b} on the same /{p} subnet? (yes/no)",
                    ans,
                    f"{a.address} is in {a.network}; {b} is in {other.network}.",
                    _one_of(ans, ans[0]))


SUBNET_TOPICS: dict[str, Callable] = {
    "network": network_q,
    "broadcast": broadcast_q,
    "first-host": first_host_q,
    "last-host": last_host_q,
    "hosts": hosts_q,
    "mask": mask_q,
    "wildcard": wildcard_q,
    "size": cidr_for_hosts_q,
    "same-subnet": same_subnet_q,
}


# ---------- networking concepts (OSI, ports, TCP/UDP) ----------

OSI_NAMES = {1: "physical", 2: "data link", 3: "network", 4: "transport",
             5: "session", 6: "presentation", 7: "application"}

# (thing, layer). Only items with a clear exam answer; ARP and TLS are left out
# because they're genuinely debated between layers.
OSI_ITEMS = [
    ("a hub", 1), ("a repeater", 1), ("cabling and signals", 1),
    ("a switch", 2), ("MAC addresses", 2), ("Ethernet frames", 2),
    ("a router", 3), ("IP addresses", 3), ("ICMP (ping)", 3), ("packets", 3),
    ("TCP", 4), ("UDP", 4), ("segments / datagrams", 4), ("port numbers", 4),
    ("HTTP", 7), ("DNS", 7), ("SMTP", 7), ("SSH", 7), ("DHCP", 7),
]

# (protocol, port, transport). Classic Network+ answers.
PORTS = [
    ("FTP (control)", 21, "tcp"), ("SSH", 22, "tcp"), ("Telnet", 23, "tcp"),
    ("SMTP", 25, "tcp"), ("DNS", 53, "both"), ("DHCP server", 67, "udp"),
    ("TFTP", 69, "udp"), ("HTTP", 80, "tcp"), ("POP3", 110, "tcp"),
    ("NTP", 123, "udp"), ("IMAP", 143, "tcp"), ("SNMP", 161, "udp"),
    ("LDAP", 389, "tcp"), ("HTTPS", 443, "tcp"), ("SMB", 445, "tcp"),
    ("Syslog", 514, "udp"), ("LDAPS", 636, "tcp"), ("RDP", 3389, "tcp"),
]


def osi_q(rng, difficulty=None):
    thing, layer = rng.choice(OSI_ITEMS)
    name = OSI_NAMES[layer]
    return Question("osi", f"Which OSI layer is {thing} associated with? (number or name)",
                    f"{layer} ({name})",
                    "Please Do Not Throw Sausage Pizza Away: Physical, Data link, Network, "
                    f"Transport, Session, Presentation, Application. {thing} -> L{layer}.",
                    _one_of(str(layer), name, f"layer {layer}", f"l{layer}",
                            name.replace(" ", "")))


def port_q(rng, difficulty=None):
    proto, port, _ = rng.choice(PORTS)
    return Question("ports", f"Default port for {proto}?", str(port),
                    f"{proto} uses port {port}.", _int_equals(port))


def transport_q(rng, difficulty=None):
    proto, port, transport = rng.choice(PORTS)
    why = {
        "tcp": "it needs reliable, ordered delivery (handshake, acks, retransmits).",
        "udp": "speed and low overhead matter more than guaranteed delivery.",
        "both": "UDP for normal queries, TCP for zone transfers and large responses.",
    }[transport]
    return Question("tcp-udp", f"Does {proto} (port {port}) use TCP, UDP or both?",
                    transport.upper() if transport != "both" else "both",
                    f"{proto} uses {transport.upper() if transport != 'both' else 'both'}: {why}",
                    _one_of(transport))


CONCEPT_TOPICS: dict[str, Callable] = {
    "osi": osi_q,
    "ports": port_q,
    "tcp-udp": transport_q,
}

ALL_TOPICS = {**SUBNET_TOPICS, **CONCEPT_TOPICS}


def generate(topics: list[str], rng: random.Random, difficulty: str = "medium") -> Question:
    return ALL_TOPICS[rng.choice(topics)](rng, difficulty)
