import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, RSLPStemmer

nltk.download('stopwords', quiet=True)
nltk.download('rslp', quiet=True)

_STOP_EN = set(stopwords.words('english'))
_STOP_EN |= {'paper', 'study', 'results', 'proposed', 'approach', 'method',
              'model', 'using', 'based', 'show', 'present', 'also', 'task'}

_STOP_PT = set(stopwords.words('portuguese'))
_STOP_PT |= {'artigo', 'trabalho', 'estudo', 'resultados', 'proposta',
              'método', 'modelo', 'utilização', 'partir', 'ainda', 'assim'}

_STOP_ALL = _STOP_EN | _STOP_PT

_stemmer_en = PorterStemmer()
_stemmer_pt = RSLPStemmer()

# Heurística simples de detecção de idioma
_PT_MARKERS = {'de', 'da', 'do', 'dos', 'das', 'em', 'para', 'com', 'uma',
               'não', 'são', 'foi', 'pelo', 'pela', 'entre', 'sobre', 'como',
               'mais', 'pode', 'sua', 'seu', 'esse', 'esta', 'públic',
               'licitação', 'contratação', 'compras', 'públicas', 'público',
               'documentos', 'análise', 'classificação', 'tribunal',
               'auditoria', 'lei', 'artigo', 'administração', 'governo'}


def detect_lang(text: str) -> str:
    """Detecta idioma por proporção de palavras-marcador PT."""
    words = set(text.lower().split()[:50])
    pt_hits = len(words & _PT_MARKERS)
    return 'pt' if pt_hits >= 3 else 'en'


def preprocess(text: str, lang: str = None) -> list[str]:
    """Tokeniza, remove stopwords e aplica stemmer (bilíngue)."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = text.split()

    if lang is None:
        lang = detect_lang(text)

    tokens = [t for t in tokens if t not in _STOP_ALL and len(t) > 1]

    if lang == 'pt':
        tokens = [_stemmer_pt.stem(t) for t in tokens]
    else:
        tokens = [_stemmer_en.stem(t) for t in tokens]

    return tokens


def preprocess_str(text: str, lang: str = None) -> str:
    """Versão que retorna string (para TfidfVectorizer)."""
    return ' '.join(preprocess(text, lang))


def doc_text(doc: dict) -> str:
    """Concatena título + abstract de um documento do corpus."""
    return doc.get('title', '') + ' ' + doc.get('abstract', '')
