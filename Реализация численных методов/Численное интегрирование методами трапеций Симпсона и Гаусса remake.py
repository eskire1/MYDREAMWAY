from prettytable import PrettyTable
import numpy as np
import math


def function(x):
    return np.array(x * math.sin(3 * x), dtype='float64')

def integral_common(x):
    return -1/3 * x * math.cos(3 * x) + 1/9 * math.sin(3 * x)

def integral(a, b):
    return integral_common(b) - integral_common(a)


def trapezoid(a, b, n):
    h = (b - a) / n
    sums = 0
    all_x = [a + k * h for k in range(n+1)]
    y = [function(x) for x in all_x]
    for i in range(1, n):
        sums += 2 * y[i]
    sums += y[0] + y[n]
    return (h / 2) * sums


def simpson(a, b, n):
    h = (b - a) / n
    sums = 0
    all_x = [a + k * h for k in range(n+1)]
    y = [function(x) for x in all_x]
    for i in range(1, n, 2):
        sums += 4 * y[i]
    for j in range(2, n, 2):
        sums += 2 * y[j]
    sums += y[0] + y[n]
    return (h / 3) * sums


def gauss(a, b, n):
    T_4 = np.array([-0.86113631, -0.33998104, 0.33998104, 0.86113631])
    A_4 = np.array([0.34785484, 0.65214516, 0.65214516, 0.34785484])

    T_8 = np.array([-0.96028986, -0.79666648, -0.52553242, -0.18343464,
                    0.18343464, 0.52553242, 0.79666648, 0.96028986])
    A_8 = np.array([0.10122854, 0.22238104, 0.31370664, 0.36268378,
                    0.36268378, 0.31370664, 0.22238104, 0.10122854])

    sums = None

    x_values_4 = function((b + a) / 2 + ((b - a) / 2) * T_4)
    x_values_8 = function((b + a) / 2 + ((b - a) / 2) * T_8)
    if n == 4:
        sums = A_4 * x_values_4
    elif n == 8:
        sums = A_8 * x_values_8
    return (b - a) / 2 * sums.sum()


a, b = [math.pi/4, math.pi/3]
y = integral(a, b)

tr_4 = trapezoid(a, b, 4)
tr_8 = trapezoid(a, b, 8)

smp_4 = simpson(a, b, 4)
smp_8 = simpson(a, b, 8)

gauss_4 = gauss(a, b, 4)
gauss_8 = gauss(a, b, 8)

print("Численное интегрирование фукции")
table = PrettyTable()
table.field_names = ['n', 'I', 'I[tr]', '|I - I[tr]|',
                     'I[sp]', '|I - I[sp]|', 'I[gs]', '|I - I[gs]']
table.add_row([4, y, tr_4, abs(y-tr_4), smp_4,
              abs(y-smp_4), gauss_4, abs(y-gauss_4)])
table.add_row([8, y, tr_8, abs(y-tr_8), smp_8,
              abs(y-smp_8), gauss_8, abs(y-gauss_8)])
print(table)
