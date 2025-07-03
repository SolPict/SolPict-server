def get_answer(explanation):
    try:
        return str(explanation.split("oxed{")[1].split("}")[0])
    except Exception as error:
        print(error)
        return -1
