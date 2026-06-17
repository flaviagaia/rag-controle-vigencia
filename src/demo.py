"""Demo: RAG sem vs com controle de vigência (~1s).

    python src/demo.py
"""

from __future__ import annotations

from pathlib import Path

from vigencia import Retriever, load_normas, naive, vigencia_aware

ROOT = Path(__file__).parent.parent

# Consultas "atuais": a resposta certa é a norma VIGENTE.
ATUAIS = [
    ("Qual o valor do repasse por aluno matriculado no Programa Alfa?", "res2024_repasse"),
    ("Qual o prazo de prestação de contas do Programa Alfa?", "res2024_prazo"),
    ("Quem é elegível ao Programa Alfa?", "res2024_elegib"),
]
# Consulta histórica: o que valia em 2023.
HISTORICA = ("Qual era o prazo de prestação de contas do Programa Alfa em 2023?", 2023, "res2023_prazo")


def main() -> None:
    normas = load_normas(ROOT / "data" / "normas.json")
    r = Retriever(normas)

    print("=" * 74)
    print("Controle de vigência: não citar norma revogada (H3)")
    print("=" * 74)

    cita_revogada = {"naive": 0, "aware": 0}
    acerto = {"naive": 0, "aware": 0}
    for q, gold in ATUAIS:
        n = naive(r, q)
        a = vigencia_aware(r, q)
        cita_revogada["naive"] += not n.vigente
        cita_revogada["aware"] += (a is not None and not a.vigente)
        acerto["naive"] += n.id == gold
        acerto["aware"] += (a is not None and a.id == gold)
        print(f"\nP: {q}")
        print(f"   ingênuo  : {n.rotulo} -> \"{n.texto}\""
              f"{'   [REVOGADA!]' if not n.vigente else ''}")
        print(f"   vigência : {a.rotulo} -> \"{a.texto}\"")

    print("\n" + "-" * 74)
    print(f"Citações de norma REVOGADA (em consultas atuais): "
          f"ingênuo {cita_revogada['naive']}/{len(ATUAIS)}, "
          f"com vigência {cita_revogada['aware']}/{len(ATUAIS)}")
    print(f"Acerto da norma vigente: ingênuo {acerto['naive']}/{len(ATUAIS)}, "
          f"com vigência {acerto['aware']}/{len(ATUAIS)}")

    # Consulta histórica: o controle de vigência resolve "vigente em tal data"
    q, ano, gold = HISTORICA
    a = vigencia_aware(r, q, ano=ano)
    print("\n" + "-" * 74)
    print(f"Consulta histórica: {q}")
    print(f"   com vigência (em {ano}): {a.rotulo} -> \"{a.texto}\""
          f"  {'✓' if a.id == gold else '✗'}")
    print("   (o ingênuo não sabe a data: responderia a regra mais parecida, sem recorte temporal)")


if __name__ == "__main__":
    main()
