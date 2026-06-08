import time
import csv
import re
import math
from functools import reduce

def timed(func):
    def wrapper(*args, **kwargs):
        t0 = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - t0:.4f}s")
        return result
    return wrapper


@timed
def load_data():
    with open('/home/ubuntu/project/Amazon_Reviews.csv') as f:
        reader = csv.reader(f)
        next(reader)
        texts = [row[7] for row in reader if len(row) > 7 and row[7].strip()]
    print(f"  Reviews: {len(texts)}")
    return texts


tokenize = lambda text: list(filter(None, re.sub(r'[^a-zA-Z0-9 ]+', ' ', text).lower().split(' ')))
clean = lambda tokens: list(filter(lambda t: len(t) > 2, tokens))


@timed
def compute_tf(texts):
    result = []
    for text in texts:
        tokens = clean(tokenize(text))
        if not tokens:
            result.append({})
            continue
        counts = {}
        for t in tokens:
            counts[t] = counts.get(t, 0) + 1
        n = len(tokens)
        result.append({t: c / n for t, c in counts.items()})
    return result


@timed
def compute_idf(tf_list, n_docs):
    doc_freq = reduce(lambda d, tf: (d.update({t: d.get(t, 0) + 1 for t in tf}) or d), tf_list, {})
    idf = {t: math.log(n_docs / df) for t, df in doc_freq.items()}
    return idf, doc_freq


@timed
def compute_tfidf(tf_list, idf, doc_freq):
    doc_tfidfs = list(map(lambda tf: {t: tf[t] * idf[t] for t in tf}, tf_list))
    agg = reduce(lambda a, d: (a[0].update({t: a[0].get(t, 0) + v for t, v in d.items()}) or a), doc_tfidfs, ({},))
    sum_tfidf = agg[0]
    n = len(doc_tfidfs)
    terms = sorted(sum_tfidf.keys(), key=lambda t: -sum_tfidf[t] / max(doc_freq.get(t, 1), 1))[:20]
    return [(t, sum_tfidf[t] / n, doc_freq.get(t, 0)) for t in terms]


texts = load_data()
tf_list = compute_tf(texts)
n_docs = len(texts)
idf, doc_freq = compute_idf(tf_list, n_docs)
top_terms = compute_tfidf(tf_list, idf, doc_freq)

print("\nTop 20 TF-IDF terms:")
for term, avg, freq in top_terms:
    print(f"  {term:<30} avg_tfidf={avg:.6f}  doc_freq={freq}")
