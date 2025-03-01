import requests
from bs4 import BeautifulSoup
import openai
import spacy
import time
from telegram_bot import send_telegram_message
from config import OPENAI_API_KEY, NEWS_URL

nlp = spacy.load("en_core_web_sm")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def request_with_retry(prompt, model="gpt-3.5-turbo", retries=5, delay=10):
    """OpenAI API 요청 시 Rate Limit 오류 발생 시 자동 재시도"""
    for i in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except openai.RateLimitError:
            print(f"⚠️ API 요청 제한. {delay}초 후 다시 시도 ({i+1}/{retries})...")
            time.sleep(delay)  
    raise Exception("🚨 API 요청 실패: Rate Limit 초과")

def get_latest_news():
    """최신 뉴스 가져오기"""
    try:
        response = requests.get(NEWS_URL)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"🚨 뉴스 페이지 로딩 실패: {e}")
        return None, None, None

    soup = BeautifulSoup(response.text, "html.parser")
    article = soup.find("a", class_="container__link")
    if not article:
        return None, None, None

    article_url = "https://edition.cnn.com" + article["href"]
    try:
        article_response = requests.get(article_url)
        article_response.raise_for_status()
    except requests.RequestException:
        return None, None, None

    article_soup = BeautifulSoup(article_response.text, "html.parser")
    paragraphs = article_soup.find_all("p")

    title = article_soup.find("h1").text if article_soup.find("h1") else None
    content = " ".join([p.text for p in paragraphs[:5]]) if paragraphs else None
    return title, content, article_url

def translate_text(text, target_language="ko"):
    """GPT를 사용해 텍스트 번역"""
    if not text:
        return "번역할 내용 없음"
    prompt = f"Translate the following text to {target_language}:\n\n{text}"
    return request_with_retry(prompt, model="gpt-3.5-turbo")

def extract_keywords(sentence):
    """핵심 키워드 추출 (최대 5개)"""
    if not sentence:
        return []
    doc = nlp(sentence)
    keywords = [token.text for token in doc if token.pos_ in ["NOUN", "VERB", "ADJ"] and len(token.text) > 3]
    return keywords[:5]  # 최대 5개까지 선택

def generate_conversation(phrase):
    """GPT를 활용해 해당 키워드를 포함한 짧은 대화 예제 생성"""
    prompt = f"Create a short dialogue using the phrase '{phrase}'."
    return request_with_retry(prompt, model="gpt-3.5-turbo")

def fetch_valid_news_data(max_retries=3):
    """최소한 2개의 유효한 키워드를 확보할 때까지 뉴스 가져오기"""
    for attempt in range(max_retries):
        news_title, news_content, news_url = get_latest_news()
        if not news_title or not news_content:
            print(f"⚠️ 뉴스 가져오기 실패. {attempt+1}/{max_retries}번째 재시도...")
            continue

        summary_sentence = request_with_retry(f"Summarize this in one sentence:\n{news_content}")
        summary_sentence_ko = translate_text(summary_sentence, target_language="ko")

        keywords = extract_keywords(summary_sentence)

        if len(keywords) >= 2:
            return news_title, news_url, summary_sentence, summary_sentence_ko, keywords

        print(f"⚠️ 유효한 키워드 부족. {attempt+1}/{max_retries}번째 재시도...")

    return "No News Available", None, "No Summary Available", "요약할 뉴스 없음", []

# 실행
news_title, news_url, summary_sentence, summary_sentence_ko, keywords = fetch_valid_news_data()

if len(keywords) < 2:
    send_telegram_message("⚠️ 오늘은 적절한 뉴스 기사를 찾지 못했습니다. 내일 다시 확인해 주세요.")
    exit()

keyword_text = "\n".join([f"- {kw} ({translate_text(kw)})" for kw in keywords])

conversations = []
for kw in keywords:
    conv_en = generate_conversation(kw)
    conv_ko = translate_text(conv_en)
    conversations.append(f"{conv_en}\n📌 {conv_ko}\n")

full_message = (
    "📚 *오늘의 영어 학습*\n\n"
    "📰 *오늘의 뉴스 헤드라인:*\n"
    + news_title + "\n"
    "📌 " + translate_text(news_title) + "\n"
    "🔗 " + (news_url if news_url else "링크 없음") + "\n\n"
    "💡 *오늘의 핵심 문장:*\n" 
    + summary_sentence + "\n"
    "📌 " + summary_sentence_ko + "\n\n"
    "🔎 *오늘의 키워드*\n"
    + keyword_text + "\n\n"
    "---\n\n"
    "🌅 *오전 학습*\n"
    "오늘은 이 키워드를 중심으로 영어를 연습해볼 거예요! 실생활에서 어떻게 활용되는지 확인해보세요. 😊\n\n"
    "💬 *대화 속에서 배우기*\n"
    + conversations[0] + "\n"
    "---\n\n"
    "🌇 *오후 학습*\n"
    "하루 동안 배운 내용을 다시 한 번 복습해보세요! 다른 맥락에서 같은 표현을 쓰면 기억에 더 잘 남아요. 📚\n\n"
    "💬 *대화 속에서 배우기*\n"
    + conversations[1] + "\n"
    "---\n\n"
    "🌙 *저녁 복습 시간*\n"
    "📖 오늘 배운 내용을 한눈에 정리해보세요!\n\n"
    "📰 *헤드라인:* " + news_title + "\n"
    "📌 " + translate_text(news_title) + "\n\n"
    "💡 *핵심 문장:* " + summary_sentence + "\n"
    "📌 " + summary_sentence_ko + "\n\n"
    "🔎 *오늘의 키워드*\n"
    + keyword_text + "\n\n"
    "💬 *대화 다시 보기*\n"
    + "\n".join(conversations) + "\n\n"
    "✏️ 오늘 배운 키워드를 사용해서 직접 문장을 만들어 보세요!\n"
    "💭 내일 아침에 다시 확인하면서 복습해 보세요!"
)

send_telegram_message(full_message)
