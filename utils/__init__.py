def divide(List: list, Number: int = 5):
    return [
        List[i * Number:(i + 1) * Number]
        for i in range((len(List) + Number - 1) // Number)
    ]
