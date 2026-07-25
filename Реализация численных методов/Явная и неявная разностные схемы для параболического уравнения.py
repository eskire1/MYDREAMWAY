import math
from prettytable import PrettyTable

# Константы
class Consts:
    gamma = 0.6
    m = -1.1
    alpha = -1.3
    beta = 0.6
    M = -1.2
    N = 1.3
    a = 1
    l = 1
    n = 10
    h = l / n
    k_1 = h * h / 6

# Функции
def f(x):
    return Consts.gamma * math.exp(Consts.m * x) + math.cos(Consts.gamma * x)

def fi(t):
    return Consts.alpha * t + math.sin(Consts.beta * t)

def psi(t):
    return math.exp(Consts.N * t) + Consts.M * math.sin(Consts.m * t + Consts.N)

def return_zero_layer(t_list):
    res = []
    x = Consts.h
    t_list.append(0)
    for _ in range(Consts.n + 1):
        res.append(f(x))
        x += Consts.h
    return res

def return_next_layer(layers, t_list):
    if layers:
        res = []
        current_j = len(layers) - 1
        current_t = Consts.k_1 * (current_j + 1)
        t_list.append(current_t)

        res.append(fi(current_t))
        for i in range(1, Consts.n):
            res.append((1 / 6) * (layers[current_j][i - 1] + 4 * layers[current_j][i] + layers[current_j][i + 1]))
        res.append(psi(current_t))
        return res
    return []

def return_layers(layers, t_list, S):
    t_list.clear()
    layers.clear()
    k = Consts.h * Consts.h / S
    a = [[0.0] * (Consts.n + 1) for _ in range(Consts.n + 1)]
    b = [[0.0] * (Consts.n + 1) for _ in range(Consts.n + 1)]
    layers.append(return_zero_layer(t_list))
    for i in range(1, Consts.n + 1):
        t_list.append(i * k)
    for j in range(Consts.n):
        a[j + 1][1] = 1.0 / (2.0 + S)
        b[j + 1][1] = fi(k * (j + 1)) + S * layers[j][1]
        for i in range(2, Consts.n):
            a[j + 1][i] = 1.0 / (2.0 + S - a[j + 1][i - 1])
            b[j + 1][i] = a[j + 1][i - 1] * b[j + 1][i - 1] + S * layers[j][i]
        new_layer = [0.0] * (Consts.n + 1)
        new_layer[Consts.n] = psi(t_list[j + 1])
        for i in range(Consts.n - 1, 0, -1):
            new_layer[i] = a[j + 1][i] * (b[j + 1][i] + new_layer[i + 1])
        new_layer[0] = fi(t_list[j + 1])
        layers.append(new_layer)

def print_layers(layers, t_list, title):
    table = PrettyTable()
    headers = ['t'] + [f"x={round(i * Consts.h, 2)}" for i in range(Consts.n + 1)]
    table.field_names = headers
    for j in range(len(layers)):
        row = [round(t_list[j], 5)] + [round(val, 5) for val in layers[j]]
        table.add_row(row)
    print(title)
    print(table)

def solve(S):
    t = []
    layers_explicit = [return_zero_layer(t)]
    for _ in range(1, Consts.n + 1):
      layers_explicit.append(return_next_layer(layers_explicit, t))
    print_layers(layers_explicit, t, "Явная схема")
    t_implicit = []
    layers_implicit = []
    return_layers(layers_implicit, t_implicit, S)
    print_layers(layers_implicit, t_implicit, "Неявная схема")

# Пример запуска
if __name__ == "__main__":
    while True:
        try:
            S = float(input("S = "))
            solve(S)
        except Exception as e:
            print("Ошибка:", e)
