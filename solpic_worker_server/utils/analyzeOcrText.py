def analyze_ocr_text(ocr_text: str) -> str:
    is_latex = False
    have_question_mark = False
    count_kor = 0
    count_eng = 0
    count_latex = 0

    for index in range(len(ocr_text)):
        char = ocr_text[index]
        chars = ocr_text[index : index + 2]

        if char == "$" or chars == "\\[" or chars == "\\]":
            count_latex += 1
            is_latex = not is_latex
            continue

        if char == "?":
            have_question_mark = True

        if is_latex:
            continue

        if "가" <= char <= "힣":
            count_kor += 1
        elif ("a" <= char <= "z") or ("A" <= char <= "Z"):
            count_eng += 1

    if not (count_latex and have_question_mark):
        raise ValueError("수학 문제가 아닌 OCR입니다.")

    if is_latex:
        raise ValueError("LaTeX 구문이 열리고 닫히지 않았습니다.")

    return "Kor" if count_kor > count_eng else "Eng"
