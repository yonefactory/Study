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
            print(f"⚠️ API Rate Limit Error. {delay}초 후 재시도 ({i+1}/{retries})...")
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
    sentences = content.split(". ")  # 문장을 분리
    if len(sentences) > 4:
        return ". ".join(sentences[:3] + [sentences[-1]])  # 앞 3문장 + 마지막 문장만 선택
    return content  # 문장이 4개 이하라면 원문 유지

def summarize_news(content):
    """뉴스 핵심 문장만 GPT에 전달하여 요약 (토큰 절약)"""
    compressed_content = extract_core_sentences(content)  # 텍스트 압축
    prompt = f"Summarize the following key sentences in one concise sentence:\n\n{compressed_content}"
    return request_with_retry(prompt, model="gpt-3.5-turbo")

def translate_text(text, target_language="ko"):
    """GPT를 사용해 텍스트 번역"""
    prompt = f"Translate the following text to {target_language}:\n\n{text}"
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
    prompt = f"Explain the following words or expressions in English and translate their meaning into Korean:\n\n"
    for term in terms:
        prompt += f"- {term}\n"
    return request_with_retry(prompt, model="gpt-3.5-turbo")

# 실행
news_title, news_content = get_latest_news()
summary_sentence = summarize_news(news_content)
summary_sentence_ko = translate_text(summary_sentence, target_language="ko")
important_terms = extract_keywords(summary_sentence)  # 단어 + 표현 포함
expressions = generate_expressions().split("\n")  # 새로운 표현 추가
all_terms = important_terms + expressions  # 전체 학습 대상

# 한국어 번역 포함한 정의 생성
term_definitions = define_terms(all_terms)

# 🟢 메시지 생성 (헤드라인: 영어 & 한국어 포함)
full_message = f"""
📖 *Today's English Learning*

📰 *Headline:*  
{news_title}  
📌 {translate_text(news_title, target_language="ko")}

💬 *Key Sentence:*  
{summary_sentence}  
📌 {summary_sentence_ko}

🔹 *Vocabulary & Expressions:*
{term_definitions}

---

🔹 *Morning Phrase:* {all_terms[0]}
📝 *Definition:* {term_definitions.split('\n')[0]}
💡 Try using this phrase in a sentence today!

---

🔹 *Afternoon Phrase:* {all_terms[1]}
📝 *Definition:* {term_definitions.split('\n')[1]}
💡 Challenge: Use this phrase in a short paragraph!

---

📚 *Evening Review*
📰 *Today's Key Sentence:* {summary_sentence}
🔹 *Expressions & Words Learned Today:*
- {all_terms[0]}
- {all_terms[1]}
- {all_terms[2]}
✅ Try making your own sentences with these!
"""

# Telegram 메시지 전송 (한 번에 전체 메시지 발송)
send_telegram_message(full_message)
