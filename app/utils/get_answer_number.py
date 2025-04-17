import random


def get_answer_number(problem: str, answer: str | None) -> str:
    problem = problem.replace("\n", " ")
    problem_array = problem.split(" ")

    try:
        answer_index = len(problem_array) - 1 - problem_array[::-1].index(answer)
    except ValueError:
        # AI 모델이 반환한 값에 의존하다 보니 정확한 정답이 나오지 않는 경우 랜덤으로 처리해주고 있습니다.
        return random.randint(1, 5)

    if answer_index > 0:
        prev_word = problem_array[answer_index - 1]
        if "(" in prev_word and ")" in prev_word:
            return prev_word.split("(")[1].split(")")[0]

    return random.randint(1, 5)
