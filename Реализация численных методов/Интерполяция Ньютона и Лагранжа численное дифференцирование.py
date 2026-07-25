from math import sin, cos, exp
from prettytable import PrettyTable


def function(x):
    return 10 * sin(x) - exp((6*x + 5)/11)


def function_1(x):
    return 10 * cos(x) - (6/11) * exp((6*x + 5)/11)


def fact(n):
    value = 1
    if n == 0:
        return value
    else:
        for i in range(1, n+1):
            value = value * i
    return value


def first_newton_function_appr(x, x0, h):
    y_values = [
        -1.5754571034,  # y0
        0.0182803684,    # dy0
        -0.000001957,   # d2y0
        -0.0000000819,   # d3y0
        -0.00000000046,    # d4y0
        0.0000000027,    # d5y0
    ]
    q = (x - x0) / h
    result = y_values[0]

    for i in range(1, 6):
        iter_value = y_values[i]
        for j in range(i):
            iter_value = iter_value * (q - j)
        result += iter_value / fact(i)

    return [result, q]


def second_newton_function_appr(x, xn, h):
    y_values = [
        -1.484075651,  # y5
        0.01827204986,   # dy4
        -0.00000220138,   # d2y3
        -0.00000008012,   # d3y2
        0.00000000224,    # d4y1
        0.0000000027,    # d5y0
    ]
    t = (x - xn) / h
    result = y_values[0]
    #print("y_values[0] = ", result)

    for i in range(1, 6):
        #print(f"{i}-ая итерация (i)")
        iter_value = y_values[i]
        #print(f"iter_value = y_values[{i}] = {iter_value}")
        for j in range(i):
            #print(f"{j}-ая итерация (j)")
            iter_value = iter_value * (t + j)
            #print(f"iter_value после вычисления в итерации = {iter_value}")
        result += iter_value / fact(i)
        #print(f"result после цикла с j = {result}")
        #print()

    return [result, t]

####################################################################
def lagranj_function_appr(x, x0, h):
    all_x = [x0 + i * h for i in range(6)]
    const = [
        410_275_287_239.583,  # c0
        -2_027_573_873_697.917,   # c1
        4_007_547_716_145.833,  # c2
        -3_959_952_997_395.833,  # c3
        1_956_181_899_739.583,  # c4
        -386_478_034_114.583     # c5
    ]
    result = 0
    for i in range(6):
        iter_value = const[i]
        for j in range(6):
            if i == j:
                continue
            iter_value *= (x - all_x[j])
        result += iter_value
    return result


def first_newton_function_diff(x, x0, h):
    all_x = [x0 + i * h for i in range(6)]
    for i in range(5):
        if all_x[i] <= x <= all_x[i+1]:
            if round(abs(all_x[i] - x), 8) == round(abs(all_x[i+1] - x), 8):
                _x0 = all_x[i]
            elif round(abs(all_x[i] - x), 8) > round(abs(all_x[i+1] - x), 8):
                _x0 = all_x[i+1]
            else:
                _x0 = all_x[i]
    q = (x - _x0) / h
    y = [
        0.0182803684,  # dy0
        -0.000001957,  # d2y0
        -0.0000000819,  # d3y0
        -0.00000000046,  # d4y0
        0.0000000027,  # d5y0
    ]
    iters = [
        y[0],
        y[1] * (2*q - 1) / fact(2),
        y[2] * (3*q**2 - 6*q + 2) / fact(3),
        y[3] * (4*q**3 - 18*q**2 + 22*q - 6) / fact(4),
        y[4] * (5*q**4 - 40*q**3 + 105*q**2 - 100*q + 24) / fact(5)
    ]
    result = (1/h) * sum(iters)
    return [result, q, _x0]


def second_newton_function_diff(x, x0, h):
    all_x = [x0 + i * h for i in range(6)]
    for i in range(5):
        if all_x[i] <= x <= all_x[i+1]:
            if round(abs(all_x[i] - x), 8) == round(abs(all_x[i+1] - x), 8):
                _xn = all_x[i+1]
            elif round(abs(all_x[i] - x), 8) > round(abs(all_x[i+1] - x), 8):
                _xn = all_x[i+1]
            else:
                _xn = all_x[i]
    t = (x - _xn) / h
    y = [
        0.01827204986,  # dy4
        -0.00000220138,  # d2y3
        -0.00000008012,  # d3y2
        0.00000000224,  # d4y1
        0.0000000027,  # d5y0
    ]
    iters = [
        y[0],
        y[1] * (2*t + 1) / fact(2),
        y[2] * (3*t**2 + 6*t + 2) / fact(3),
        y[3] * (4*t**3 + 18*t**2 + 22*t + 6) / fact(4),
        y[4] * (5*t**4 + 40*t**3 + 105*t**2 + 100*t + 24) / fact(5),
    ]
    result = (1/h) * sum(iters)
    return [result, t, _xn]


a = 0
b = 0.01

xs = []
print(f"Введите 3 значения x из отрезка [{a}; {b}]: ")
for i in range(3):
    while True:
        x = float(input(f"x[{i+1}] = "))
        if a <= x <= b:
            xs.append(x)
            break
        else:
            print("x не из отрезка")

table = PrettyTable()
table.field_names = ["x", "y(x)", "PI_5(x)", "|y(x) - PI_5(x)|", "q",
                     "PII_5(x)", "|y(x) - PII_5(x)|", "t",
                     "L_5(x)", "|y(x) - L_5(x)|"]

h = round((b - a) / 5, 10)

for i in range(3):
    nIif_a, q_a = first_newton_function_appr(xs[i], a, h)
    nIIif_a, t_a = second_newton_function_appr(xs[i], b, h)
    lf_a = lagranj_function_appr(xs[i], a, h)
    y = function(xs[i])

    table.add_row([xs[i], y, nIif_a, abs(y - nIif_a), q_a, nIIif_a, abs(y - nIIif_a),
                   t_a, lf_a, abs(y - lf_a)])

print("Интерполирование функции")
print(table)
print('\n')

table = PrettyTable()
table.field_names = ["x", "y'(x)", "~x(0)", "(PI_5(x))'", "|y'(x) - (PI_5(x))'|", "q",
                     "~x(5)", "(PII_5(x))'", "|y'(x) - (PII_5)(x))'|", "t"]

for i in range(3):
    nIif_d, q_d, _x0 = first_newton_function_diff(xs[i], a, h)
    nIIif_d, t_d, _xn = second_newton_function_diff(xs[i], a, h)
    y1 = function_1(xs[i])

    table.add_row([xs[i], y1, _x0, nIif_d, abs(y1 - nIif_d), q_d, _xn, nIIif_d, abs(y1 - nIIif_d),
                   t_d])

print("Численное дифференцирование функции")
print(table)
