def divide_solving(solving):
    divided_solving = solving.replace("\\[", "\\(").replace("\\]", "\\)").split("\\(")
    divided_solving = "\\)".join(divided_solving).split("\\)")

    math_expression = []
    sentence_expression = []

    for index, value in enumerate(divided_solving):
        if index % 2 != 0:
            math_expression.append(value)
        else:
            sentence_expression.append(value)

    return sentence_expression, math_expression
