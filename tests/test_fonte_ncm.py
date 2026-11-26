from brfiscal.fontes.ncm import converter

AMOSTRA = {
    "Data_Ultima_Atualizacao_NCM": "Vigente em 26/11/2026",
    "Ato": "Resolução Gecex nº 926/2026",
    "Nomenclaturas": [
        {
            "Codigo": "19",
            "Descricao": "Preparações à base de cereais",
            "Data_Inicio": "01/04/2022",
            "Data_Fim": "31/12/9999",
        },
        {
            "Codigo": "19.05",
            "Descricao": "Produtos de padaria",
            "Data_Inicio": "01/04/2022",
            "Data_Fim": "31/12/9999",
        },
        {
            "Codigo": "1905.90",
            "Descricao": "- Outros",
            "Data_Inicio": "01/04/2022",
            "Data_Fim": "31/12/9999",
        },
        {
            "Codigo": "1905.90.10",
            "Descricao": "Pão de <i>forma</i>",
            "Data_Inicio": "01/04/2022",
            "Data_Fim": "31/12/2026",
            "Tipo_Ato_Ini": "Res Gecex",
            "Numero_Ato_Ini": "272",
            "Ano_Ato_Ini": "2021",
        },
    ],
}


def test_converter():
    meta, itens = converter(AMOSTRA)
    assert meta["vigencia"] == "2026-11-26"
    assert meta["ato"] == "Resolução Gecex nº 926/2026"
    folha = itens[-1]
    assert folha == {
        "c": "19059010",
        "d": "Pão de forma",
        "dc": "Produtos de padaria > Outros > Pão de forma",
        "p": ["19", "1905", "190590"],
        "i": "2022-04-01",
        "f": "2026-12-31",
        "a": "Res Gecex 272 2021",
    }
    assert "f" not in itens[0]  # 31/12/9999 = sem fim
