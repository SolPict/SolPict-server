def analyze_ocr_text(ocr_text: str) -> str:
    is_latex = False
    have_question_mark = False
    count_num = 0
    count_kor = 0
    count_eng = 0
    count_latex = 0

    for char in ocr_text:
        if char == "$":
            count_latex += 1
            is_latex = not is_latex
            continue

        if is_latex:
            continue

        if "가" <= char <= "힣":
            count_kor += 1
        elif ("a" <= char <= "z") or ("A" <= char <= "Z"):
            count_eng += 1
        elif char.isdigit():
            count_num += 1
        elif char == "?":
            have_question_mark = True

    if not (count_latex and count_num and have_question_mark):
        raise ValueError("수학 문제가 아닌 OCR입니다.")

    if is_latex:
        raise ValueError("LaTeX 구문이 열리고 닫히지 않았습니다.")

    return "Kor" if count_kor > count_eng else "Eng"
