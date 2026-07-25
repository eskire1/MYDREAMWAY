#include <iostream>
#include <string>
#include <windows.h>
#include <time.h>

using namespace std;

int quickSort_diff_count = 0;
int quickSort_change_count = 0;

bool is_good_number(string number) {
	bool flag = true;
	for (int i = 0; i < number.length(); i++) {
		if (!isdigit(number[i])) {
			flag = false;
			break;
		}
	}
	if (flag && number.length() > 0 && number != "0") {
		return true;
	}
	else {
		return false;
	}
}

void shell_sort(int arr[], int* steps, int steps_size, int size_arr) {
	cout << "Сортируем..." << endl;
	int step;
	int change_counts = 0;
	int diff_counts = 0;
	for (int x = 0; x < steps_size; x++) {
		step = steps[x];
		for (int i = step; i < size_arr; i++) {
			int j = i;
			change_counts++;
			int insert_el = arr[i];
			while (j >= 0) {
				diff_counts++;
				if ((arr[j-step] <= insert_el) || (j == 0) || (j-step < 0)) {
					change_counts++;
					arr[j] = insert_el;
					break;
				}
				change_counts++;
				arr[j] = arr[j-step];
				j -= step;
			}
		}
	}
	cout << "Результат:" << endl;
	for (int i = 0; i < size_arr; i++) {
		cout << arr[i] << " ";
	}
	cout << endl;
	cout << "Количество сравнений: " << diff_counts << endl;
	cout << "Количество перестановок: " << change_counts / 3 << endl;
}

void pyramid_sort(int arr[], int size_arr) {
    size_arr++;
	int pyramid[size_arr];
	int temp, current, smallest;

	int change_count_for_build = 0;
	int change_count_for_rebuild = 0;
	int diff_count_for_build = 0;
	int diff_count_for_rebuild = 0;

	int pyramid_size = size_arr - 1;
	for (int i = 1; i < size_arr; i++) {
		current = i;

		change_count_for_build++;
		pyramid[i] = arr[i-1];

		while (current > 1) {
			diff_count_for_build++;
			if (pyramid[current] < pyramid[current/2]) {

				change_count_for_build += 3;
				temp = pyramid[current];
				pyramid[current] = pyramid[current/2];
				pyramid[current / 2] = temp;

			}
			else {
				break;
			}
			current = current / 2;
		}
	}

	for (int i = 0; i < size_arr; i++) {
		change_count_for_build += 2;
		arr[i] = pyramid[1];
		pyramid[1] = pyramid[pyramid_size];

		pyramid_size -= 1;
		current = 1;
		while (current <= pyramid_size) {
			smallest = current;

			diff_count_for_rebuild++;
			if ((pyramid[current] > pyramid[current*2]) && (current*2 <= pyramid_size)) {
				smallest = current * 2;
			}

			diff_count_for_rebuild++;
			if ((pyramid[smallest] > pyramid[current*2 + 1]) && ((current*2 + 1) <= pyramid_size)) {
				smallest = current * 2 + 1;
			}

			if (smallest == current) {
				break;
			}
			else {

				change_count_for_rebuild += 3;
				temp = pyramid[current];
				pyramid[current] = pyramid[smallest];
				pyramid[smallest] = temp;

				current = smallest;
			}
		}
	}
	cout << "Результат:" << endl;
	for (int i = 0; i < size_arr; i++) {
		cout << arr[i] << " ";
	}
	cout << endl;
	cout << "---------------------" << endl;
	cout << "Общее количество перестановок: " << change_count_for_build/3 + change_count_for_rebuild/3 << endl;
	cout << "Общее количество сравнений: " << diff_count_for_build + diff_count_for_rebuild << endl;
}

void quick_sort(int arr[], int _i, int size_arr) {
	int mid = arr[(size_arr + _i) / 2];
	int i = _i;
	int j = size_arr;
	while (i <= j) {
		while (arr[i] < mid) {
			quickSort_diff_count++;
			i++;
		}
		while (arr[j] > mid) {
			quickSort_diff_count++;
			j--;
		}
		if (i <= j) {
			quickSort_change_count++;
			int temp = arr[j];
			arr[j] = arr[i];
			arr[i] = temp;
			i++;
			j--;
		}
	}
	if (_i <= j) {
		quick_sort(arr, _i, j);
	}
	if (i <= size_arr) {
		quick_sort(arr, i, size_arr);
	}
}

