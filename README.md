# subnet-trainer

![tests](https://github.com/alexandruraad/subnet-trainer/actions/workflows/tests.yml/badge.svg)

A small command-line trainer for the networking basics that come up in Network+, CCNA and SOC interviews: subnetting, OSI layers, ports, and TCP vs UDP.

I built it while studying for CompTIA Network+. Flashcards were fine for remembering ports, but they didn't help with subnetting. For that you need endless fresh questions, and when you get one wrong you need to see *why*. So every question here is generated randomly, and every wrong answer shows the working using the block-size ("magic number") method.

No dependencies, just the Python standard library.

## Install

```bash
git clone https://github.com/alexandruraad/subnet-trainer.git
cd subnet-trainer
pip install -e .
```

Or run it without installing: `python -m subnet_trainer ...`

## Usage

### Quiz

```bash
subnet-trainer quiz                         # 10 mixed subnetting questions
subnet-trainer quiz -n 20 -d hard           # longer, with prefixes down to /9
subnet-trainer quiz -t concepts             # OSI layers, ports, TCP/UDP
subnet-trainer quiz -t network,broadcast    # drill specific topics
subnet-trainer quiz --seed 42               # same questions every time
```

```
[3/4] Network address of 192.168.52.174/18?
> 192.168.0.0
Correct.

[4/4] Write /25 as a dotted-decimal subnet mask.
> 255.255.255.0
Not quite. Answer: 255.255.255.128
  /25 = 25 ones then 7 zeros: 11111111.11111111.11111111.10000000 = 255.255.255.128.

Score: 3/4 (75%) in 41s
```

| Topic | Asks for |
|---|---|
| `network`, `broadcast` | network / broadcast address of a host |
| `first-host`, `last-host` | usable range |
| `hosts` | usable hosts in a prefix |
| `mask`, `wildcard` | prefix to dotted mask, or ACL wildcard mask |
| `size` | smallest prefix that fits N hosts (VLSM) |
| `same-subnet` | whether two hosts can talk without a router |
| `osi`, `ports`, `tcp-udp` | concepts (group: `concepts`) |

Answers are forgiving: `/26`, `26` and `255.255.255.192` all count for a prefix, and `2`, `l2` and `data link` all count for an OSI layer.

### Calculator

```
$ subnet-trainer calc 172.16.45.200/20
Address       172.16.45.200        10101100.00010000.00101101.11001000
Netmask       255.255.240.0 (/20)  11111111.11111111.11110000.00000000
Wildcard      0.0.15.255           00000000.00000000.00001111.11111111
Network       172.16.32.0          10101100.00010000.00100000.00000000
Broadcast     172.16.47.255        10101100.00010000.00101111.11111111
First host    172.16.32.1
Last host     172.16.47.254
Usable hosts  4,094
Private       yes

Mask is 255.255.240.0. The interesting octet is the 3rd (240), so the block size is 256 - 240 = 16. 45 falls in the block 32-47, so the network is 172.16.32.0 and the broadcast is 172.16.47.255.
```

It also accepts a dotted mask: `subnet-trainer calc 10.1.2.3 255.255.240.0`.

### Stats

Your results are saved to `~/.subnet-trainer/stats.json`, so you can see where you're weakest (example output):

```
$ subnet-trainer stats
topic            score  accuracy
size            6/11        55%  ######
broadcast       9/12        75%  ########
hosts          14/15        93%  #########

Weakest topic: size. Drill it with: subnet-trainer quiz --topics size
```

## Notes

- `/31` and `/32` follow RFC 3021: a /31 has 2 usable addresses (point-to-point links), and a /32 is a single host. Quiz questions stay between /9 and /30 to avoid edge-case arguments.
- ARP and TLS are left out of the OSI questions on purpose, because which layer they belong to is genuinely debated.
- Port answers follow the classic exam answers (for example HTTPS = TCP 443, even though HTTP/3 runs over UDP).

## Development

```bash
pip install -e ".[dev]"
pytest
```

The tests generate thousands of questions and check that every answer passes its own checker, and they independently verify the `same-subnet` answers.

## Roadmap

- [ ] IPv6 questions (prefix length, address compression)
- [ ] VLSM scenario mode: split a block for several departments
- [ ] Timed "exam mode" with a countdown
- [ ] Binary / hex conversion drills

## License

MIT
