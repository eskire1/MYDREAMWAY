from prettytable import PrettyTable
from math import cos, sin, exp


def f(x):
    return 0.6 * exp(-1.1 * x) + cos(0.6 * x)


def F(x):
    return -1.3 * exp(x) + 0.6 * cos(0.6 * x)


def phi(t):
    return -1.3 * t + sin(0.6 * t)


def psi(t):
    return exp(1.3 * t) - 1.2 * sin(-1.1 * t) + 1.3


def u_start(x):
    return f(x)


def du_start(x):
    return F(x)


def u_0_t(t):
    return phi(t)


def u_l_t(t):
    return psi(t)


l = 1
n = 10
h = l / n
k = h


u = [[0] * (n + 1) for _ in range(n + 2)]
# Пометим левый и правый край виртуального слоя как пустые
u[0][0] = " "
u[0][n] = " "

X = [round(h * i, 2) for i in range(n+1)]
T = [round(k * j, 2) for j in range(n+1)]

# Заполняем виртуальный слой
for j in range(1, n):
    u[0][j] = u_start(X[j]) - k * du_start(X[j])

# Заполняем слой u[1][j]
for j in range(n+1):
    u[1][j] = u_start(X[j])

# Заполняем левый и правый край сетки
for i in range(2
        , n+2):
    u[i][0] = u_0_t(T[i-1])
    u[i][n] = u_l_t(T[i-1])

# Заполняем оставшуюся часть сетки
for i in range(1, n + 1):
    for j in range(1, n):
        u[i+1][j] = u[i][j-1] + u[i][j+1] - u[i-1][j]

table = PrettyTable()
table.field_names = ["t"] + [f'x={x}' for x in X]
for i in range(n + 2):
    row = []
    if i == 0:
        row.append("Вирт. слой")
    else:
        row.append(f't={T[i-1]}')
    row += [x if x == " " else round(x, 5) for x in u[i]]
    table.add_row(row)
print(table)
