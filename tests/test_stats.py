from subnet_trainer import stats


def test_record_and_report(tmp_path):
    path = tmp_path / "stats.json"
    stats.record([("hosts", True), ("mask", False), ("mask", True)], path)
    stats.record([("mask", False)], path)
    data = stats.load(path)
    assert data["hosts"] == {"correct": 1, "total": 1}
    assert data["mask"] == {"correct": 1, "total": 3}
    assert "Weakest topic: mask" in stats.report(data)


def test_empty_report():
    assert "No stats yet" in stats.report({})
