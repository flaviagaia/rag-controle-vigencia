# rag-controle-vigencia

Controle de vigência num RAG jurídico: **não citar norma revogada** (Hipótese H3).

> **Em uma frase:** quando a norma nova convive com a antiga no índice, a busca por
> similaridade pode devolver a **revogada** (textos quase idênticos, muda só o
> valor); filtrar os candidatos pela vigência antes de responder elimina esse erro.

> *Versioning control in a legal RAG: don't cite a repealed rule. A naive retriever
> can rank an old, repealed norm first because its wording matches the question; a
> validity filter discards out-of-force candidates before answering, and also
> resolves "what was in force on date X".*

---

## O problema

Em texto normativo, a versão nova de uma regra **revoga** a anterior, mas a anterior
continua existindo (em PDFs, no histórico, no índice do RAG). As duas são quase
iguais: muda só o número (R$ 80 → R$ 100; 30 → 60 dias). Para a busca vetorial elas
são praticamente o mesmo documento, e nada impede a **revogada** de ficar em primeiro
lugar. Citar norma fora de vigência é um erro factual grave em qualquer aplicação
jurídica.

Este repo reaproveita a marcação de vigência produzida na ingestão
(`rag-ingestao-legislacao`): cada nó tem `vigente`, `inicio`, `fim` e `revogado_por`.

## Como funciona (o técnico)

Dois sistemas sobre o mesmo retriever TF-IDF (n-gramas 1–2, sem acento):

- `naive` — devolve o melhor match por similaridade, **ignorando a vigência**.
- `vigencia_aware` — percorre o ranking e devolve o **primeiro candidato válido**.
  Sem data, usa a flag `vigente` (a norma atual). Com `ano=X`, usa
  `valida_em(n, X)` e resolve o que valia naquela data (consulta histórica).

```
valida_em(n, ano) = (n.inicio <= ano) e (n.fim é None ou ano < n.fim)

vigencia_aware(query, ano=None):
    para n em ranking_por_similaridade(query):
        ok = valida_em(n, ano) se ano dado, senão n.vigente
        se ok: retorna n      # primeiro válido
    retorna None              # nada válido -> melhor abster
```

Complexidade: a do retriever (uma multiplicação esparsa query × matriz), mais uma
varredura linear `O(k)` no ranking até achar o primeiro válido. O filtro de vigência
é praticamente de graça.

## Resultado (determinístico, offline)

Corpus fictício com pares revogada/vigente (repasse R$ 80 → R$ 100; prazo 30 → 60
dias). A norma nova **reescreve** o texto (outras palavras); a antiga, mais literal,
casa melhor com a pergunta, então a busca tende a trazer a revogada.

| Métrica (3 consultas atuais)            | Ingênuo | Com vigência |
| --------------------------------------- | ------- | ------------ |
| Citações de norma **revogada**          | **2/3** | **0/3**      |
| Acerto da norma vigente correta         | 1/3     | **3/3**      |

Consulta histórica ("qual era o prazo **em 2023**?") → `vigencia_aware(ano=2023)`
devolve a Resolução 18/2023 (30 dias), correta para a data. O ingênuo não tem recorte
temporal: responderia a regra mais parecida, sem saber a data.

Rode você mesmo:

```bash
pip install -r requirements.txt
python src/demo.py
python -m pytest -q
```

## Como explicar em 30 segundos

"A lei muda mas a versão antiga não some do índice. Como o texto é quase igual, a
busca pode citar a regra **revogada**. Eu filtro os candidatos pela vigência antes de
responder: nunca cito norma fora de vigor, e ainda consigo responder 'o que valia em
tal data'."

## Limitações honestas

- Corpus pequeno e fictício, escolhido para o efeito ser claro e reproduzível. O
  ponto é o **mecanismo** (filtrar por vigência), não a magnitude do número.
- O texto da norma nova foi redigido para que a revogada vencesse o ranking de forma
  determinística. Em corpus real a falha do ingênuo é **intermitente** (depende do
  quão parecidos são os textos), o que é justamente o risco: você não sabe quando vai
  citar a revogada.
- O filtro depende da qualidade da marcação de vigência na ingestão. Vigência mal
  extraída (revogação tácita, vigência parcial, vacatio legis) propaga o erro.
- `valida_em` usa granularidade de ano para simplificar; datas reais (dia/mês,
  vigência futura) são uma extensão direta do mesmo predicado.

## Referências científicas (crédito aos autores)

- **Lewis et al. (2020).** *Retrieval-Augmented Generation for Knowledge-Intensive
  NLP Tasks.* NeurIPS. Formulação do RAG.
- **Yan et al. (2024).** *Corrective Retrieval Augmented Generation (CRAG).* arXiv:2401.15884.
  Avaliar/filtrar o que foi recuperado antes de gerar; aqui o filtro é a vigência.
- **Robertson & Zaragoza (2009).** *The Probabilistic Relevance Framework: BM25 and
  Beyond.* Base de recuperação por similaridade léxica.
- O corpus é fictício; a modelagem de vigência segue a praxe da técnica legislativa
  brasileira (LC 95/1998) de identificar a norma revogadora e a data de eficácia.

Bibliografia completa do portfólio em `REFERENCIAS.md`.

---

Part of my LinkedIn series on efficient RAG → [Flávia Gaia](https://www.linkedin.com/in/flavia-gaia/)
