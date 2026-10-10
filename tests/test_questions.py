import ipaddress
import random

import pytest

from subnet_trainer import core
from subnet_trainer.cli import main, run_quiz
from subnet_trainer.questions import ALL_TOPICS, generate


@pytest.mark.parametrize("topic", list(ALL_TOPICS))
@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_generated_answer_passes_its_own_checker(topic, difficulty):
    rng = random.Random(1234)
    for _ in range(200):
        q = generate([topic], rng, difficulty)
        assert q.check(q.answer.split(" ")[0]), q


def test_wrong_and_garbage_answers_fail():
    q = generate(["network"], random.Random(1), "easy")
    assert not q.check("not an ip")
    assert not q.check("")
    assert not q.check("1.2.3.4") or q.answer == "1.2.3.4"


def test_same_subnet_answers_are_actually_right():
    rng = random.Random(7)
    for _ in range(300):
        q = generate(["same-subnet"], rng, "hard")
        # prompt: "Are A and B on the same /P subnet? (yes/no)"
        words = q.prompt.split()
        a, b, p = words[1], words[3], int(words[7].lstrip("/"))
        same = ipaddress.IPv4Address(b) in core.analyse(f"{a}/{p}").network
        assert q.answer == ("yes" if same else "no")


def test_prefix_answer_accepts_mask_or_slash():
    rng = random.Random(3)
    q = generate(["size"], rng, "easy")
    p = int(q.answer.lstrip("/"))
    assert q.check(f"/{p}") and q.check(str(p)) and q.check(str(core.prefix_to_mask(p)))


def test_run_quiz_with_scripted_answers():
    rng = random.Random(0)
    answers = iter(["wrong", "q"])
    lines = []
    results = run_quiz(["hosts"], 5, "easy", rng, ask=lambda _: next(answers), out=lines.append)
    assert results == [("hosts", False)]
    assert any("Answer:" in line for line in lines)


def test_cli_calc(capsys):
    assert main(["calc", "192.168.1.130/25"]) == 0
    assert "192.168.1.128" in capsys.readouterr().out


def test_cli_rejects_unknown_topic():
    with pytest.raises(SystemExit):
        main(["quiz", "--topics", "nope"])
