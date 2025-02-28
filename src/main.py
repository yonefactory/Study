import requests
from bs4 import BeautifulSoup
import openai
import spacy
import time
from telegram_bot import send_telegram_message
from config import OPENAI_API_KEY, NEWS_URL

nlp = spacy.load("en_core_web_sm")

# OpenAI 최신 API 사용을 위해 client 생성
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
            time.sleep(delay)  # 재시도 전 대기
    raise Exception("🚨 API 요청 실패: Rate Limit 초과")

def get_latest_news():
    """미국 뉴스 사이트에서 최신 기사 가져오기"""
    response = requests.get(NEWS_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    # 뉴스 기사 링크 추출
    article = soup.find("a", class_="container__link")
    article_url = "https://edition.cnn.com" + article["href"]

    # 기사 본문 가져오기
    article_response = requests.get(article_url)
    article_soup = BeautifulSoup(article_response.text, "html.parser")
    paragraphs = article_soup.find_all("p")

    # 상위 5문장만 가져오기
    title = article_soup.find("h1").text
    content = " ".join([p.text for p in paragraphs[:5]])
    return title, content

def extract_core_sentences(content):
    """뉴스에서 중요한 첫 3문장 + 마지막 1문장만 선택하여 압축"""
    sentences = content.split(". ")  
    if len(sentences) > 4:
        return ". ".join(sentences[:3] + [sentences[-1]])  
    return content  

def summarize_news(content):
    """뉴스 핵심 문장만 GPT에 전달하여 요약 (토큰 절약)"""
    compressed_content = extract_core_sentences(content)  
    prompt = "Summarize the following key sentences in one concise sentence:\n\n" + compressed_content
    return request_with_retry(prompt, model="gpt-3.5-turbo")

def translate_text(text, target_language="ko"):
    """GPT를 사용해 텍스트 번역"""
    prompt = "Translate the following text to " + target_language + ":\n\n" + text
    return request_with_retry(prompt, model="gpt-3.5-turbo")

def extract_keywords(sentence):
    """핵심 문장에서 중요한 단어 및 표현 추출"""
    doc = nlp(sentence)
    keywords = [token.text for token in doc if token.pos_ in ["NOUN", "VERB", "ADJ"] and len(token.text) > 3]
    return keywords[:3]

def generate_expressions():
    """자주 쓰이는 영어 표현(구, 관용어) 생성"""
    prompt = "Generate three commonly used English expressions, including idioms or phrasal verbs."
    return request_with_retry(prompt, model="gpt-3.5-turbo")

def define_terms(terms):
    """3개의 단어 또는 표현을 한 번의 요청으로 정의 (영어 설명 + 한국어 번역)"""
    prompt = "Explain the following words or expressions in English and translate their meaning into Korean:\n\n"
    for term in terms:
        prompt += "- " + term + "\n"
    return request_with_retry(prompt, model="gpt-3.5-turbo")

def select_important_terms(terms):
    """GPT를 활용하여 가장 중요한 단어/표현 2개를 선택"""
    prompt = "From the following words and expressions, select the two most essential and frequently used ones:\n\n"
    prompt += "\n".join(terms)
    prompt += "\n\nReturn only the two selected expressions in a comma-separated format."

    selected_terms = request_with_retry(prompt, model="gpt-3.5-turbo")
    return selected_terms.split(", ")

def generate_quiz(phrase):
    """GPT를 활용해 빈칸 채우기 퀴즈 생성"""
    prompt = f"Create a fill-in-the-blank quiz using the phrase '{phrase}'."
    return request_with_retry(prompt, model="gpt-3.5-turbo")

def generate_conversation(phrase):
    """GPT를 활용해 해당 표현을 포함한 짧은 대화 예제 생성"""
    prompt = f"Create a short dialogue using the phrase '{phrase}'."
    return request_with_retry(prompt, model="gpt-3.5-turbo")

# 실행
news_title, news_content = get_latest_news()
summary_sentence = summarize_news(news_content)
summary_sentence_ko = translate_text(summary_sentence, target_language="ko")
important_terms = extract_keywords(summary_sentence)
expressions = generate_expressions().split("\n")
all_terms = important_terms + expressions

selected_terms = select_important_terms(all_terms)
selected_morning_phrase = selected_terms[0].strip()
selected_afternoon_phrase = selected_terms[1].strip()

if selected_morning_phrase not in all_terms:
    selected_morning_phrase = all_terms[0]
if selected_afternoon_phrase not in all_terms:
    selected_afternoon_phrase = all_terms[1]

term_definitions = define_terms(all_terms)
morning_quiz = generate_quiz(selected_morning_phrase)
afternoon_conversation = generate_conversation(selected_afternoon_phrase)

# Telegram 메시지 전송
full_message = (
    "📚 *오늘의 영어 학습*\n\n"
    "📰 *오늘의 뉴스 헤드라인:*\n"
    + news_title + "\n📌 " + translate_text(news_title, target_language="ko") + "\n\n"
    "💡 *오늘의 핵심 문장:*\n"
    + summary_sentence + "\n📌 " + summary_sentence_ko + "\n\n"
    "🔎 *오늘의 단어 및 표현:*\n" + term_definitions + "\n\n"
    "---\n\n"
    "🌅 *아침 학습 표현:* " + selected_morning_phrase + "\n"
    "📝 *설명:* " + term_definitions.split("\n")[all_terms.index(selected_morning_phrase)] + "\n"
    "❓ *빈칸 채우기 퀴즈:*\n" + morning_quiz + "\n"
    "✏️ *빈칸에 알맞은 단어를 채워보세요!*\n\n"
    "---\n\n"
    "🌇 *오후 학습 표현:* " + selected_afternoon_phrase + "\n"
    "💬 *대화 속에서 배우기:*\n" + afternoon_conversation + "\n"
    "📝 *이 표현을 포함한 자신만의 대화를 만들어보세요!*\n\n"
    "---\n\n"
    "🌙 *저녁 복습 시간*\n"
    "💬 *오늘 배운 핵심 문장:* " + summary_sentence + "\n"
    "📌 " + summary_sentence_ko + "\n"
    "📖 *오늘 배운 표현:*\n"
    "- " + selected_morning_phrase + "\n"
    "- " + selected_afternoon_phrase + "\n"
    "✅ *오늘 배운 표현을 활용하여 문장을 만들어 보세요!*"
)

send_telegram_message(full_message)
