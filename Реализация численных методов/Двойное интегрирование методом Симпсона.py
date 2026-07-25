import prettytable


def function(x, y):
    return x + 6 * y


def F_1(x):
    return 2 / 5 * x ** (5/2) + 3 / 2 * x ** 2


def F_2(x):
    return x - 3 / x


def quad_simpson(n, m, a, A, b, B):
    lambda_array = [[0 for _ in range(2*n+1)] for _ in range(2*m+1)]
    table = prettytable.PrettyTable()
    for j in range(0, 2*m-1, 2):
        for i in range(0, 2*n-1, 2):
            lambda_array[j][i] += 1
            lambda_array[j][i+1] += 4
            lambda_array[j][i+2] += 1
            lambda_array[j+1][i] += 4
            lambda_array[j+1][i+1] += 16
            lambda_array[j+1][i+2] += 4
            lambda_array[j+2][i] += 1
            lambda_array[j+2][i+1] += 4
            lambda_array[j+2][i+2] += 1

    for j in range(0, 2*m+1):
        table.add_row([w for w in lambda_array[j]])

    h = (A - a) / (2 * n)
    k = (B - b) / (2 * m)

    x0 = a
    y0 = b

    sums = 0

    for i in range(0, 2*n+1):
        for j in range(0, 2*m+1):
            xi = x0 + i * h
            yj = y0 + j * k
            if (a <= xi <= A):
                if (0 <= xi <= 1 and yj <= xi**0.5) or (1 < xi <= 2 and yj <= 1/xi):
                    sums += lambda_array[j][i] * function(xi, yj)

    sums = (k * h / 9) * sums

    table.header = False
    return [sums, table]


print("[Введите количество пар (n, m)]")
q = int(input("> "))

a = 0
A = 2
b = 0
B = 1

n = []
m = []

integral_value = F_1(A/2) - F_1(0) + F_2(A) - F_2(A/2)

final_table = prettytable.PrettyTable()
final_table.field_names = ['n', 'm', 'I', 'I[smp]', '|I - I[smp]|']

print("[Введите n и m]")
for i in range(q):
    n.append(int(input(f"n[{i+1}] = ")))
    m.append(int(input(f"m[{i+1}] = ")))
    print('\n', end='')

for i in range(q):
    smp_result, table = quad_simpson(n[i], m[i], a, A, b, B)
    print(f"[Матрица Лямбда для n = {n[i]}; m = {m[i]}]")
    print(table)
    final_table.add_row([n[i], m[i], integral_value, smp_result,
                        abs(integral_value-smp_result)])

print('Численное двойное интегрирование интеграла:')
print(final_table)
