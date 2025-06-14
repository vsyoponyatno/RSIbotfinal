import yaml
import datetime

with open("keywords.yaml", "r", encoding="utf-8") as f:
    KEYWORDS = yaml.safe_load(f)

def check_risk(text, source="@unknown"):
    categories = []
    lowered = text.lower()

    for cat, words in KEYWORDS.items():
        if any(word.lower() in lowered for word in words):
            categories.append(cat)

    level = None
    if len(categories) >= 3:
        level = "🔴 ВЫСОКИЙ"
    elif len(categories) == 2:
        level = "🟠 СРЕДНИЙ"
    elif len(categories) == 1:
        level = "🟢 НИЗКИЙ"

    if not level:
        return None

    trimmed = text[:1000]
    now = datetime.datetime.now().strftime("%H:%M")

    result = f"""{level} тревожность
Категории: {', '.join(categories)}

{trimmed}
Источник: {source}
Время: {now}"""
    return result

if __name__ == "__main__":
    while True:
        msg = input("Введите пост: ")
        risk = check_risk(msg, "@testchannel")
        if risk:
            print("\n" + risk + "\n")
        else:
            print("🚫 Нет тревожности\n")
