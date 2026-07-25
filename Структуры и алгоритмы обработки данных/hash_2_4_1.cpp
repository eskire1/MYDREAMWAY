#include <string>
#include <iostream>
#include <time.h>
#include <windows.h>

using namespace std;

int const global_size = 10;
int count_hash = 0;

string words[global_size] = {"begin", "type", "function", "procedure", "then", "case", "repeat", "while", "do", "exit"};
string hashTable[global_size];

bool hashEmpty() {
	return (count_hash == 0);
}

bool hashFull() {
	return (count_hash == global_size);
}

int hashFunction(string _value) {
	int sum = 0;
	for (int i = 0; i < _value.length(); i++) {
		sum += static_cast<int>(_value[i]);
	}
	return sum % 10;
}

void addElement(string _value) {
	cout << "Хеш-значение исходного текстового ключа: " << hashFunction(_value) << endl;
	while (true) {
		int index = hashFunction(_value);
		if (hashTable[index] == "") {
			hashTable[index] = _value;
			count_hash++;
			cout << "Текстовый ключ " << _value << " добавлен в индекс: " << index << endl;
			break;
		}
		else {
			cout << "Произошёл конфликт текстовых ключей с " << hashTable[index] << " , меняем исходный текстовый ключ:" << endl;
			_value = _value + ")";
			cout << "> " << _value << endl;
			cout << "-----" << endl;
		}
	}
}

void removeElement(string _value) {
	int index = hashFunction(_value);
	cout << "Удаляем с хеш-таблицы текстовый ключ " << hashTable[index] << " с индексом " << index << endl;
	hashTable[index] = "";
	count_hash--;
}

int findElement(string _value) {
	int index = hashFunction(_value);
	if (hashTable[index] == _value) {
		return index;
	}
	else {
		return -1;
	}
}

void printHash() {
	for (int i = 0; i < global_size; i++) {
		if (hashTable[i] != "") {
			cout << i << ") " << hashTable[i] << endl;
		}
	}
}

bool checkKey(string _value) {
	for (int i = 0; i < global_size; i++) {
		if (words[i] == _value) {
			return true;
		}
	}
	return false;
}

int main() {
	SetConsoleCP(1251);
	SetConsoleOutputCP(1251);
	string inp;
	int index;
	int c = 5;

	for (int i = 0; i < global_size; i++) {
		hashTable[i] = "";
	}

	while (true) {
		if (c == 5) {
			cout << "Список доступных текстовых ключей:" << endl;
			for (int i = 0; i < global_size; i++) {
				cout << words[i] << " | ";
			}
			cout << endl;
			cout << "---------------------" << endl;
			cout << "Выберите команду:" << endl;
			cout << "1) Добавить элемент" << endl << "2) Удалить элемент" << endl << "3) Вывести хеш-таблицу" << endl << "4) Найти индекс ключа" << endl << "5) Выход" << endl;
			c = 0;
		}
		cout << "Команда:" << endl;
		cout << "> ";
		getline(cin, inp);
		if (inp == "1") {
			if (hashFull()) {
				cout << "Хеш-таблица заполнена" << endl;
				continue;
			}
			cout << "Введите ключ:" << endl;
			while (true) {
				cout << "> ";
				getline(cin, inp);
				if (checkKey(inp)) {
					break;
				}
				else {
					cout << "Такого ключа нет в списке доступных." << endl;
				}
			}
			addElement(inp);
		}
		else if (inp == "2") {
			if (hashEmpty()) {
				cout << "Хеш-таблица пуста" << endl;
				continue;
			}
			cout << "Введите текстовый ключ:" << endl;
			while (true) {
				cout << "> ";
				getline(cin, inp);
				if (findElement(inp) != -1) {
					break;
				}
				else {
					cout << "Такого текстового ключа нет в хеш-таблице." << endl;
				}
			}
			removeElement(inp);
		}
		else if (inp == "3") {
			if (hashEmpty()) {
				cout << "Хеш-таблица пуста" << endl;
				continue;
			}
			printHash();
		}
		else if (inp == "4") {
			if (hashEmpty()) {
				cout << "Хеш-таблица пуста" << endl;
				continue;
			}
			cout << "Введите текстовый ключ:" << endl;
			cout << "> ";
			getline(cin, inp);
			int result = findElement(inp);
			if (result == -1) {
				cout << "Такого текстового ключа нет в хеш-таблице" << endl;
			}
			else {
				cout << result << ") " << inp << endl;
			}
		}
		else if (inp == "5") {
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
