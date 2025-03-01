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
    """핵심 문장에서 단어 추출"""
    if not sentence:
        return []
    doc = nlp(sentence)
    keywords = [token.text for token in doc if token.pos_ in ["NOUN", "VERB", "ADJ"] and len(token.text) > 3]
    return keywords[:3]

def generate_expressions():
    """GPT를 사용해 표현(숙어, 관용어) 생성"""
    prompt = "Generate three commonly used English expressions, including idioms or phrasal verbs."
    return request_with_retry(prompt, model="gpt-3.5-turbo").split("\n")

def generate_conversation(phrase):
    """GPT를 활용해 해당 표현을 포함한 짧은 대화 예제 생성"""
    prompt = f"Create a short dialogue using the phrase '{phrase}'."
    return request_with_retry(prompt, model="gpt-3.5-turbo")

def fetch_valid_news_data(max_retries=3):
    """최소한 하나 이상의 유효한 데이터(단어/표현)를 확보할 때까지 뉴스 가져오기"""
    for attempt in range(max_retries):
        news_title, news_content, news_url = get_latest_news()
        if not news_title or not news_content:
            print(f"⚠️ 뉴스 가져오기 실패. {attempt+1}/{max_retries}번째 재시도...")
            continue

        summary_sentence = request_with_retry(f"Summarize this in one sentence:\n{news_content}")
        summary_sentence_ko = translate_text(summary_sentence, target_language="ko")

        important_terms = extract_keywords(summary_sentence)
        expressions = generate_expressions()

        if important_terms and expressions:
            return news_title, news_url, summary_sentence, summary_sentence_ko, important_terms, expressions

        print(f"⚠️ 유효한 단어 또는 표현이 부족함. {attempt+1}/{max_retries}번째 재시도...")

    return "No News Available", None, "No Summary Available", "요약할 뉴스 없음", [], []

# 실행
news_title, news_url, summary_sentence, summary_sentence_ko, important_terms, expressions = fetch_valid_news_data()

if not important_terms or not expressions:
    send_telegram_message("⚠️ 오늘은 적절한 뉴스 기사를 찾지 못했습니다. 내일 다시 확인해 주세요.")
    exit()

selected_morning_word = important_terms[0]
selected_afternoon_expression = expressions[0]

selected_morning_word_ko = translate_text(selected_morning_word)
selected_afternoon_expression_ko = translate_text(selected_afternoon_expression)

morning_conversation = generate_conversation(selected_morning_word)
morning_conversation_ko = translate_text(morning_conversation)

afternoon_conversation = generate_conversation(selected_afternoon_expression)
afternoon_conversation_ko = translate_text(afternoon_conversation)

full_message = (
    "📚 *오늘의 영어 학습*\n\n"
    "📰 *오늘의 뉴스 헤드라인:*\n"
    + news_title + "\n🔗 " + (news_url if news_url else "링크 없음") + "\n📌 " + translate_text(news_title) + "\n\n"
    "💡 *오늘의 핵심 문장:* " + summary_sentence + "\n📌 " + summary_sentence_ko + "\n\n"
    "🔎 *오늘의 단어 및 표현:* \n"
    "- " + selected_morning_word + " (" + selected_morning_word_ko + ")\n"
    "- " + selected_afternoon_expression + " (" + selected_afternoon_expression_ko + ")\n\n"
    "---\n\n"
    "🌅 *아침 학습*\n"
    "💬 *대화 속에서 배우기*\n"
    + morning_conversation + "\n📌 " + morning_conversation_ko + "\n\n"
    "---\n\n"
    "🌇 *오후 학습*\n"
    "💬 *대화 속에서 배우기*\n"
    + afternoon_conversation + "\n📌 " + afternoon_conversation_ko + "\n\n"
    "---\n\n"
    "🌙 *저녁 복습 시간*\n"
    "📖 오늘 배운 내용을 정리해 보세요!\n"
    "✅ 오늘 배운 표현을 활용한 예제 문장\n"
    "- " + selected_morning_word + ": (영어 문장 만들기)\n"
    "- " + selected_afternoon_expression + ": (영어 문장 만들기)\n"
    "✏️ 직접 문장을 만들어 보세요!\n"
    "1. " + selected_morning_word + "을 사용하여 문장을 만들어 보세요.\n"
    "2. " + selected_afternoon_expression + "을 활용하여 새로운 문장을 작성해 보세요.\n"
    "💭 내일 아침에 다시 확인하면서 복습해 보세요!"
)

send_telegram_message(full_message)
