# 실행
news_title, news_content = get_latest_news()
summary_sentence = summarize_news(news_content)
summary_sentence_ko = translate_text(summary_sentence, target_language="ko")
important_terms = extract_keywords(summary_sentence)
expressions = generate_expressions().split("\n")
all_terms = important_terms + expressions

# GPT가 선택한 중요 표현 리스트 가져오기
selected_terms = select_important_terms(all_terms)

# 예외 처리: selected_terms가 2개 미만이면 all_terms에서 보충
if len(selected_terms) < 2:
    print("⚠️ 선택된 표현이 부족합니다. 대체 표현을 추가합니다.")
    missing_count = 2 - len(selected_terms)
    selected_terms += all_terms[:missing_count]  # 부족한 개수만큼 all_terms에서 채우기

# 예외 처리: 그래도 부족할 경우 기본값 설정
if len(selected_terms) < 2:
    print("🚨 모든 리스트가 비어 있습니다. 기본 표현을 사용합니다.")
    selected_terms = ["keep up the good work", "break the ice"]  # 기본값

# 최종 선택된 표현
selected_morning_phrase = selected_terms[0].strip()
selected_afternoon_phrase = selected_terms[1].strip()

# 예문 및 대화 생성
term_definitions = define_terms(all_terms)
morning_example_sentence = generate_example_sentence(selected_morning_phrase)
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
    "💡 *예문:* " + morning_example_sentence + "\n"
    "✏️ **이 문장을 해석해보세요!**\n\n"
    "---\n\n"
    "🌇 *오후 학습 표현:* " + selected_afternoon_phrase + "\n"
    "💬 *대화 속에서 배우기:*\n" + afternoon_conversation + "\n\n"
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
