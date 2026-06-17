"""Controle de vigência: não citar norma revogada (Hipótese H3).

Quando a norma nova convive com a antiga no índice, a busca por similaridade pode
devolver a REVOGADA (textos quase idênticos, muda só o valor). Em jurídico, citar
norma fora de vigência é erro factual grave. O controle de vigência filtra os
candidatos pela validade antes de responder.

Reaproveita a marcação de vigência da ingestão (cada nó tem vigente/inicio/fim/
revogado_por). Suporta também "vigente em uma data X" (consulta histórica).

- naive          : responde com o melhor match, ignorando a vigência.
- vigencia_aware : descarta o que não está vigente (ou não valia na data pedida)
                   e responde com o melhor match VÁLIDO.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class Norma:
    id: str
    rotulo: str
    texto: str
    vigente: bool
    inicio: int
    fim: int | None
    revogado_por: str | None


def load_normas(path: Path) -> list[Norma]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Norma(**n) for n in data["nodes"]]


def valida_em(n: Norma, ano: int) -> bool:
    """A norma estava em vigor no ano dado?"""
    return n.inicio <= ano and (n.fim is None or ano < n.fim)


class Retriever:
    def __init__(self, normas: list[Norma]) -> None:
        self.normas = normas
        self._vec = TfidfVectorizer(ngram_range=(1, 2), strip_accents="unicode")
        self._mat = self._vec.fit_transform(f"{n.rotulo} {n.texto}" for n in normas)

    def ranked(self, query: str) -> list[Norma]:
        sims = cosine_similarity(self._vec.transform([query]), self._mat).ravel()
        return [self.normas[i] for i in sims.argsort()[::-1]]


def naive(retriever: Retriever, query: str) -> Norma:
    """Ignora a vigência: pega o melhor match, mesmo se revogado."""
    return retriever.ranked(query)[0]


def vigencia_aware(retriever: Retriever, query: str, ano: int | None = None) -> Norma | None:
    """Filtra pela vigência. Sem ano -> usa a flag 'vigente' (norma atual).
    Com ano -> resolve o que valia naquela data (consulta histórica)."""
    for n in retriever.ranked(query):
        ok = valida_em(n, ano) if ano is not None else n.vigente
        if ok:
            return n
    return None
