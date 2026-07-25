#include <iostream>
#include <string>
#include <windows.h>
#include <time.h>
#include <cmath>
#include <vector>
#include <list>

using namespace std;

struct Stack {
	int size_num = -1;
	int num;
	Stack* next = nullptr;
};

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

void quick_sort_first(int arr[], int _i, int size_arr) {
	int mid = (size_arr + _i) / 2;
	int i = _i;
	int j = size_arr;
	while (i <= j) {
		while (arr[i] < arr[mid]) {
			i++;
		}
		while (arr[j] > arr[mid]) {
			j--;
		}
		if (i <= j) {
			int temp = arr[j];
			arr[j] = arr[i];
			arr[i] = temp;
			i++;
			j--;
		}
	}
	if (j > 0) {
		quick_sort_first(arr, 0, j);
	}
	if (i <= size_arr) {
		quick_sort_first(arr, i, size_arr);
	}
}

void simple_bucket_sort_with_dop_arr(int arr[], int size_arr) {
	int dop_arr[size_arr];
	int i;

	for (i = 0; i < size_arr; i++) {
		dop_arr[arr[i] - 1] = arr[i];
	}

	cout << "Результат: " << endl;
	for (i = 0; i < size_arr; i++) {
		arr[i] = dop_arr[i];
		cout << arr[i] << " ";
	}
	cout << endl;
}

void simple_bucket_sort_without_dop_arr(int arr[], int size_arr) {
	int temp;
	int diff_count = 0;
	int change_count = 0;
	for (int i = 0; i < size_arr; i++) {
		while (i + 1 != arr[i]) {
			diff_count++;
			change_count++;
			temp = arr[arr[i] - 1];
			arr[arr[i] - 1] = arr[i];
			arr[i] = temp;
		}
		diff_count++;
	}
	cout << "Результат: " << endl;
	for (int i = 0; i < size_arr; i++) {
		cout << arr[i] << " ";
	}
	cout << endl;
	cout << "Количество сравнений: " << diff_count << endl;
	cout << "Количество перестановок: " << change_count << endl;
}

void bucket_sort(int arr[], int size_arr, int bucket_size) {

	bucket_size++;
	Stack* bucket[bucket_size];
	Stack* element = nullptr;

	for (int i = 0; i < bucket_size; i++) {
		bucket[i] = nullptr;
	}

	for (int j = 0; j < size_arr; j++) {
		element = new Stack;
		element->num = arr[j];

		if (bucket[arr[j]] == nullptr) {
			bucket[arr[j]] = element;
		}
		else {
			element->next = bucket[arr[j]];
			bucket[arr[j]] = element;
		}
	}

	int s = 0;
	for (int i = 0; i < bucket_size; i++) {
		Stack* current = bucket[i];
		Stack* temp;
		while (current != nullptr) {
			temp = current;
			arr[s] = current->num;
			s++;
			current = current->next;
			delete temp;
		}
	}
	cout << "Результат:" << endl;
	for (int i = 0; i < size_arr; i++) {
		cout << arr[i] << " ";
	}
	cout << endl;

}

void radix_sort(int arr[], int size_arr) {
	int max_el = arr[0];
	for (int i = 0; i < size_arr; i++) {
		if (arr[i] > max_el) {
			max_el = arr[i];
		}
	}
	int max_digits = 0;
	while (max_el != 0) {
		max_digits++;
		max_el = max_el / 10;
	}

	int base = 1;
	int s, t;
	int i, j, index;
	Stack* redixs[10];
	for (i = 0; i < 10; i++) { redixs[i] = nullptr; };
	Stack* current;
	Stack* temp;
	Stack* element = nullptr;

	for (j = 0; j < max_digits; j++) {
		s = 0;
		for (i = 0; i < size_arr; i++) {
			index = (arr[i] / base) % 10;

			element = new Stack;
			element->num = arr[i];

			if (redixs[index] == nullptr) {
				element->size_num = 0;
				redixs[index] = element;
			}
			else {
				element->size_num = redixs[index]->size_num + 1;
				element->next = redixs[index];
				redixs[index] = element;
			}
		}
		for (i = 0; i < 10; i++) {
			current = redixs[i];
			t = 0;
			while (current != nullptr) {
				temp = current;
				index = s + current->size_num;
				arr[index] = current->num;
				current = current->next;
				t++;
				delete temp;
			}
			redixs[i] = nullptr;
			s += t;
		}
		base = base * 10;
	}
	cout << "Результат:" << endl;
	for (i = 0; i < size_arr; i++) {
		cout << arr[i] << " ";
	}
	cout << endl;
}

