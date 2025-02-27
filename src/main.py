import requests
from bs4 import BeautifulSoup
import openai
import spacy
from telegram_bot import send_telegram_message
from config import OPENAI_API_KEY, NEWS_URL

nlp = spacy.load("en_core_web_sm")

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
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

def extract_keywords(sentence):
    """핵심 문장에서 중요한 단어 추출"""
    doc = nlp(sentence)
    keywords = [token.text for token in doc if token.pos_ in ["NOUN", "VERB", "ADJ"] and len(token.text) > 3]
    return keywords[:3]

def define_word(word):
    """단어 정의 및 예문 생성"""
    prompt = f"Explain the word '{word}' in simple English and provide an example sentence."
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

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
