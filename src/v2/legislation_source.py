"""
legislation_source.py — Busca legislação federal brasileira relevante.
Combina: (1) base local curada de normas TIC/nuvem + (2) busca no LexML via scraping.
"""
import re
import requests
from dataclasses import dataclass

# Base curada: legislação federal relevante para contratações TIC/nuvem
LEGISLATION_DB = [
    {"tipo": "Lei", "numero": "14.133", "ano": 2021,
     "ementa": "Lei de Licitações e Contratos Administrativos",
     "url": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/L14133.htm",
     "tags": ["licitação", "contrato", "contratação", "administração pública", "pregão", "dispensa"]},
    {"tipo": "Decreto", "numero": "10.947", "ano": 2022,
     "ementa": "Regulamenta o inciso VII do caput do art. 12 da Lei nº 14.133/2021, para dispor sobre o plano de contratações anual",
     "url": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/decreto/D10947.htm",
     "tags": ["contratação", "planejamento", "TIC", "plano de contratações"]},
    {"tipo": "Decreto", "numero": "10.332", "ano": 2020,
     "ementa": "Institui a Estratégia de Governo Digital 2020-2022",
     "url": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/decreto/D10332.htm",
     "tags": ["governo digital", "transformação digital", "nuvem", "cloud"]},
    {"tipo": "Instrução Normativa", "numero": "SGD/ME nº 1", "ano": 2019,
     "ementa": "Dispõe sobre o processo de contratação de soluções de TIC",
     "url": "https://www.gov.br/governodigital/pt-br/contratacoes",
     "tags": ["TIC", "contratação", "ETP", "termo de referência", "solução de TI"]},
    {"tipo": "Instrução Normativa", "numero": "SGD/ME nº 94", "ano": 2022,
     "ementa": "Dispõe sobre o processo de contratação de soluções de TIC pelos órgãos e entidades integrantes do SISP",
     "url": "https://www.gov.br/governodigital/pt-br/contratacoes",
     "tags": ["TIC", "SISP", "contratação", "planejamento", "nuvem"]},
    {"tipo": "Portaria", "numero": "SGD/MGI nº 5.950", "ano": 2023,
     "ementa": "Dispõe sobre a contratação de serviços de computação em nuvem",
     "url": "https://www.gov.br/governodigital/pt-br/contratacoes/portaria-sgd-mgi-no-5950",
     "tags": ["nuvem", "cloud", "IaaS", "PaaS", "SaaS", "computação em nuvem", "contratação"]},
    {"tipo": "Decreto", "numero": "11.856", "ano": 2023,
     "ementa": "Institui a Política Nacional de Cibersegurança",
     "url": "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/decreto/D11856.htm",
     "tags": ["segurança", "cibersegurança", "dados", "proteção"]},
    {"tipo": "Lei", "numero": "13.709", "ano": 2018,
     "ementa": "Lei Geral de Proteção de Dados Pessoais (LGPD)",
     "url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm",
     "tags": ["dados", "proteção", "privacidade", "LGPD", "tratamento de dados"]},
    {"tipo": "Decreto", "numero": "9.637", "ano": 2018,
     "ementa": "Institui a Política Nacional de Segurança da Informação",
     "url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/decreto/d9637.htm",
     "tags": ["segurança da informação", "dados", "classificação", "governo"]},
    {"tipo": "Decreto", "numero": "11.246", "ano": 2022,
     "ementa": "Estratégia Nacional de Governo Digital 2024-2027",
     "url": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/decreto/D11260.htm",
     "tags": ["governo digital", "transformação digital", "nuvem", "EGD"]},
    {"tipo": "Acórdão TCU", "numero": "1.503/2020", "ano": 2020,
     "ementa": "Diretrizes sobre contratações de computação em nuvem no setor público",
     "url": "https://portal.tcu.gov.br/",
     "tags": ["nuvem", "TCU", "contratação", "auditoria", "cloud"]},
    {"tipo": "Acórdão TCU", "numero": "2.569/2019", "ano": 2019,
     "ementa": "Governança e gestão de TI na Administração Pública Federal",
     "url": "https://portal.tcu.gov.br/",
     "tags": ["TI", "governança", "gestão", "administração pública"]},
]


@dataclass
class LegislationResult:
    tipo: str
    numero: str
    ano: int
    ementa: str
    url: str
    relevance_score: float


def search_legislation(query: str, top_n: int = 10) -> list[LegislationResult]:
    """Busca legislação relevante na base curada por matching de tags + texto."""
    query_lower = query.lower()
    query_terms = set(re.findall(r'\w+', query_lower))

    results = []
    for norma in LEGISLATION_DB:
        # Score: contagem de tags que matcham + match na ementa
        score = 0
        for tag in norma["tags"]:
            tag_terms = set(re.findall(r'\w+', tag.lower()))
            if tag_terms & query_terms:
                score += 2
            if tag.lower() in query_lower:
                score += 3
        # Match na ementa
        ementa_terms = set(re.findall(r'\w+', norma["ementa"].lower()))
        score += len(ementa_terms & query_terms)

        if score > 0:
            results.append(LegislationResult(
                tipo=norma["tipo"], numero=norma["numero"],
                ano=norma["ano"], ementa=norma["ementa"],
                url=norma["url"], relevance_score=score
            ))

    results.sort(key=lambda r: -r.relevance_score)
    return results[:top_n]


def search_lexml(query: str, max_results: int = 5) -> list[LegislationResult]:
    """Busca complementar no LexML (scraping leve da página de resultados)."""
    try:
        url = "https://www.lexml.gov.br/busca/search"
        params = {"keyword": query, "tipoDocumento": "Legislacao"}
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            return []

        # Extrair títulos e URNs do HTML de resultados
        results = []
        titles = re.findall(r'<a[^>]*class="title"[^>]*>([^<]+)</a>', resp.text)
        links = re.findall(r'href="(urn:lex:br[^"]*)"', resp.text)

        for i, title in enumerate(titles[:max_results]):
            urn = links[i] if i < len(links) else ""
            # Parse tipo e número do título
            results.append(LegislationResult(
                tipo="Norma", numero=title[:50], ano=0,
                ementa=title, url=f"https://www.lexml.gov.br/{urn}",
                relevance_score=max_results - i
            ))
        return results
    except Exception:
        return []


def search_all(queries: list[str], top_n: int = 10) -> list[LegislationResult]:
    """Busca em todas as fontes e deduplica."""
    all_results = []
    seen = set()
    for q in queries:
        for r in search_legislation(q, top_n=5):
            key = f"{r.tipo}-{r.numero}"
            if key not in seen:
                seen.add(key)
                all_results.append(r)
        for r in search_lexml(q, max_results=3):
            key = r.ementa[:50]
            if key not in seen:
                seen.add(key)
                all_results.append(r)
    all_results.sort(key=lambda r: -r.relevance_score)
    return all_results[:top_n]


if __name__ == "__main__":
    results = search_legislation("contratação computação em nuvem administração pública")
    print(f"Resultados da base curada ({len(results)}):")
    for r in results:
        print(f"  [{r.relevance_score:.0f}] {r.tipo} {r.numero}/{r.ano} — {r.ementa[:70]}")
