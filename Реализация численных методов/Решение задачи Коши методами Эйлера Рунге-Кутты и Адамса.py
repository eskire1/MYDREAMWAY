import math
from prettytable import PrettyTable

# Функция для вычисления правой части дифференциального уравнения
def f(x, y):
  return x**3 * y

# Точное решение (для вычисления погрешности)
def exact_solution(x):
  C = 2 * math.exp(-4)
  return C * math.exp(x**4 / 4)

# Метод Эйлера (используется только для старта и для таблицы)
def euler(x, y, h):
    return y + h * f(x, y)

# Метод Рунге-Кутты 4-го порядка (используется для старта и для таблицы)
def runge_kutta(x, y, h):
    k1 = h * f(x, y)
    k2 = h * f(x + h / 2, y + k1 / 2)
    k3 = h * f(x + h / 2, y + k2 / 2)
    k4 = h * f(x + h, y + k3)
    return y + (k1 + 2 * k2 + 2 * k3 + k4) / 6

# Метод Адамса
def adams(x, y_i, y_im1, y_im2, y_im3, h):
    f_i = f(x, y_i)
    f_im1 = f(x - h, y_im1)
    f_im2 = f(x - 2*h, y_im2)
    f_im3 = f(x - 3*h, y_im3)
    return y_i + (h / 24) * (55*f_i - 59*f_im1 + 37*f_im2 - 9*f_im3)



def solve_ode(a, b, n, y0):
    h = (b - a) / n
    x_values = [a + i * h for i in range(n + 1)]

    # Инициализация для метода Адамса
    y_euler = [0]*(n + 1)
    y_rk = [0]*(n + 1)
    y_adams = [0]*(n + 1)

    y_euler[0] = y0
    y_rk[0] = y0
    y_adams[0] = y0


    y_euler[1] = euler(a, y0, h)
    y_euler[2] = euler(a + h, y_euler[1], h)
    y_euler[3] = euler(a + 2*h, y_euler[2], h)

    # Используем Рунге-Кутту для вычисления y1, y2 и y3
    y_rk[1] = runge_kutta(a, y0, h)
    y_rk[2] = runge_kutta(a + h, y_rk[1], h)
    y_rk[3] = runge_kutta(a + 2*h, y_rk[2], h)

    y_adams[1] = y_rk[1]
    y_adams[2] = y_rk[2]
    y_adams[3] = y_rk[3]



    table = PrettyTable()
    table.field_names = ["i", "x(i)", "y(x(i))", "y^Э(i)", "|y(x(i)) - y^Э(i)|",
                           "y^(Р-К)(i)", "|y(x(i)) - y^(Р-К)(i)|", "y^A(i)", "|y(x(i)) - y^A(i)|"]

    # Заполняем первые 4 строки таблицы
    for i in range(4):
        x = x_values[i]
        y_exact = exact_solution(x)

        euler_error = abs(y_exact - y_euler[i])

        rk_error = abs(y_exact - y_rk[i])

        adams_error = abs(y_exact - y_adams[i])

        table.add_row([i, f"{x:.6f}", f"{y_exact:.6f}", f"{y_euler[i]:.6f}", f"{euler_error:.6f}",
                       f"{y_rk[i]:.6f}", f"{rk_error:.6f}", f"{y_adams[i]:.6f}", f"{adams_error:.6f}"])


    for i in range(4, n + 1): # Начинаем с i=4, т.к. нужно 4 предыдущих значения для метода Адамса
        x = x_values[i]
        y_exact = exact_solution(x)

        # Метод Эйлера (вычисляем просто, чтобы заполнить таблицу)
        y_euler[i] = euler(x_values[i-1], y_euler[i-1], h)

        # Метод Рунге-Кутты
        y_rk[i] = runge_kutta(x_values[i-1], y_rk[i-1], h)

        # Метод Адамса
        y_adams[i] = adams(x_values[i-1], y_adams[i-1], y_adams[i-2], y_adams[i-3], y_adams[i-4], h)


        euler_error = abs(y_exact - y_euler[i])

        rk_error = abs(y_exact - y_rk[i])

        adams_error = abs(y_exact - y_adams[i])

        table.add_row([i, f"{x:.6f}", f"{y_exact:.6f}", f"{y_euler[i]:.6f}", f"{euler_error:.6f}",
                       f"{y_rk[i]:.6f}", f"{rk_error:.6f}", f"{y_adams[i]:.6f}", f"{adams_error:.6f}"])


    return table



