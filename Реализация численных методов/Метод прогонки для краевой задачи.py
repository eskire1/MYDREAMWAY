import numpy as np
from prettytable import PrettyTable

def solve_tridiagonal(a, b, c, d):
    """
    Решает систему линейных уравнений с трехдиагональной матрицей методом прогонки.

    Args:
        a: Нижняя диагональ матрицы (n-1 элементов).
        b: Главная диагональ матрицы (n элементов).
        c: Верхняя диагональ матрицы (n-1 элементов).
        d: Вектор правой части (n элементов).

    Returns:
        Решение системы (вектор y).
    """

    n = len(d)

    # Прямой ход
    alpha = np.zeros(n)
    beta = np.zeros(n)

    alpha[0] = -c[0] / b[0]
    beta[0] = d[0] / b[0]

    for i in range(1, n - 1):
        alpha[i] = -c[i] / (b[i] + a[i-1] * alpha[i-1])
        beta[i] = (d[i] - a[i-1] * beta[i-1]) / (b[i] + a[i-1] * alpha[i-1])

    beta[n - 1] = (d[n - 1] - a[n-2] * beta[n - 2]) / (b[n - 1] + a[n-2] * alpha[n - 2])

    # Обратный ход
    y = np.zeros(n)
    y[n - 1] = beta[n - 1]

    for i in range(n - 2, -1, -1):
        y[i] = alpha[i] * y[i + 1] + beta[i]

    return y


def solve_boundary_value_problem(n):
    """
    Решает краевую задачу для обыкновенного дифференциального уравнения второго порядка
    методом прогонки.

    Args:
        n: Количество шагов.
    """

    a = 0.0  # Левая граница отрезка
    b_val = 1.0  # Правая граница отрезка
    h = (b_val - a) / n  # Шаг

    # Определяем коэффициенты дифференциального уравнения
    def p(x):  # Коэффициент при y'
        return 2 * x

    def q(x):  # Коэффициент при y
        return 2

    def f(x):  # Правая часть уравнения
        return 2 * (5 - 2 * x)

    # Заполняем матрицу и вектор правой части
    x = np.linspace(a, b_val, n + 1)  # узлы сетки
    m = np.zeros(n + 1)
    r = np.zeros(n + 1)
    phi = np.zeros(n + 1)
    c = np.zeros(n + 1)
    d = np.zeros(n + 1)

    A = np.zeros(n - 1)
    B = np.zeros(n - 1)
    C = np.zeros(n - 1)
    D = np.zeros(n - 1)


    # Дискретизация уравнения. используем центральную разностную схему.
    for i in range(1, n): # Skip 0 and n indices due to boundary conditions

        xi = x[i]
        pi = p(xi)
        qi = q(xi)
        fi = f(xi)

        A[i-1] = 1 - (h/2)*pi
        B[i-1] = -2 + h*h*qi
        C[i-1] = 1 + (h/2)*pi
        D[i-1] = -h*h*fi


    # Граничные условия: -y'(0) + y(0) = 0, y(1) = 1.38
    # Аппроксимируем первое граничное условие центральной разностной схемой:
    # - (y[1] - y[-1]) / (2h) + y[0] = 0
    # y[-1] - мнимая точка, она нам нужна только для аппроксимации.
    # Из этой аппроксимации выразим y[-1] = y[1] - 2hy[0]
    # Подставим это в разностное уравнение для точки x [0] :
    # y''[0] + p(x[0]) * y'[0] + q(x[0]) * y[0] = f(x[0])
    # (y[1] - 2y[0] + y[-1]) / h^2 + p(x[0]) * (y[1] - y[-1]) / (2h) + q(x[0]) * y[0] = f(x[0])
    # Заменяем y[-1]:
    # (2y[1] - 2(1+h*p(x[0]))y[0] ) / h^2  + q(x[0]) * y[0] = f(x[0])
    # (2y[1] + (-2(1+h*p(x[0]))+h^2*q(x[0]))y[0] ) / h^2 = f(x[0])
    # Перепишем в виде a*y[i-1] + b*y[i] + c*y[i+1] = d:
    # a = 0, b = -2*(1+h*p(x[0])) + h^2*q(x[0]), c = 2, d = h^2*f(x[0])

    m[0] = 0
    r[0] = -2*(1 + h*p(x[0])) + h*h*q(x[0])
    phi[0] = 2
    c[0] = r[0]
    d[0] = h*h*f(x[0])

    #Второе граничное условие: y(1) = 1.38

    #Формируем векторы a, b, c, d для прогонки
    a_tridiag = A[0:n-2]
    b_tridiag = B[0:n-1]
    c_tridiag = C[0:n-2]
    d_tridiag = D[0:n-1]




    #Решаем систему
    y_internal = solve_tridiagonal(a_tridiag, b_tridiag, c_tridiag, d_tridiag)

    #Собираем все решение целиком
    y = np.zeros(n+1)
    #Подставляем граничные условия:
    y[0] = y_internal[0]*h*h*f(x[0])/ (2 - (2*(1 + h*p(x[0])) + h*h*q(x[0])))
    y[1:n] = y_internal
    y[n] = 1.38

    # Подготовка данных для вывода в таблице
    table = PrettyTable()
    table.field_names = ['n', 'x(i)', 'y(i)', 'm(i)', 'r(i)', 'phi(i)', 'c(i)', 'd(i)']

    for i in range(n + 1):
        table.add_row([n, x[i], y[i], m[i], r[i], phi[i], c[i], d[i]])

    print(table)
    print("\n")


# Решаем задачу для n = 10 и n = 20
print("Метод прогонки с шагом n = 10")
solve_boundary_value_problem(10)

print("Метод прогонки с шагом n = 20")
solve_boundary_value_problem(20)
