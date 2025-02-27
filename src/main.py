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

def request_with_retry(prompt, model="gpt-3.5-turbo", retries=3, delay=5):
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

def summarize_news(content):
    """뉴스에서 핵심 문장 추출"""
    prompt = f"Summarize the following news article in one key sentence:\n\n{content}"
    return request_with_retry(prompt, model="gpt-3.5-turbo")

def extract_keywords(sentence):
    """핵심 문장에서 중요한 단어 추출"""
    doc = nlp(sentence)
    keywords = [token.text for token in doc if token.pos_ in ["NOUN", "VERB", "ADJ"] and len(token.text) > 3]
    return keywords[:3]

def define_word(word):
    """단어 정의 및 예문 생성"""
    prompt = f"Explain the word '{word}' in simple English and provide an example sentence."
    return request_with_retry(prompt, model="gpt-3.5-turbo")

# 실행
news_title, news_content = get_latest_news()
summary_sentence = summarize_news(news_content)
important_words = extract_keywords(summary_sentence)
word_definitions = {word: define_word(word) for word in important_words}

# 🟢 테스트 모드: 모든 메시지를 한 번에 생성
full_message = f"""
📖 *Today's English Learning*

📰 *Headline:* {news_title}
💬 *Key Sentence:* {summary_sentence}

🔹 *Vocabulary Words:*
{word_definitions}

---

🔹 *Morning Word:* {important_words[0]}
📝 *Definition:* {word_definitions[important_words[0]]}
💡 Try using this word in a sentence today!

---

🔹 *Afternoon Word:* {important_words[1]}
📝 *Definition:* {word_definitions[important_words[1]]}
💡 Challenge: Use this word in a short paragraph!

---

📚 *Evening Review*
📰 *Today's Key Sentence:* {summary_sentence}
🔹 *Words Learned Today:*
- {important_words[0]}
- {important_words[1]}
- {important_words[2]}
✅ Try making your own sentences with these words!
"""

# Telegram 메시지 전송 (한 번에 전체 메시지 발송)
send_telegram_message(full_message)
