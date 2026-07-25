import numpy as np

A = np.array([[1, 7, 2, 1],
     [7, 3, 5, 5],
     [2, 5, 4, 3],
     [1, 5, 3, 9]])

dimension = len(A)

def calculate_degree(n):
    matrixs = np.array([None] * n)
    matrixs[0] = A
    for i in range(n - 1):
        matrixs[i + 1] = matrixs[i] @ matrixs[0]

    return matrixs

def get_Sp(matrixs):
    traces = [np.trace(matrix) for matrix in matrixs]
    return traces


def values_in_parentheses(i, Sp_values, p_array): #Составляет из двух массивов один двухмерный массив.
    values = np.array([None] * 2)
    values[0] = Sp_values[:i]
    values[1] = np.empty(i)
    values[1][0] = 0
    for z in range(1, i):
        values[1][z] = p_array[z - 1]

    return values

def get_sum(coeffs, i): #coeffs - массив из двух массивов. 1-й массив: значения Sp; 2-й массив: значения p.
    sum = 0.0
    for z in range(i):
        if z == 0:
            sum += coeffs[0][i-1]
            continue

        sum += coeffs[1][z] * coeffs[0][i-1-z]

    return sum


def get_p(Sp_values, n):
    p_array = np.array([None] * n)
    p_array[0] = -Sp_values[0]
    for i in range(2, n + 1):
        coeffs_in_parentheses = values_in_parentheses(i, Sp_values, p_array)
        sum = get_sum(coeffs_in_parentheses, i)
        p_array[i-1] = (-1/i) * sum

    return p_array


matrixs = calculate_degree(dimension)
print(matrixs)

Sp = get_Sp(matrixs)
print(Sp)

p = get_p(Sp, dimension)
print(p)

# Sp_values = np.random.rand(5)
# print(Sp_values)
#
# p_array_rand = np.random.rand(5)
# print(p_array_rand)

#i = 2

# values = values_in_parentheses(i, Sp_values, p_array_rand)
# print(values)

def inverse_A(matrixs, p_array):
    if p[3] == 0:
        print("p(n) = 0, вычисление невозможно!")

    ones = np.eye(4)  # Создаем единичную матрицу
    matrixs[len(matrixs) - 1] = ones

    new_matrixs = np.empty_like(matrixs)
    new_matrixs[1:] = matrixs[:3]
    print(new_matrixs)
    new_matrixs[0] = matrixs[3]
    print(new_matrixs)
    matrixs = new_matrixs
    print("----------------------------------------------------")
    print(matrixs)
    print("----------------------")
    p_array = p
    p_and_matrixs = values_in_parentheses(len(matrixs), matrixs, p_array)
    print(p_and_matrixs)
    #print(p_and_matrixs[1][1])
    A_sum = get_sum(p_and_matrixs, len(matrixs))
    inverse_A = -(1/p_array[len(matrixs) - 1]) * A_sum

    return inverse_A

inverse_A = inverse_A(matrixs, p)
print(inverse_A)



# ---------- То, как мы матрицы разворачивали ^^ (первые три и последнюю вперёд всех ставили) -----------
# reversed_part = matrixs[:3][::-1] # Отрезаем ту часть, что нужно перевернуть
# new_matrixs = np.empty_like(matrixs)
# new_matrixs[:3] = matrixs[2::-1]  # Переворачиваем первые три
# new_matrixs[3] = matrixs[3]  # Копируем четвертый элемент из старого массива в новый массив матриц
# matrixs = new_matrixs  # Меняем старый массив на новый