#include <string>
#include <iostream>
#include <time.h>
#include <windows.h>

using namespace std;
// ------------------------------
int const global_size = 10;
// ------------------------------
int count_hash = 0;

string hashTable[global_size];
string random_words[40] = {"Although", "Burking", "Kormilo", "Monolithic", "Oporos", "Relativistic", "Shine", "Stretching", "To-tout", "Veal",
						 "Dazzling", "Ebennoye", "Grandfather", "Little mermaid", "Nazem", "Rhymeplet", "Stencil", "Talented", "Two-shift",
						 "Vampire", "Acre", "Boyaryshnya", "Called", "Dusting", "Gaoler", "Lemma", "Needles", "Pigosatina", "Shipbuilder",
						 "Swaika", "Attachment", "Dating", "Decatade", "Deficit", "Gilaki", "Naboom", "Navoi", "Prevent", "Semites",
						 "Super-planned"};

bool hashEmpty() {
	return (count_hash == 0);
}

bool hashFull() {
	return (count_hash == global_size);
}

int hashFunction(string _value, int hashSize) {
	int sum = 0;
	for (int i = 0; i < _value.length(); i++) {
		sum += static_cast<int>(_value[i]);
	}
	return sum % hashSize;
}

void addElement(string _value) {
	int index = hashFunction(_value, global_size);
	int switch_count = 0;
	for (int i = 0; i <= global_size - 1; i++) {
		if (hashTable[index] == "") {
			hashTable[index] = _value;
			count_hash++;
			cout << "Ключ " << _value << " добавлен в индекс: " << index << endl;
			break;
		}
		else if (hashTable[index] == _value) {
			cout << "Ключ " << _value << " уже есть в хеш-таблице" << endl;
			return ;
		}
		index = ((index + 1) % global_size);
		switch_count++;
	}
	cout << "Было произведено " << switch_count << " сравнений ключа при добавлении элемента" << endl;
}

void removeElement(string _value) {
	int index = hashFunction(_value, global_size);
	int switch_count = 0;
	for (int i = 0; i <= global_size - 1; i++) {
		if (hashTable[index] == _value) {
			hashTable[index] = "";
			count_hash--;
			cout << "Ключ " << _value << " удалён из хеш-таблицы" << endl;
			break;
		}
		index = ((index + 1) % global_size);
		switch_count++;
	}
	cout << "Было произведено " << switch_count << " сравнений ключа при удалении элемента" << endl;
}

int findElement(string _value, int mode, int hashSize, string _hashTable[]) {
	int index = hashFunction(_value, hashSize);
	int switch_count = 0;
	for (int i = 0; i <= hashSize - 1; i++) {
		switch_count++;
		if (_hashTable[index] == "") {
			return -1;
		}
		else if (_hashTable[index] == _value) {
			if (mode) {
				cout << "Было произведено " << switch_count << " сравнений ключа при поиске элемента" << endl;
			}
			return index;
		}
		index = ((index + 1) % hashSize);
	}
}

void printHash() {
	for (int i = 0; i < global_size; i++) {
		if (hashTable[i] != "") {
			cout << i << ") " << hashTable[i] << endl;
		}
	}
}

int addElementsTest(string hashTableTest[], string testWords[], int hashSize, string randomWord) {
	int switch_count = 0;
	for (int j = 0; j < 10; j++) {
		int index = hashFunction(testWords[j], hashSize);
		for (int i = 0; i <= hashSize - 1; i++) {
			switch_count++;
			if (hashTableTest[index] == "") {
				hashTableTest[index] = testWords[j];
				break;
			}
			index = ((index + 1) % hashSize);
		}
	}
	findElement(randomWord, 1, hashSize, hashTableTest);
	for (int j = 0; j < hashSize; j++) {
		hashTableTest[j] = "";
	}
	return switch_count;
}

void testHash() {
	string hashTable11[11];
	string hashTable13[13];
	string hashTable17[17];
	string words[10];
	int random, switch_count;
	bool ctn;
	cout << "Набор из 10 случайных добавляемых слов:" << endl;
	for (int i = 0; i < 10; i++) {
		while (true) {
			ctn = false;
			random = rand() % 40;
			for (int j = 0; j < i+1; j++) {
				if (random_words[random] == words[j]) {
					ctn = true;
					break;
				}

			}
			if (!ctn) {
				break;
			}
		}
		words[i] = random_words[random];
		cout << random_words[random] << " | ";
	}
	cout << endl << "-----------------------" << endl;
	random = rand() % 10;
	cout << "Будем искать слово: " << words[random] << endl;
	cout << "-----------------------" << endl;
	cout << "Хеш-таблица с размером 11" << endl;
	switch_count = addElementsTest(hashTable11, words, 11, words[random]);
	cout << "Общее количество сравнений при добавлении: " << switch_count << endl;
	cout << "-----------------------" << endl;
	cout << "Хеш-таблица с размером 13" << endl;
	switch_count = addElementsTest(hashTable13, words, 13, words[random]);
	cout << "Общее количество сравнений при добавлении: " << switch_count << endl;
	cout << "-----------------------" << endl;
	cout << "Хеш-таблица с размером 17" << endl;
	switch_count = addElementsTest(hashTable17, words, 17, words[random]);
	cout << "Общее количество сравнений при добавлении: " << switch_count << endl;
}

int main() {
	SetConsoleCP(1251);
	SetConsoleOutputCP(1251);
	srand(time(NULL));
	string inp;
	int index;
	int c = 5;

	for (int i = 0; i < global_size; i++) {
		hashTable[i] = "";
	}

	while (true) {
		if (c == 5) {
			cout << "Выберите команду:" << endl;
			cout << "1) Добавить элемент" << endl << "2) Удалить элемент" << endl << "3) Вывести хеш-таблицу" << endl << "4) Найти индекс ключа" << endl << "5) Сделать тест с разными размерами хеш-таблиц" << endl << "6) Выход" << endl;
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
				if (inp != "") {
					break;
				}
				else {
					cout << "Получена пустая строка." << endl;
				}
			}
			addElement(inp);
		}
		else if (inp == "2") {
			if (hashEmpty()) {
				cout << "Хеш-таблица пуста" << endl;
				continue;
			}
			cout << "Введите ключ:" << endl;
			while (true) {
				cout << "> ";
				getline(cin, inp);
				if (findElement(inp, 0, global_size, hashTable) != -1) {
					break;
				}
				else {
					cout << "Такого ключа нет в хеш-таблице." << endl;
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
			cout << "Введите ключ:" << endl;
			cout << "> ";
			getline(cin, inp);
			int result = findElement(inp, 1, global_size, hashTable);
			if (result == -1) {
				cout << "Такого ключа нет в хеш-таблице" << endl;
			}
			else {
				cout << result << ") " << inp << endl;
			}
		}
		else if (inp == "5") {
			cout << "Делаем тест..." << endl;
			cout << "-----------------------" << endl;
			testHash();
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

