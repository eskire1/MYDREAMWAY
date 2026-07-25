from prettytable import PrettyTable
from math import cos, sin


c = 0.1
a, b = [0, 0.75]


def function(x):
    return 3 * cos(2 * x) - x + 0.25


def function_1(x):
    return ( - 6 * sin(2 * x) - 1)


def function_2(x):
    return ( - 12 * cos(2 * x))


def fi(x):
    return x + c * function(x) #итерационная формула метода простых итераций


def newton_iteration(x):
    return x - function(x) / function_1(x) #итерационная формула метода Ньютона


def upgraded_newton_iteration(x, x0):
    return x - function(x) / function_1(x0) #итерационная формула модифицированного метода Ньютона


def common_iterations(eps, delta, x0):
    table = PrettyTable()
    table.field_names = [
        "n+1", "x(n)", "x(n+1)", "|x(n+1) - x(n)|", "| f(x(n+1)) |"]

    last_iter = x0
    next_iter = fi(last_iter)
    value_check = abs(function(next_iter))
    n = 1

    while abs(next_iter - last_iter) > eps or value_check > delta:
        table.add_row([n, last_iter, next_iter, abs(
            next_iter - last_iter), value_check])
        last_iter = next_iter
        next_iter = fi(last_iter)
        value_check = abs(function(next_iter))
        n += 1

    table.add_row([n, last_iter, next_iter, abs(
        next_iter - last_iter), value_check])

    return table


def newton_method(eps, delta, x0):
    if function(x0) * function_2(x0) <= 0:
        print("Метод Ньютона, function(x0) * function_2(x0) = ", function(x0) * function_2(x0))
        print("function(x0) = ", function(x0))
        print("function_2(x0) = " + str(function_2(x0)) + "\n")
        return False
    table = PrettyTable()
    table.field_names = [
        "n+1", "x(n)", "x(n+1)", "|x(n+1) - x(n)|", "| f(x(n+1)) |"]

    last_iter = x0
    next_iter = newton_iteration(last_iter)
    value_check = abs(function(next_iter))
    n = 1

    while abs(next_iter - last_iter) > eps or value_check > delta:
        table.add_row([n, last_iter, next_iter, abs(
            next_iter - last_iter), value_check])
        last_iter = next_iter
        next_iter = newton_iteration(last_iter)
        value_check = abs(function(next_iter))
        n += 1

    table.add_row([n, last_iter, next_iter, abs(
        next_iter - last_iter), value_check])

    return table


def upgraded_newton_method(eps, delta, x0):
    if function(x0) * function_2(x0) <= 0:
        print("Модифицированный Метод Ньютона, function(x0) * function_2(x0) = ", function(x0) * function_2(x0))
        print("function(x0) = ", function(x0))
        print("function_2(x0) = " + str(function_2(x0)) + "\n")
        return False
    table = PrettyTable()
    table.field_names = [
        "n+1", "x(n)", "x(n+1)", "|x(n+1) - x(n)|", "| f(x(n+1)) |"]

    last_iter = x0
    next_iter = upgraded_newton_iteration(last_iter, x0)
    value_check = abs(function(next_iter))
    n = 1

    while abs(next_iter - last_iter) > eps or value_check > delta:
        table.add_row([n, last_iter, next_iter, abs(
            next_iter - last_iter), value_check])
        last_iter = next_iter
        next_iter = upgraded_newton_iteration(last_iter, x0)
        value_check = abs(function(next_iter))
        n += 1

    table.add_row([n, last_iter, next_iter, abs(
        next_iter - last_iter), value_check])

    return table


while True:
    x0 = float(input(f"Введите x0 из отрезка [{a} : {b}]: "))
    if a <= x0 <= b:
        break
    else:
        print("x0 не входит в отрезок")

ci_1 = common_iterations(0.001, 0.001, x0)
ci_2 = common_iterations(0.00001, 0.00001, x0)

ni_1 = newton_method(0.001, 0.001, x0)
ni_2 = newton_method(0.00001, 0.00001, x0)

uni_1 = upgraded_newton_method(0.001, 0.001, x0)
uni_2 = upgraded_newton_method(0.00001, 0.00001, x0)

print("Метод простых итерации (eps = 1e-03; delta = 1e-03)")
print(ci_1)
input("Продолжить?")
print("\n")

print("Метод Ньютона (eps = 1e-03; delta = 1e-03)")
if not ni_1:
    print("Не выполняется достаточное условие сходимости метода Ньютона")
else:
    print(ni_1)
input("Продолжить?")
print("\n")

print("Модифицированный метод Ньютона (eps = 1e-03; delta = 1e-03)")
if not uni_1:
    print("Не выполняется достаточное условие сходимости модифицированного метода Ньютона")
else:
    print(uni_1)
input("Продолжить?")
print("\n")

print("Метод простых итерации (eps = 1e-05; delta = 1e-05)")
print(ci_2)
input("Продолжить?")
print("\n")

print("Метод Ньютона (eps = 1e-05; delta = 1e-05)")
if not ni_2:
    print("Не выполняется достаточное условие сходимости метода Ньютона")
else:
    print(ni_2)
input("Продолжить?")
print("\n")

print("Модифицированный метод Ньютона (eps = 1e-05; delta = 1e-05)")
if not uni_2:
    print("Не выполняется достаточное условие сходимости модифицированного метода Ньютона")
else:
    print(uni_2)
