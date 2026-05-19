import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

nltk.download('stopwords', quiet=True)

_STOPWORDS = set(stopwords.words('english'))
# Termos ubíquos em abstracts científicos que não discriminam tema
_STOPWORDS |= {'paper', 'study', 'results', 'proposed', 'approach', 'method',
               'model', 'using', 'based', 'show', 'present', 'also', 'task'}

_stemmer = PorterStemmer()


def preprocess(text: str) -> list[str]:
    """Tokeniza, remove stopwords e aplica Porter stemmer."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in _STOPWORDS and len(t) > 1]
    tokens = [_stemmer.stem(t) for t in tokens]
    return tokens


def preprocess_str(text: str) -> str:
    """Versão que retorna string (para TfidfVectorizer)."""
    return ' '.join(preprocess(text))


def doc_text(doc: dict) -> str:
    """Concatena título + abstract de um documento do corpus."""
    return doc.get('title', '') + ' ' + doc.get('abstract', '')
