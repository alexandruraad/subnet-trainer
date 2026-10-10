import pytest

from subnet_trainer import core


def test_analyse_slash_26():
    i = core.analyse("192.168.10.77/26")
    assert str(i.network) == "192.168.10.64/26"
    assert str(i.broadcast) == "192.168.10.127"
    assert str(i.first_host) == "192.168.10.65"
    assert str(i.last_host) == "192.168.10.126"
    assert str(i.netmask) == "255.255.255.192"
    assert str(i.wildcard) == "0.0.0.63"
    assert i.usable_hosts == 62


def test_dotted_mask_input():
    assert core.analyse("10.1.2.3 255.255.240.0").prefix == 20


def test_missing_prefix_is_an_error():
    with pytest.raises(ValueError):
        core.analyse("10.1.2.3")


@pytest.mark.parametrize("prefix,hosts", [(24, 254), (30, 2), (31, 2), (32, 1), (16, 65534)])
def test_usable_hosts(prefix, hosts):
    assert core.usable_hosts(prefix) == hosts


def test_point_to_point_31():
    i = core.analyse("10.0.0.0/31")
    assert str(i.first_host) == "10.0.0.0"
    assert str(i.last_host) == "10.0.0.1"


@pytest.mark.parametrize("hosts,prefix", [(2, 30), (3, 29), (30, 27), (62, 26), (63, 25), (500, 23)])
def test_smallest_prefix_for_hosts(hosts, prefix):
    assert core.smallest_prefix_for_hosts(hosts) == prefix


def test_to_binary():
    assert core.to_binary("192.168.1.1") == "11000000.10101000.00000001.00000001"


def test_block_size_explanation_mentions_block():
    text = core.block_size_explanation("172.16.45.200/20")
    assert "block size is 256 - 240 = 16" in text
    assert "172.16.32.0" in text and "172.16.47.255" in text


def test_block_size_on_octet_boundary():
    assert "10.20.0.0" in core.block_size_explanation("10.20.30.40/16")


def test_describe_runs():
    out = core.describe("10.4.77.130/27")
    assert "10.4.77.128" in out and "Usable hosts" in out
