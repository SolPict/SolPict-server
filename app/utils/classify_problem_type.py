import random


def classify_problem_type() -> str:
    # 추후에 또 다른 AI모델 사용해서 분류 기능 확장
    return random.choice(["Algebra", "Number & Operation", "Geometry"])
