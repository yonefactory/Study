import os
import json
import requests
from bs4 import BeautifulSoup
import openai
import spacy
import time
from datetime import datetime
from translation import translate_text

# spaCy 모델 로드
nlp = spacy.load("en_core_web_sm")

# OpenAI API 설정
from config import OPENAI_API_KEY, NEWS_URL
client = openai.OpenAI(api_key=OPENAI_API_KEY)

NEWS_DATA_PATH = "data/news.json"

def save_news_data(news_title, news_url, summary_sentence, summary_sentence_ko, keywords):
    """오늘의 뉴스 데이터를 JSON 파일에 저장"""
    data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "news_title": news_title,
        "news_url": news_url,
        "summary_sentence": summary_sentence,
        "summary_sentence_ko": summary_sentence_ko,
        "keywords": keywords
    }
    with open(NEWS_DATA_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def load_news_data():
    """저장된 뉴스 데이터를 불러옴 (오늘 날짜와 일치하면 사용)"""
    if not os.path.exists(NEWS_DATA_PATH):
        return None

    with open(NEWS_DATA_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("date") == datetime.now().strftime("%Y-%m-%d"):
        return data["news_title"], data["news_url"], data["summary_sentence"], data["summary_sentence_ko"], data["keywords"]
    return None

def fetch_valid_news_data():
    """오늘의 뉴스 데이터 가져오기 (처음 실행 시 저장, 이후 실행 시 로드)"""
    saved_data = load_news_data()
    if saved_data:
        return saved_data  # 기존 데이터 사용

    news_title, news_content, news_url = get_latest_news()
    if not news_title or not news_content:
        return "No News Available", None, "No Summary Available", "요약할 뉴스 없음", []

    summary_sentence = request_with_retry(f"Summarize this in one sentence:\n{news_content}")
    summary_sentence_ko = translate_text(summary_sentence, target_language="ko")
    keywords = extract_keywords(summary_sentence)

    if len(keywords) < 2:
        return "No News Available", None, "No Summary Available", "요약할 뉴스 없음", []

    save_news_data(news_title, news_url, summary_sentence, summary_sentence_ko, keywords)
    return news_title, news_url, summary_sentence, summary_sentence_ko, keywords
