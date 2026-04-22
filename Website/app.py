import os
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH  = os.path.join(BASE, '..', 'cleaning', 'cleaned_data.csv')
INDEX_PATH = os.path.join(BASE, '..', 'AI_features', 'vezeeta_faiss.index')

print("Loading data...")
df = pd.read_csv(DATA_PATH, encoding='latin-1')
text_cols = ['Speciality', 'symptoms_text', 'subspecialties_text', 'description', 'about_doctor']
df[text_cols] = df[text_cols].fillna('')
df['search_text'] = (
    df['Speciality'] + ' | ' +
    df['symptoms_text'] + ' | ' +
    df['subspecialties_text'] + ' | ' +
    df['description']
).str[:512]
df = df[df['search_text'].str.strip().str.len() > 10].reset_index(drop=True)

print("Loading model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

print("Loading FAISS index...")
index = faiss.read_index(INDEX_PATH)
print(f"Ready — {index.ntotal:,} doctors indexed.")

app = Flask(__name__, static_folder='.')
CORS(app)


@app.route('/')
def index_page():
    return send_from_directory('.', 'vezeeta2.html')


@app.route('/api/recommend', methods=['POST'])
def recommend():
    data = request.get_json(force=True)
    query = (data.get('query') or '').strip()
    if not query:
        return jsonify({'error': 'query is required'}), 400

    max_fee   = data.get('max_fee')
    city      = (data.get('city') or '').strip()
    specialty = (data.get('specialty') or '').strip()
    top_k     = min(int(data.get('top_k', 5)), 20)

    query_vec = model.encode(
        [query], normalize_embeddings=True, convert_to_numpy=True
    ).astype('float32')

    fetch_k = min(top_k * 20, index.ntotal)
    scores, indices = index.search(query_vec, fetch_k)

    candidates = df.iloc[indices[0]].copy()
    candidates['similarity_score'] = scores[0]

    max_reviews = candidates['reviews_count'].max() or 1
    candidates['review_score'] = candidates['reviews_count'] / max_reviews
    candidates['final_score'] = (
        0.7 * candidates['similarity_score'] +
        0.3 * candidates['review_score']
    )

    if max_fee:
        candidates = candidates[candidates['fee'] <= float(max_fee)]
    if city:
        candidates = candidates[
            candidates['address'].str.lower().str.contains(city.lower(), na=False)
        ]
    if specialty:
        candidates = candidates[
            candidates['Speciality'].str.lower().str.contains(specialty.lower(), na=False)
        ]

    top = candidates.sort_values('final_score', ascending=False).head(top_k)

    results = []
    for _, row in top.iterrows():
        fee = row['fee']
        wait = row['waiting_time_min']
        results.append({
            'name':        row['name'],
            'specialty':   row['Speciality'],
            'address':     row['address'],
            'fee':         int(fee)  if pd.notna(fee)  and fee  > 0  else None,
            'wait':        int(wait) if pd.notna(wait) and wait > 0  else None,
            'reviews':     int(row['reviews_count']) if pd.notna(row['reviews_count']) else 0,
            'match':       round(float(row['similarity_score']) * 100, 1),
            'profile_url': row.get('profile_url', '') or '',
        })

    return jsonify({'results': results})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
