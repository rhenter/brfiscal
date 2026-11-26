from brfiscal.__main__ import main


def test_info(capsys):
    assert main(["info"]) == 0
    saida = capsys.readouterr().out
    assert "ncm:" in saida and "cest:" in saida


def test_buscar(capsys):
    assert main(["buscar", "ncm", "papel higienico", "--limite", "1"]) == 0
    assert "4818.10.00" in capsys.readouterr().out