int main() {
	SetConsoleCP(1251);
	SetConsoleOutputCP(1251);
	srand(time(NULL));
	string inp = "";
	string mode = "";
	int random;
	int c = 5;
	bool arr_created = false;
	int size_arr = 0;
	int bucket_size = 0;
	int* arr;
	int* temp;
	while (true) {
		if (c == 5) {
			cout << "---------------------" << endl;
			cout << "Выберите команду:" << endl;
			cout << "1) Создать массив с случайными элементами" << endl << "2) Показать исходный массив" << endl << "3) Простейшая карманная сортировка" << endl << "4) Обобщенная карманная сортировка" << endl << "5) Разрядная сортировка" << endl << "6) Выход" << endl;
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
				random = rand() % 1000;
				arr[i] = random;
				temp[i] = random;
			}
			if (!arr_created) {
				arr_created = true;
			}
			cout << "Массив заполнен!" << endl;
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
			for (int i = 0; i < size_arr; i++) {
				temp[i] = -1;
			}
			for (int i = 0; i < size_arr; i++) {
				int index = rand() % size_arr;
				while (true) {
					if (temp[index] == -1) {
						temp[index] = i + 1;
						break;
					}
					index = (index + 1) % size_arr;
				}
			}
			cout << "Создаем другой список для этой сортировки:" << endl;
			for (int i = 0; i < size_arr; i++) {
				cout << temp[i] << " ";
			}
			cout << endl;
			cout << "Выберите модификатор:" << endl;
			cout << "1) Использовать дополнительный массив" << endl << "2) Не использовать дополнительный массив" << endl;
			while (true) {
				cout << "> ";
				getline(cin, mode);
				if (mode == "1") {
					simple_bucket_sort_with_dop_arr(temp, size_arr);
					break;
				}
				else if (mode == "2") {
					simple_bucket_sort_without_dop_arr(temp, size_arr);
					break;
				}
				else {
					cout << "Неизвестная команда" << endl;
				}
			}
			for (int i = 0; i < size_arr; i++) {
				temp[i] = arr[i];
			}
		}
		else if (inp == "4") {
			if (!arr_created) {
				cout << "Массив не создан!" << endl;
				continue;
			}
			cout << "Нужно создать новый массив для этой сортировки." << endl;
			cout << "Введите максимальный элемент для массива, оно должно быть больше 1 и меньше " << size_arr << endl;
			while (true) {
				cout << "> ";
				getline(cin, inp);
				if (is_good_number(inp)) {
					bucket_size = stoi(inp);
					if (bucket_size > 1 && bucket_size < size_arr) {
						break;
					}
				}
				cout << "Число не подходит условиям" << endl;
			}

			for (int i = 0; i < size_arr; i++) {
				random = rand() % (bucket_size + 1);
				temp[i] = random;
			}
			for (int i = 0; i < size_arr; i++) {
				cout << temp[i] << " ";
			}
			cout << endl;

			bucket_sort(temp, size_arr, bucket_size);
			for (int i = 0; i < size_arr; i++) {
				temp[i] = arr[i];
			}
		}
		else if (inp == "5") {
			if (!arr_created) {
				cout << "Массив не создан!" << endl;
				continue;
			}
			cout << "Сортируем..." << endl;
			radix_sort(temp, size_arr);
		}
		else if (inp == "6") {
			cout << "Выходим..." << endl;
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

