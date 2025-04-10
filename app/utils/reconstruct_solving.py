def reconstruct_solving(sentence_expression, math_expression):
    result = []
    sentence_first = sentence_expression[0] is None

    sentences = sentence_expression[1:]
    maths = math_expression[1:]

    max_len = max(len(sentences), len(maths))

    for i in range(max_len):
        if sentence_first:
            if i < len(sentences):
                result.append(sentences[i] or "")
            if i < len(maths):
                result.append(maths[i] or "")
        else:
            if i < len(maths):
                result.append(maths[i] or "")
            if i < len(sentences):
                result.append(sentences[i] or "")

    return "".join(result)
