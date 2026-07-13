# -*- coding: utf-8 -*-
"""
train.py -- ML Training Pipeline for SupportAI Chatbot
Trains TF-IDF + SVM and Naive Bayes classifiers, evaluates both,
saves the best model + label encoder + metrics to chatbot/model/
Run: python train.py
"""

import json
import os
import re
import numpy as np
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import LabelEncoder

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'chatbot', 'model')
os.makedirs(MODEL_DIR, exist_ok=True)


def preprocess(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    return text


def load_data():
    with open(os.path.join(BASE_DIR, 'chatbot', 'intents.json'), encoding='utf-8') as f:
        intents = json.load(f)['intents']
    X, y = [], []
    for intent in intents:
        if intent['tag'] == 'fallback':
            continue
        for pattern in intent['patterns']:
            X.append(preprocess(pattern))
            y.append(intent['tag'])
    return X, y


def train():
    print("=" * 55)
    print("   SupportAI -- ML Training Pipeline")
    print("=" * 55)

    X, y = load_data()
    print(f"\n[DATA] {len(X)} samples | {len(set(y))} intent classes")
    print(f"       Classes: {sorted(set(y))}\n")

    le    = LabelEncoder()
    y_enc = le.fit_transform(y)

    svm_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), stop_words='english', sublinear_tf=True)),
        ('clf',   LinearSVC(C=1.0, max_iter=2000))
    ])

    nb_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), stop_words='english')),
        ('clf',   MultinomialNB(alpha=0.1))
    ])

    print("[CV] 5-Fold Cross-Validation:")
    svm_cv = cross_val_score(svm_pipeline, X, y_enc, cv=5, scoring='accuracy')
    nb_cv  = cross_val_score(nb_pipeline,  X, y_enc, cv=5, scoring='accuracy')
    print(f"   SVM  mean={svm_cv.mean():.4f}  std={svm_cv.std():.4f}  folds={np.round(svm_cv, 4)}")
    print(f"   NB   mean={nb_cv.mean():.4f}  std={nb_cv.std():.4f}  folds={np.round(nb_cv, 4)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )

    svm_pipeline.fit(X_train, y_train)
    nb_pipeline.fit(X_train, y_train)

    svm_preds = svm_pipeline.predict(X_test)
    nb_preds  = nb_pipeline.predict(X_test)
    svm_acc   = accuracy_score(y_test, svm_preds)
    nb_acc    = accuracy_score(y_test, nb_preds)

    print(f"\n[EVAL] Test Accuracy:  SVM={svm_acc*100:.2f}%  NB={nb_acc*100:.2f}%")

    best_pipeline = svm_pipeline if svm_acc >= nb_acc else nb_pipeline
    best_name     = "SVM"         if svm_acc >= nb_acc else "Naive Bayes"
    best_preds    = svm_preds     if svm_acc >= nb_acc else nb_preds
    best_acc      = max(svm_acc, nb_acc)
    best_cv       = svm_cv        if svm_acc >= nb_acc else nb_cv

    print(f"[BEST] Winner: {best_name} ({best_acc*100:.2f}%)\n")

    print("[REPORT] Classification Report:")
    print(classification_report(
        y_test, best_preds,
        target_names=le.inverse_transform(sorted(set(y_enc)))
    ))

    cm     = confusion_matrix(y_test, best_preds)
    labels = le.inverse_transform(sorted(set(y_enc)))
    print("[MATRIX] Confusion Matrix:")
    print(f"{'':>18}" + "".join(f"{l[:6]:>8}" for l in labels))
    for i, row in enumerate(cm):
        print(f"{labels[i]:>18}" + "".join(f"{v:>8}" for v in row))

    # Retrain on full dataset before saving
    best_pipeline.fit(X, y_enc)

    model_path   = os.path.join(MODEL_DIR, 'intent_model.pkl')
    encoder_path = os.path.join(MODEL_DIR, 'label_encoder.pkl')
    metrics_path = os.path.join(MODEL_DIR, 'metrics.json')

    joblib.dump(best_pipeline, model_path)
    joblib.dump(le, encoder_path)

    metrics = {
        'model':        best_name,
        'accuracy':     round(best_acc * 100, 2),
        'cv_mean':      round(float(best_cv.mean()) * 100, 2),
        'cv_std':       round(float(best_cv.std())  * 100, 2),
        'num_samples':  len(X),
        'num_classes':  len(set(y)),
        'classes':      sorted(set(y)),
        'svm_accuracy': round(svm_acc * 100, 2),
        'nb_accuracy':  round(nb_acc  * 100, 2),
    }
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

    print(f"\n[SAVED] {model_path}")
    print(f"[SAVED] {encoder_path}")
    print(f"[SAVED] {metrics_path}")
    print("\n[DONE] Run `python app.py` to start the chatbot.\n")

    return metrics


if __name__ == '__main__':
    train()
