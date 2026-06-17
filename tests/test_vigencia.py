import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vigencia import Retriever, load_normas, naive, valida_em, vigencia_aware  # noqa: E402

NORMAS = load_normas(ROOT / "data" / "normas.json")
R = Retriever(NORMAS)

Q_REPASSE = "Qual o valor do repasse por aluno matriculado no Programa Alfa?"
Q_PRAZO = "Qual o prazo de prestação de contas do Programa Alfa?"


def test_dados_tem_par_revogada_vigente():
    ids = {n.id for n in NORMAS}
    assert {"res2022_repasse", "res2024_repasse"} <= ids
    assert any(not n.vigente for n in NORMAS)
    assert any(n.vigente for n in NORMAS)


def test_naive_cita_norma_revogada():
    # O sistema ingênuo, sem controle de vigência, traz a norma revogada.
    n = naive(R, Q_REPASSE)
    assert n.id == "res2022_repasse"
    assert n.vigente is False


def test_vigencia_aware_nunca_cita_revogada():
    for q in (Q_REPASSE, Q_PRAZO, "Quem é elegível ao Programa Alfa?"):
        a = vigencia_aware(R, q)
        assert a is not None
        assert a.vigente is True


def test_vigencia_aware_traz_a_vigente_certa():
    assert vigencia_aware(R, Q_REPASSE).id == "res2024_repasse"
    assert vigencia_aware(R, Q_PRAZO).id == "res2024_prazo"


def test_valida_em_recorte_temporal():
    por_id = {n.id: n for n in NORMAS}
    antiga, nova = por_id["res2023_prazo"], por_id["res2024_prazo"]
    # Em 2023 valia a antiga (30 dias); a nova ainda não existia.
    assert valida_em(antiga, 2023) is True
    assert valida_em(nova, 2023) is False
    # Em 2025 vale a nova; a antiga já foi revogada.
    assert valida_em(antiga, 2025) is False
    assert valida_em(nova, 2025) is True


def test_consulta_historica_resolve_o_que_valia_na_data():
    a = vigencia_aware(R, Q_PRAZO, ano=2023)
    assert a.id == "res2023_prazo"  # 30 dias, vigente em 2023


def test_contraste_agregado():
    atuais = [
        (Q_REPASSE, "res2024_repasse"),
        (Q_PRAZO, "res2024_prazo"),
        ("Quem é elegível ao Programa Alfa?", "res2024_elegib"),
    ]
    rev_naive = sum(not naive(R, q).vigente for q, _ in atuais)
    rev_aware = sum(not vigencia_aware(R, q).vigente for q, _ in atuais)
    assert rev_naive >= 2  # ingênuo cita revogada
    assert rev_aware == 0  # com vigência, nunca
