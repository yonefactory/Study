import openai
from config import OPENAI_API_KEY

# OpenAI 클라이언트 생성
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def generate_conversation(phrase):
    """GPT를 활용해 해당 키워드를 포함한 짧은 대화 예제 생성"""
    prompt = f"Create a short and natural dialogue using the phrase '{phrase}'. Keep it simple and relevant to everyday conversation."

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"🚨 대화 생성 실패: {e}")
        return "대화 생성 오류 발생"
