import sys
from news_processor import fetch_valid_news_data
from telegram_bot import send_telegram_message
from translation import translate_text
from conversation import generate_conversation

def send_morning_learning():
    """7AM - 오늘의 영어 학습"""
    news_title, news_url, summary_sentence, summary_sentence_ko, keywords = fetch_valid_news_data()

    keyword_text = "\n".join([f"{i+1}. {kw} ({translate_text(kw)})" for i, kw in enumerate(keywords)])

    message = (
        "📚 오늘의 영어 학습\n\n"
        "📰 오늘의 뉴스 헤드라인:\n\n"
        + news_title + "\n📌 " + translate_text(news_title) +
        "\n🔗 " + (news_url if news_url else "링크 없음") + "\n\n"
        "💡 오늘의 핵심 문장:\n\n"
        + summary_sentence + "\n"
        "📌 " + summary_sentence_ko + "\n\n"
        "🔎 오늘의 키워드\n\n"
        + keyword_text
    )

    send_telegram_message(message)

def send_morning_study():
    """11AM - 오전 학습"""
    news_title, _, _, _, keywords = fetch_valid_news_data()

    keyword_message = "🔹 오늘의 학습 키워드: " + keywords[0] + " (" + translate_text(keywords[0]) + ")\n\n"
    conversation = generate_conversation(keywords[0]) + "\n📌 " + translate_text(generate_conversation(keywords[0]))

    message = (
        "🌅 오전 학습\n"
        "오늘은 이 키워드를 중심으로 영어를 연습해볼 거예요! 실생활에서 어떻게 활용되는지 확인해보세요. 😊\n\n"
        + keyword_message
        + "💬 대화 속에서 배우기\n"
        + conversation
    )

    send_telegram_message(message)

def send_afternoon_study():
    """4PM - 오후 학습"""
    news_title, _, _, _, keywords = fetch_valid_news_data()

    keyword_message = "🔹 오늘의 학습 키워드: " + keywords[1] + " (" + translate_text(keywords[1]) + ")\n\n"
    conversation = generate_conversation(keywords[1]) + "\n📌 " + translate_text(generate_conversation(keywords[1]))

    message = (
        "🌇 오후 학습\n"
        "하루 동안 배운 내용을 다시 한 번 복습해보세요! 다른 맥락에서 같은 표현을 쓰면 기억에 더 잘 남아요. 📚\n\n"
        + keyword_message
        + "💬 대화 속에서 배우기\n"
        + conversation
    )

    send_telegram_message(message)

def send_evening_review():
    """7PM - 저녁 복습"""
    news_title, news_url, summary_sentence, summary_sentence_ko, keywords = fetch_valid_news_data()

    keyword_text = "\n".join([f"{i+1}. {kw} ({translate_text(kw)})" for i, kw in enumerate(keywords)])
    conversations = [generate_conversation(kw) + "\n📌 " + translate_text(generate_conversation(kw)) for kw in keywords]

    message = (
        "🌙 저녁 복습 시간\n"
        "📖 오늘 배운 내용을 한눈에 정리해보세요!\n\n"
        "📰 헤드라인: \n" + news_title + "\n📌 " + translate_text(news_title) + "\n\n"
        "💡 핵심 문장:\n\n" + summary_sentence + "\n"
        "📌 " + summary_sentence_ko + "\n\n"
        "🔎 오늘의 키워드\n\n"
        + keyword_text + "\n\n"
        "💬 대화 다시 보기\n"
        + "\n".join(conversations) + "\n\n"
        "✏️ 오늘 배운 키워드를 사용해서 직접 문장을 만들어 보세요!\n"
        "💭 내일 아침에 다시 확인하면서 복습해 보세요!"
    )

    send_telegram_message(message)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python3 daily_study.py <옵션>")
        sys.exit(1)

    option = sys.argv[1]

    if option == "morning_learning":
        send_morning_learning()
    elif option == "morning_study":
        send_morning_study()
    elif option == "afternoon_study":
        send_afternoon_study()
    elif option == "evening_review":
        send_evening_review()
    else:
        print("잘못된 옵션입니다.")
        sys.exit(1)
