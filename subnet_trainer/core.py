"""Subnet maths: the calculator behind the quiz and the `calc` command."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass


@dataclass(frozen=True)
class SubnetInfo:
    address: ipaddress.IPv4Address
    network: ipaddress.IPv4Network
    prefix: int
    netmask: ipaddress.IPv4Address
    wildcard: ipaddress.IPv4Address
    broadcast: ipaddress.IPv4Address
    first_host: ipaddress.IPv4Address
    last_host: ipaddress.IPv4Address
    total_addresses: int
    usable_hosts: int


def parse(cidr: str) -> ipaddress.IPv4Interface:
    """Accept '10.0.0.5/24' or '10.0.0.5 255.255.255.0'."""
    text = cidr.strip()
    if " " in text:
        ip, mask = text.split(None, 1)
        text = f"{ip}/{mask.strip()}"
    if "/" not in text:
        raise ValueError(f"missing prefix or mask in {cidr!r} (try 10.0.0.5/24)")
    return ipaddress.IPv4Interface(text)


def usable_hosts(prefix: int) -> int:
    """Usable host count, with the /31 (RFC 3021) and /32 edge cases."""
    if prefix == 32:
        return 1
    if prefix == 31:
        return 2
    return 2 ** (32 - prefix) - 2


def analyse(cidr: str) -> SubnetInfo:
    iface = parse(cidr)
    net = iface.network
    p = net.prefixlen
    if p >= 31:
        first, last = net.network_address, net.broadcast_address
    else:
        first, last = net.network_address + 1, net.broadcast_address - 1
    return SubnetInfo(
        address=iface.ip,
        network=net,
        prefix=p,
        netmask=net.netmask,
        wildcard=net.hostmask,
        broadcast=net.broadcast_address,
        first_host=first,
        last_host=last,
        total_addresses=net.num_addresses,
        usable_hosts=usable_hosts(p),
    )


def to_binary(ip: ipaddress.IPv4Address | str) -> str:
    """192.168.1.1 -> 11000000.10101000.00000001.00000001"""
    return ".".join(f"{int(o):08b}" for o in str(ip).split("."))


def prefix_to_mask(prefix: int) -> ipaddress.IPv4Address:
    return ipaddress.IPv4Network(f"0.0.0.0/{prefix}").netmask


def smallest_prefix_for_hosts(hosts: int) -> int:
    """Smallest subnet (largest prefix) that still fits `hosts` usable hosts."""
    if hosts < 1:
        raise ValueError("need at least one host")
    for p in range(30, -1, -1):
        if usable_hosts(p) >= hosts:
            return p
    raise ValueError("too many hosts for IPv4")


def block_size_explanation(cidr: str) -> str:
    """Explain the network address with the 'magic number' method taught for Network+/CCNA."""
    info = analyse(cidr)
    p = info.prefix
    octets = [int(o) for o in str(info.address).split(".")]
    if p % 8 == 0:
        keep = p // 8
        return (
            f"/{p} ends on an octet boundary, so keep the first {keep} octet(s) "
            f"and zero the rest: {info.network.network_address}."
        )
    idx = p // 8  # the "interesting" octet
    mask_octet = int(str(info.netmask).split(".")[idx])
    block = 256 - mask_octet
    start = (octets[idx] // block) * block
    names = ["1st", "2nd", "3rd", "4th"]
    return (
        f"Mask is {info.netmask}. The interesting octet is the {names[idx]} ({mask_octet}), "
        f"so the block size is 256 - {mask_octet} = {block}. "
        f"{octets[idx]} falls in the block {start}-{start + block - 1}, "
        f"so the network is {info.network.network_address} "
        f"and the broadcast is {info.broadcast}."
    )


def describe(cidr: str) -> str:
    """Multi-line breakdown used by the `calc` command."""
    i = analyse(cidr)
    rows = [
        ("Address", i.address, to_binary(i.address)),
        ("Netmask", f"{i.netmask} (/{i.prefix})", to_binary(i.netmask)),
        ("Wildcard", i.wildcard, to_binary(i.wildcard)),
        ("Network", i.network.network_address, to_binary(i.network.network_address)),
        ("Broadcast", i.broadcast, to_binary(i.broadcast)),
        ("First host", i.first_host, ""),
        ("Last host", i.last_host, ""),
        ("Usable hosts", f"{i.usable_hosts:,}", ""),
        ("Private", "yes" if i.address.is_private else "no", ""),
    ]
    width = max(len(str(v)) for _, v, _ in rows)
    lines = [f"{k:<13} {str(v):<{width}}  {b}".rstrip() for k, v, b in rows]
    lines.append("")
    lines.append(block_size_explanation(cidr))
    return "\n".join(lines)
