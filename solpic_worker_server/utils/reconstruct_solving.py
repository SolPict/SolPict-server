from collections import deque


def reconstruct_solving(sentence_expression, math_expression):
    result = []
    sentences = deque(sentence_expression)
    formulas = deque(math_expression)

    [first_queue, second_queue] = (
        [formulas, sentences] if sentences[0] is None else [sentences, formulas]
    )

    while first_queue or second_queue:
        if first_queue:
            first = first_queue.popleft()

        if second_queue:
            second = second_queue.popleft()

        result.append(second)
        result.append(first)

    return "".join(result[1:])