int main() {
	SetConsoleCP(1251);
	SetConsoleOutputCP(1251);
	srand(time(NULL));
	string inp = "";
	int step_count, step;
	int random;
	int c = 5;
	bool arr_created = false;
	int size_arr = 0;
	int* arr;
	int* temp;
	while (true) {
		if (c == 5) {
			cout << "---------------------" << endl;
			cout << "Выберите команду:" << endl;
			cout << "1) Создать массив с случайными элементами" << endl << "2) Показать исходный массив" << endl << "3) Сортировка Шелла" << endl << "4) Пирамидная сортировка" << endl << "5) Быстрая сортировка" << endl << "6) Выход" << endl;
			c = 0;
		}
		cout << "Команда:" << endl;
		cout << "> ";
		getline(cin, inp);
		if (inp == "1") {
			cout << "Введите размер массива: " << endl;
			while (true) {
				cout << "> ";
				getline(cin, inp);
				if (is_good_number(inp)) {
					break;
				}
				cout << "Введено не натуральное число" << endl;
			}
			if (stoi(inp) != size_arr) {
				if (arr_created) {
					delete [] arr;
					delete [] temp;
				}
				size_arr = stoi(inp);
				arr = new int[size_arr];
				temp = new int[size_arr];
			}

			for (int i = 0; i < size_arr; i++) {
				random = rand() % (size_arr + 10);
				arr[i] = random;
				temp[i] = random;
			}
			if (!arr_created) {
				arr_created = true;
			}
			cout << "Массив создан!" << endl;
		}
		else if (inp == "2") {
			if (!arr_created) {
				cout << "Массив не создан!" << endl;
				continue;
			}
			for (int i = 0; i < size_arr; i++) {
				cout << temp[i] << " ";
			}
			cout << endl;
		}
		else if (inp == "3") {
			if (!arr_created) {
				cout << "Массив не создан!" << endl;
				continue;
			}
			cout << "Введите количество шагов:" << endl;
			while (true) {
				cout << "> ";
				getline(cin, inp);
				if (is_good_number(inp)) {
					break;
				}
				cout << "Получено не натуральное число" << endl;
			}
			step_count = stoi(inp);
			int* steps = new int[step_count];
			cout << "Введите величины шагов в убывающем порядке" << endl;
			for (int i = 0; i < step_count; i++) {
				if (i == step_count - 1) {
					cout << "Последний шаг обязательно должен быть равен 1, поэтому ставим его по умолчанию" << endl;
					steps[i] = 1;
					break;
				}
				cout << "Введите значение шага:" << endl;
				cout << "Минимальная величина, которая доступна: " << step_count-i << endl;
				while (true) {
					cout << "> ";
					getline(cin, inp);
					if (is_good_number(inp)) {
						step = stoi(inp);
						if (step >= size_arr) {
							cout << "Шаг не может быть больше длины массива" << endl;
							continue;
						}
						if (step < step_count-i) {
							cout << "Пока такая величина не может быть принята" << endl;
							continue;
						}
						if (i != 0) {
							if (step >= steps[i-1]) {
								cout << "Шаги должны быть в убывающем порядке" << endl;
								continue;
							}
						}
						break;
					}
				cout << "Получено не натуральное число" << endl;
				}
				steps[i] = step;
			}

			shell_sort(temp, steps, step_count, size_arr);
			for (int i = 0; i < size_arr; i++) {
				temp[i] = arr[i];
			}
			delete [] steps;
		}
		else if (inp == "4") {
			if (!arr_created) {
				cout << "Массив не создан!" << endl;
				continue;
			}
			pyramid_sort(temp, size_arr);
			for (int i = 0; i < size_arr; i++) {
				temp[i] = arr[i];
			}
		}
		else if (inp == "5") {
			quickSort_change_count = 0;
			quickSort_diff_count = 0;
			if (!arr_created) {
				cout << "Массив не создан!" << endl;
				continue;
			}
			cout << "Сортируем..." << endl;
			quick_sort(temp, 0, size_arr-1);
			cout << "Результат: " << endl;
			for (int i = 0; i < size_arr; i++) {
				cout << temp[i] << " ";
				temp[i] = arr[i];
			}
			cout << endl;
			cout << "Количество перестановок: " << quickSort_change_count << endl;
			cout << "Количество сравнений: " << quickSort_diff_count << endl;
		}
		else if (inp == "6") {
			cout << "Выходим..." << endl;
			if (arr_created) {
				delete [] arr;
				delete [] temp;
			}
			break;
		}
		else {
			cout << "Неизвестная команда" << endl;
		}
		c++;
		cout << "------------------" << endl;
    }
	return 0;
}
