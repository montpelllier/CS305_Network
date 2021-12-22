def find_narcissistic_number(start: int, end: int) -> list:
    narcissistic_number = []
    for i in range(start, end):
        s = str(i)
        sum = 0
        for j in range(len(s)):
            sum = sum + int(s[j])**len(s)
        if i == sum:
            narcissistic_number.append(i)

    return narcissistic_number

print(find_narcissistic_number(1,1000))