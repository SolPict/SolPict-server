def get_answer_number(problem: str, answer: str | None) -> str:
    problem = problem.replace("\n", " ")
    problem_array = problem.split(" ")

    try:
        answer_index = len(problem_array) - 1 - problem_array[::-1].index(answer)
    except ValueError:
        return None

    if answer_index > 0:
        prev_word = problem_array[answer_index - 1]
        if "(" in prev_word and ")" in prev_word:
            return prev_word.split("(")[1].split(")")[0]

    return None
