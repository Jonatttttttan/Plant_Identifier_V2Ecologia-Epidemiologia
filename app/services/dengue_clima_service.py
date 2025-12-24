from __future__ import annotations
import pandas as pd


from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@dataclass
class RAGIndex:
    vectorizer: TfidfVectorizer
    matrix: Any # sparse matrix
    docs: List[str]
    meta: List[Dict[str, Any]]

def dengue_df_to_weekly(df_dengue: pd.DataFrame) -> pd.DataFrame:
    """
    Entrada: df com colunas ["data_iniSE", "casos]
    Saída: df com colunas ["ano", "semana", "casos"]

    """
    df = df_dengue.copy()
    df["data_iniSE"] = pd.to_datetime(df["data_iniSE"], errors="coerce")
    df = df.dropna(subset=["data_iniSE"])

    # Semana ISO (aproximação prática; se você tiver semana epidemiológica pronta, melhor ainda)
    iso = df["data_iniSE"].dt.isocalendar()
    df["ano"] = iso["year"].astype(int)
    df["semana"] = iso["week"].astype(int)

    # garante numérico
    df["casos"] = pd.to_numeric(df["casos"], errors="coerce")

    # agrega caso exista mais de 1 registro por semana
    df = df.groupby(["ano", "semana"], as_index=False)["casos"].sum()
    return df


def lista_clima_to_df(
        chuva_semanal: List[Dict[str, Any]],
        temp_semanal: List[Dict[str, Any]],
) -> pd.DataFrame:
    """
    Entrada:
      chuva: [{'ano': 1999, 'indice': 52, 'chuva_mm': 83.6},...]
      temp: [{'ano':1999, 'indice': 52, 'temperatura_media': 21.1},...]
    Saída:
      df: colunas [ "ano", "semana", "chuva_mm", "temperatura_media"]

    """
    df_chuva = pd.DataFrame(chuva_semanal).copy()
    df_temp = pd.DataFrame(temp_semanal).copy()

    # n ormaliza nomes
    if "indice" in df_chuva.columns:
        df_chuva = df_chuva.rename(columns={"indice": "semana"})
    if "indice" in df_temp.columns:
        df_temp = df_temp.rename(columns={"indice": "semana"})

    # tipos
    for c in ["ano", "semana"]:
        if c in df_chuva.columns:
            df_chuva[c] = pd.to_numeric(df_chuva[c], errors="coerce").astype("Int64")
        if c in df_temp.columns:
            df_temp[c] = pd.to_numeric(df_temp[c], errors="coerce").astype("Int64")

    if "chuva_mm" in df_chuva.columns:
        df_chuva["chuva_mm"] = pd.to_numeric(df_chuva["chuva_mm"], errors="coerce")
    if "temperatura_media" in df_temp.columns:
        df_temp["temperatura_media"] = pd.to_numeric(df_temp["temperatura_media"], errors="coerce")

    # merge por ano+semana
    df = pd.merge(df_chuva, df_temp, on=["ano", "semana"], how="outer")

    # limpa
    df = df.dropna(subset=["ano", "semana"]).copy()
    df["ano"] = df["ano"].astype(int)
    df["semana"] = df["semana"].astype(int)

    return df[["ano", "semana", "chuva_mm", "temperatura_media"]].sort_values(by=["ano", "semana"])

def merge_dengue_clima(df_dengue_weekly: pd.DataFrame, df_clima_weekly: pd.Dataframe) -> pd.DataFrame:
    """
    Saída final por semana:
      ["ano", "semana", "casos", "chuva_mm", "temperatura_media"]

    """
    df = pd.merge(df_dengue_weekly, df_clima_weekly, on=["ano", "semana"], how="left")
    return df.sort_values(["ano", "semana"]).reset_index(drop=True)

def build_week_documents(df:pd.DataFrame) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Constrói 1 documento por semana (linha).
    """
    docs = []
    meta = []

    for _, row in df.iterrows():
        ano = int(row["ano"])
        semana = int(row["semana"])
        casos = int(row["casos"]) if pd.notna(row["casos"]) else 0
        chuva = row["chuva_mm"]
        temp = row["temperatura_media"]

        chuva_txt = "sem dado" if pd.isna(chuva) else f"{float(chuva):.2f} mm"
        temp_txt = "sem dado" if pd.isna(temp) else f"{float(temp):.2f} °C"

        text = (
            f"Ano {ano}, semana {semana}."
            f"Casos de dengue: {casos}. "
            f"Chuva semanal: {chuva_txt}."
            f"Temperatura média semanaç:{temp_txt}."
        )

        docs.append(text)
        meta.append({"ano": ano, "semana": semana})
    return docs, meta

def build_rag_index(docs: List[str], meta: List[Dict[str, Any]]) -> RAGIndex:
     vectorizer = TfidfVectorizer(
         lowercase=True,
         stop_words=None, # português misto; deixo None para não remover palavras úteis
         ngram_range = (1, 2)
     )
     matrix = vectorizer.fit_transform(docs)
     return RAGIndex(vectorizer=vectorizer, matrix=matrix, docs=docs, meta=meta)

def retrieve(index: RAGIndex, query: str, top_k: int = 8) -> List[Dict[str, Any]]:
    q_vec = index.vectorizer.transform([query])
    sims = cosine_similarity(q_vec, index.matrix).flatten()
    top_idx = sims.argsort()[::-1][:top_k]

    results = []
    for i in top_idx:
        results.append({
            "score": float(sims[i]),
            "text": index.docs[i],
            "meta": index.meta[i],
        })
    return results

def answer_with_openai(question: str, retrieved: List[Dict[str, Any]]) -> str:
    context = "\n".join([f"- {r["text"]}" for r in retrieved])

    prompt = (
        "Você é um assistente de análise de dados epidemiológicos e climáticos.\n"
        "Responda APENAS com base no contexto fornecido.\n"
        "Se não houver contexto suficiente, diga claramente que não dá para concluir.\n\n"
        f"CONTEXTO (semanas recuperadas):\n{context}\n\n"
        f"PERGUNTA:\n{question}\n\n"
        "FORMATO:\n"
        "- Responda em português.\n"
        "- Use 4 a 8 bullets.\n"
        "- Se citar semanas/anos, cite explicitamente.\n"
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você é um assistente especializado em análise de séries temporais de dengue e clima."},
            {"role": "user",  "content": prompt}
        ],
        max_tokens=450,
        temperature=0.3,
    )
    return resp.choices[0].message.content

def rag_pipeline(
        df_dengue: pd.DataFrame,
        chuva_semanal: List[Dict[str, Any]],
        temp_semanal: List[Dict[str, Any]],
        question: str,
        top_k: int = 8,
) -> Dict[str, Any]:
    df_dengue_week = dengue_df_to_weekly(df_dengue)
    df_clima_week = lista_clima_to_df(chuva_semanal, temp_semanal)
    df_merged = merge_dengue_clima(df_dengue_week, df_clima_week)

    docs, meta = build_week_documents(df_merged)
    index = build_rag_index(docs, meta)

    retrieved = retrieve(index, question, top_k=top_k)
    answer = answer_with_openai(question, retrieved)

    return {
        "answer" : answer,
        "retrieved": retrieved,
        "rows" : len(df_merged)
    }


