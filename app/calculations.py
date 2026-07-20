def count_digits(content: str) -> dict:
    '''Возвращает {'0': N, '1': N, ..., '9': N} для одной строки содержимого.'''
    counts = {str(d): 0 for d in range(10)}
    for ch in content:
        if ch.isdigit():
            counts[ch] += 1
    return counts


def aggregate_digit_counts(per_file_counts: dict) -> dict:
    '''Суммирует статистику по нескольким файлам в одну общую.'''
    total = {str(d): 0 for d in range(10)}
    for counts in per_file_counts.values():
        for digit, value in counts.items():
            total[digit] += value
    return total
