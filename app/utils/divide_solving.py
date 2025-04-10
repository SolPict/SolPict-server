def divide_solving(solving):
    start = 0

    math_expression = []
    sentence_expression = []

    if solving[0:2] == "\\[" or solving[0:2] == "\\(":
        sentence_expression.append(None)
    else:
        math_expression.append(None)

    for index in range(len(solving) - 2):
        token = solving[index : index + 2]
        if token == "\\[" or token == "\\(":
            sentence_expression.append(solving[start:index])
            start = index
        elif token == "\\]" or token == "\\)":
            math_expression.append(solving[start : index + 3])
            start = index + 3

    if start < len(solving):
        sentence_expression.append(solving[start:])

    return sentence_expression, math_expression