table = PrettyTable()
flag_table_filled = 0

def solve_ode_rk(a, b, y0, n, eps):
    global flag_table_filled, table
    h = (b - a) / n
    H = h * 2
    x_values = [a + i * h for i in range(n + 1)]
    y_rk_h = [0]*(n + 1)
    y_rk_H = [0]*(n + 1)

    y_rk_h[0] = y0
    y_rk_H[0] = y0

    if flag_table_filled == 0:
        #table = PrettyTable()
        table.field_names = ["i", "x(i)", "y(i)", "y(i)_rk_h", "y(i)_rk_H", "|y(i)_rk_h - y(i)_rk_H|", "|y(i) - y(i)_rk_h|", "h"]
        #table.field_names = ["i", "x(i)", "y(i)", "y(i)_rk_h"]

        table.add_row([0, f"{a:.16f}", f"{y0:.16f}", f"{y_rk_h[0]:.16f}", f"{y_rk_H[0]:.16f}", f"{0:.16f}", f"{abs(exact_solution(x_values[0]) - y_rk_h[0]):.16f}", f"{h:.4f}"])
        flag_table_filled = 1

    for i in range (1, n + 1):
        y_exact = exact_solution(x_values[i])
        y_rk_h[i] = runge_kutta(x_values[i-1], y_rk_h[i-1], h)

        if i % 2 == 0:
            y_rk_H[i] = runge_kutta(x_values[i-2], y_rk_H[i-2], H)
            y_error = abs(y_rk_h[i] - y_rk_H[i])

            if y_error > eps:
                table.add_row([i, x_values[i], y_exact, y_rk_h[i], y_rk_H[i], y_error, f"{abs(y_exact - y_rk_h[i]):.16f}", f"{h:.4f}"])
                table.add_row([i-2, x_values[i-2], exact_solution(x_values[i-2]), f"{y_rk_h[i-2]:.16f}", f"{y_rk_H[i-2]:.16f}", f"{abs(y_rk_h[i-2] - y_rk_H[i-2]):.16f}", f"{abs(exact_solution(x_values[i-2]) - y_rk_h[i-2]):.16f}", f"{h/2:.4f}"])
                solve_ode_rk(x_values[i - 2], b, y_rk_h[i - 2], (n - i + 2) * 2, eps)
                return table

            table.add_row([i, x_values[i], y_exact, y_rk_h[i], y_rk_H[i], y_error, abs(y_exact - y_rk_h[i]), f"{h:.4f}"])

        else:
            table.add_row([i, x_values[i], y_exact, y_rk_h[i], "", "", abs(y_exact - y_rk_h[i]), ""])

    return table


# Начальные условия и интервал
a = -2
b = -1
y0 = 2

eps1 = 5*10 ** (-2)
eps2 = 3*10 ** (-3)


print("Решение для n = 10:")
print(solve_ode(a, b, 10, y0))

print("\nРешение для n = 20:")
print(solve_ode(a, b, 20, y0))

# Для метода Рунге-Кутта при n = 10 и E = 5*10^(-2)
print("\nРешение методом Рунге-Кутта при n = 10 и E = 5*10^(-2):")
print(solve_ode_rk(a, b, y0, 10, eps1))

table.clear()
flag_table_filled = 0

# Для метода Рунге-Кутта при n = 20 и E = 3*10^(-3)
print("\nРешение методом Рунге-Кутта при n = 20 и E = 3*10^(-3):")
print(solve_ode_rk(a, b, y0, 20, eps2))
