import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F

class NeuroFilter:
    def __init__(self):
        print("Загружаю модель...")
        self.tokenizer = AutoTokenizer.from_pretrained("cointegrated/rubert-tiny-toxicity")
        self.model = AutoModelForSequenceClassification.from_pretrained("cointegrated/rubert-tiny-toxicity")
        self.model.eval()

    def get_score(self, text):
        with torch.no_grad():
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True)
            outputs = self.model(**inputs)
            scores = F.softmax(outputs.logits, dim=1).squeeze()
            return float(scores[1])

if __name__ == "__main__":
    nf = NeuroFilter()
    while True:
        msg = input("Введите текст для оценки: ")
        score = nf.get_score(msg)
        print(f"Тревожность: {score:.2f}")
