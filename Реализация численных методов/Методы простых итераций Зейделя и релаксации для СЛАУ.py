from prettytable import PrettyTable


def calculate_iteration_CI(X: list, alpha: list, betta: list) -> list:
    new_iteration = []
    for i in range(len(X)):
        sums = betta[i]
        for j in range(len(X)):
            if i != j:
                sums += alpha[i][j] * X[j]
        new_iteration.append(sums)
    return new_iteration


def check_diff(l_appr, c_appr):
    deltas = []
    for i in range(len(l_appr)):
        deltas.append(abs(c_appr[i] - l_appr[i]))
    return deltas


x = int(input("x0 = "))
y = int(input("y0 = "))
z = int(input("z0 = "))

A = [[6, -2, -3],
     [-3, -5, 1],
     [2, -3, 6]]

B = [10,
     -12,
     15]

alpha = [[], [], []]
betta = []


for i in range(3):
    for j in range(3):
        alpha[i].append(-1 * A[i][j] / A[i][i])
    betta.append(B[i] / A[i][i])


def calculate_common_iterations(alpha, betta, eps):
    k = 1
    table = PrettyTable()
    table.field_names = ['k+1', 'x(k)', 'y(k)', 'z(k)', 'x(k+1)',
                         'y(k+1)', 'z(k+1)', 'd(x)', 'd(y)', 'd(z)', 'S']

    last_appr = []
    appr = [x, y, z]

    last_appr = appr.copy()
    appr = calculate_iteration_CI(appr, alpha, betta)
    delta = check_diff(last_appr, appr)

    while sum(delta) > eps:
        table.add_row([k, round(last_appr[0], 7), round(last_appr[1], 7), round(last_appr[2], 7),
                       round(appr[0], 7), round(appr[1], 7), round(appr[2], 7),
                       round(delta[0], 7), round(
                           delta[1], 7), round(delta[2], 7),
                       round(sum(delta), 7)])
        last_appr = appr.copy()
        appr = calculate_iteration_CI(appr, alpha, betta)
        delta = check_diff(last_appr, appr)
        k += 1

    table.add_row([k, round(last_appr[0], 7), round(last_appr[1], 7), round(last_appr[2], 7),
                   round(appr[0], 7), round(appr[1], 7), round(appr[2], 7),
                   round(delta[0], 7), round(delta[1], 7), round(delta[2], 7),
                   round(sum(delta), 7)])
    return [k, table]


def calculate_iteration_Z(X: list, alpha: list, betta: list) -> list:
    new_iteration = []
    for i in range(len(X)):
        sums = betta[i]

        for j in range(i):
            sums += alpha[i][j] * new_iteration[j]

        for j in range(i+1, len(X)):
            sums += alpha[i][j] * X[j]

        new_iteration.append(sums)
    return new_iteration


def calculate_zeidel(alpha, betta, eps):
    k = 1
    table = PrettyTable()
    table.field_names = ['k+1', 'x(k)', 'y(k)', 'z(k)', 'x(k+1)',
                         'y(k+1)', 'z(k+1)', 'd(x)', 'd(y)', 'd(z)', 'S']

    last_appr = []
    appr = [x, y, z]

    last_appr = appr.copy()
    appr = calculate_iteration_Z(appr, alpha, betta)
    delta = check_diff(last_appr, appr)

    while sum(delta) > eps:
        table.add_row([k, round(last_appr[0], 7), round(last_appr[1], 7), round(last_appr[2], 7),
                       round(appr[0], 7), round(appr[1], 7), round(appr[2], 7),
                       round(delta[0], 7), round(
                           delta[1], 7), round(delta[2], 7),
                       round(sum(delta), 7)])
        last_appr = appr.copy()
        appr = calculate_iteration_Z(appr, alpha, betta)
        delta = check_diff(last_appr, appr)
        k += 1

    table.add_row([k, round(last_appr[0], 7), round(last_appr[1], 7), round(last_appr[2], 7),
                   round(appr[0], 7), round(appr[1], 7), round(appr[2], 7),
                   round(delta[0], 7), round(delta[1], 7), round(delta[2], 7),
                   round(sum(delta), 7)])
    return [k, table]


def calculate_iteration_R(X: list, alpha: list, betta: list) -> list:
    Rs = []
    max_index = -1
    maxs = -1

    for i in range(len(X)):
        sums = betta[i] - X[i]

        for j in range(len(X)):
            if i != j:
                sums += alpha[i][j] * X[j]

        Rs.append(sums)

        if abs(sums) > maxs:
            max_index = i
            maxs = abs(sums)

    return [Rs, max_index]


def calculate_relaxation(alpha, betta, eps):
    k = 0
    table = PrettyTable()
    table.field_names = [
        'k', 'x(k)', 'y(k)', 'z(k)', 'Rx(k)', 'Ry(k)', 'Rz(k)', 'max(|R|)']

    appr = [x, y, z]

    all_R = calculate_iteration_R(appr, alpha, betta)
    abs_R = [abs(x) for x in all_R[0]]

    while (max(abs_R)) > eps:

        table.add_row([k, round(appr[0], 9), round(appr[1], 9), round(appr[2], 9),
                       round(all_R[0][0], 9), round(
                       all_R[0][1], 9), round(all_R[0][2], 9),
                       round(max(abs_R), 9)])

        max_i = all_R[1]
        appr[max_i] += all_R[0][max_i]
        all_R = calculate_iteration_R(appr, alpha, betta)
        abs_R = [abs(x) for x in all_R[0]]
        k += 1

    table.add_row([k, round(appr[0], 9), round(appr[1], 9), round(appr[2], 9),
                   round(all_R[0][0], 9), round(
                       all_R[0][1], 9), round(all_R[0][2], 9),
                   "-"])
    return [k, table]


CI_1 = calculate_common_iterations(alpha, betta, 0.001)
Z_1 = calculate_zeidel(alpha, betta, 0.001)
R_1 = calculate_relaxation(alpha, betta, 0.001)

CI_2 = calculate_common_iterations(alpha, betta, 0.00001)
Z_2 = calculate_zeidel(alpha, betta, 0.00001)
R_2 = calculate_relaxation(alpha, betta, 0.00001)

print("Метод простых итерации (eps = 0.001)")
print(CI_1[1])
input("Продолжить?")
print("\n")

print("Метод Зейделя (eps = 0.001)")
print(Z_1[1])
input("Продолжить?")
print("\n")

print("Метод Релаксации (eps = 0.001)")
print(R_1[1])
input("Продолжить?")
print("\n")

print("Метод простых итерации (eps = 0.00001)")
print(CI_2[1])
input("Продолжить?")
print("\n")

print("Метод Зейделя (eps = 0.00001)")
print(Z_2[1])
input("Продолжить?")
print("\n")

print("Метод Релаксации (eps = 0.00001)")
print(R_2[1])
print("\n")

# final_table = PrettyTable()
# print("Сводная таблица по быстроте приближений (k):")
# final_table.field_names = ["eps", "Прост. ит.", "Мет. Зей.", "Мет. Рел."]
# final_table.add_row(['10e-3', CI_1[0], Z_1[0], R_1[0]])
# final_table.add_row(['10e-5', CI_2[0], Z_2[0], R_2[0]])
# print(final_table)
