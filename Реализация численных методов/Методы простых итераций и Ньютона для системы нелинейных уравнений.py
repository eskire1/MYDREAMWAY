import numpy as np
from prettytable import PrettyTable


def f1(x, y):
    return x + y - 1


def f2(x, y):
    return x - y ** 2 + 2


def coefalpha(x, y):
    return -((2 * y) / (2 * y + 1))


def coefbeta(x, y):
    return -(1 / (2 * y + 1))


def coefgamma(x, y):
    return -(1 / (2 * y + 1))


def coefdelta(x, y):
    return (1 / (2 * y + 1))


def phi1(x, y):
    return x + coefalpha(x, y) * f1(x, y) + coefbeta(x, y) * f2(x, y)


def phi2(x, y):
    return y + coefgamma(x, y) * f1(x, y) + coefdelta(x, y) * f2(x, y)


# def detW(x, y):
#     return -2 * y - 1


def Fxk(x, y):
    #return x - (-2 * x * y - y ** 2 + 2 * y - x - 2) / detW(x, y)
    return x - ((2 * y)/(2 * y + 1) * (x + y - 1) + 1/(2 * y + 1) * (x - y ** 2 + 2))
def Fyk(x, y):
    #return y - (-y - y ** 2 + 3) / detW(x, y)
    return y - (1/(2 * y + 1) * (x + y - 1) + 1/((-2) * y - 1) * (x - y ** 2 + 2))

def Fxk_mod(x, y, y0):
    return x - ((2 * y0)/(2 * y0 + 1) * (x + y - 1) + 1/(2 * y0 + 1) * (x - y ** 2 + 2))

def Fyk_mod(x, y, y0):
    return y - (1/(2 * y0 + 1) * (x + y - 1) + 1/((-2) * y0 - 1) * (x - y ** 2 + 2))

def MPI(x, y, eps):
    results = []
    iteration = 1
    while True:
        xp, yp = x, y
        x, y = phi1(xp, yp), phi2(xp, yp)
        results.append((iteration, xp, x, abs(x - xp), yp, y, abs(y - yp), abs(f1(x, y)), abs(f2(x, y))))
        if abs(x - xp) <= eps and abs(y - yp) <= eps and abs(f1(x, y)) <= eps and abs(f2(x, y)) <= eps:
            break
        iteration += 1
    return results


def NewtonMethod(x, y, eps):
    results = []
    iteration = 1
    while True:
        xp, yp = x, y
        x, y = Fxk(xp, yp), Fyk(xp, yp)
        results.append((iteration, xp, x, abs(x - xp), yp, y, abs(y - yp), abs(f1(x, y)), abs(f2(x, y))))
        if abs(x - xp) <= eps and abs(y - yp) <= eps and abs(f1(x, y)) <= eps and abs(f2(x, y)) <= eps:
            break
        iteration += 1
    return results


def NewtonMethodMod(x, y, eps):
    results = []
    iteration = 1
    y0 = y
    while True:
        xp, yp = x, y
        x, y = Fxk_mod(xp, yp, y0), Fyk_mod(xp, yp, y0)
        results.append((iteration, xp, x, abs(x - xp), yp, y, abs(y - yp), abs(f1(x, y)), abs(f2(x, y))))
        if abs(x - xp) <= eps and abs(y - yp) <= eps and abs(f1(x, y)) <= eps and abs(f2(x, y)) <= eps:
            break
        iteration += 1
    return results


def print_results(method_name, results):
    print(f"\n{method_name}")
    table = PrettyTable()
    table.field_names = ["k+1", "x_k", "x_(k+1)", "|x_(k+1) - x_k|", "y_k", "y_(k+1)", "|y_(k+1) - y_k|", "|f1(x,y)|", "|f2(x,y)|"]
    for row in results:
        table.add_row(row)
    print(table)
    print(f"Ответы: x = {results[-1][2]}, y = {results[-1][5]}")


if __name__ == "__main__":
    x = float(input("Введите x = ").replace(',', '.'))
    y = float(input("Введите y = ").replace(',', '.'))

    print_results("МЕТОД ПРОСТЫХ ИТЕРАЦИЙ e = (10^-3)", MPI(x, y, 1e-3))
    print_results("МЕТОД ПРОСТЫХ ИТЕРАЦИЙ e = (10^-5)", MPI(x, y, 1e-5))
    print_results("МЕТОД НЬЮТОНА e = (10^-3)", NewtonMethod(x, y, 1e-3))
    print_results("МЕТОД НЬЮТОНА e = (10^-5)", NewtonMethod(x, y, 1e-5))
    print_results("МЕТОД НЬЮТОНА МОД e = (10^-3)", NewtonMethodMod(x, y, 1e-3))
    print_results("МЕТОД НЬЮТОНА МОД e = (10^-5)", NewtonMethodMod(x, y, 1e-5))

