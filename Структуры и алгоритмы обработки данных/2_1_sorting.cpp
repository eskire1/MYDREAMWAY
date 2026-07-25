#include <iostream>
#include <string>
#include <windows.h>
#include <time.h>

using namespace std;

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

void bubble_sort(int arr[], int size_arr) {
	int temp;
	int change_count = 0;
	int diff_count = 0;
	for (int i = 0; i < size_arr; i++) {
		for (int j = 1; j < (size_arr - i); j++) {
			diff_count++;
			if (arr[j-1] > arr[j]) {
				change_count++;
				temp = arr[j];
				arr[j] = arr[j-1];
				arr[j-1] = temp;
			}
		}
	}
	cout << "Результат сортировки пузырьком:" << endl;
	for (int i = 0; i < size_arr; i++) {
		cout << arr[i] << " ";
	}
	cout << endl;
	cout << "Было совершено " << change_count << " перестановок во время сортировки." << endl;
	cout << "Было совершено " << diff_count << " сравнений во время сортировки." << endl;
}

void sort_choice(int arr[], int size_arr) {
	int temp;
	int change_count = 0;
	int diff_count = 0;
	for (int i = 0; i < (size_arr - 1); i++) {
		int min_index = i;
		for (int j = i + 1; j < size_arr; j++) {
			diff_count++;
			if (arr[j] < arr[min_index]) {
				min_index = j;
			}
		}
		if (i != min_index) {
			change_count++;
			temp = arr[i];
			arr[i] = arr[min_index];
			arr[min_index] = temp;
		}
	}
	cout << "Результат сортировки выбором:" << endl;
	for (int i = 0; i < size_arr; i++) {
		cout << arr[i] << " ";
	}
	cout << endl;
	cout << "Было совершено " << change_count << " перестановок во время сортировки." << endl;
	cout << "Было совершено " << diff_count << " сравнений во время сортировки." << endl;
}

void sort_insert(int arr[], int size_arr) {
	int j;
	int insert_el;
	int change_count = 0;
	int diff_count = 0;
	for (int i = 1; i < size_arr; i++) {
		int j = i;
		change_count++;
		insert_el = arr[i];
		while (j > 0) {
			diff_count++;
			if (arr[j-1] <= insert_el) {
				change_count++;
				arr[j] = insert_el;
				break;
			}
			change_count++;
			arr[j] = arr[j-1];
			j--;
		}
		if (j == 0) {
			change_count++;
			arr[j] = insert_el;
		}
	}
	cout << "Результат сортировки вставкой:" << endl;
	for (int i = 0; i < size_arr; i++) {
		cout << arr[i] << " ";
	}
	cout << endl;
	cout << "Было совершено " << change_count / 3 << " перестановок во время сортировки." << endl;
	cout << "Было совершено " << diff_count << " сравнений во время сортировки." << endl;
}


int main() {
	SetConsoleCP(1251);
	SetConsoleOutputCP(1251);
	srand(time(NULL));
	string inp = "";
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
			cout << "1) Создать массив с случайными элементами" << endl << "2) Показать исходный массив" << endl << "3) Сортировка пузырьком" << endl << "4) Сортировка выбором" << endl << "5) Сортировка вставкой" << endl << "6) Выход" << endl;
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
			bubble_sort(temp, size_arr);
			for (int i = 0; i < size_arr; i++) {
				temp[i] = arr[i];
			}
		}
		else if (inp == "4") {
			if (!arr_created) {
				cout << "Массив не создан!" << endl;
				continue;
			}
			sort_choice(temp, size_arr);
			for (int i = 0; i < size_arr; i++) {
				temp[i] = arr[i];
			}
		}
		else if (inp == "5") {
			if (!arr_created) {
				cout << "Массив не создан!" << endl;
				continue;
			}
			sort_insert(temp, size_arr);
			for (int i = 0; i < size_arr; i++) {
				temp[i] = arr[i];
			}
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
