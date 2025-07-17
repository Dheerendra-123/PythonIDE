def print_diamond(n):
    if n % 2 == 0:
        print("Please enter an odd number for a symmetric diamond.")
        return

    for i in range(1, n + 1, 2):
        print(' ' * ((n - i) // 2) + '*' * i)

    for i in range(n - 2, 0, -2):
        print(' ' * ((n - i) // 2) + '*' * i)

rows = 7
print(f"Diamond with {rows} rows:")
print_diamond(rows)