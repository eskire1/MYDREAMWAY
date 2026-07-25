#include <string>
#include <iostream>
#include <time.h>
#include <windows.h>

using namespace std;
// ------------------------------
int const global_size = 10;
// ------------------------------
int count_hash = 0;
int switch_count = 0;

struct Node {
	Node *next = nullptr;
	Node *back = nullptr;
	string value = "";
};

struct hashElement {
	Node* first = nullptr;
	Node* last = nullptr;
	int elCount = 0;
};

hashElement hashTable[global_size];

string random_words[50] = {"Although", "Burking", "Kormilo", "Monolithic", "Oporos", "Relativistic", "Shine", "Stretching", "To-tout", "Veal",
						 "Dazzling", "Ebennoye", "Grandfather", "Little mermaid", "Nazem", "Rhymeplet", "Stencil", "Talented", "Two-shift",
						 "Vampire", "Acre", "Boyaryshnya", "Called", "Dusting", "Gaoler", "Lemma", "Needles", "Pigosatina", "Shipbuilder",
						 "Swaika", "Attachment", "Dating", "Decatade", "Deficit", "Gilaki", "Naboom", "Navoi", "Prevent", "Semites",
						 "Super-planned", "Access", "Canalia", "Folk", "Forestless", "Mentoring", "Plug", "Retrial", "To shout", "Vanguard",
						 "Vertoprap"};

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
	Node* current_check = hashTable[index].first;
	while (current_check != nullptr) {
		if (current_check->value == _value) {
			cout << "Такой ключ уже есть в хеш-таблице" << endl;
			return ;
		}
		current_check = current_check->next;
	}
	switch_count = 0;
	Node* new_node = new Node();
	new_node->value = _value;
	hashTable[index].elCount++;

	if (hashTable[index].first == nullptr) {

		hashTable[index].first = new_node;
		hashTable[index].last = new_node;

		count_hash++;
		cout << "Ключ " << _value << " добавлен в индекс: " << index << endl;
	}
	else {
		Node* current = hashTable[index].last;
		current->next = new_node;
		new_node->back = current;
		hashTable[index].last = new_node;
		cout << "Ключ " << _value << " добавлен в конец списка находяшегося в индексе: " << index << endl;
		cout << "Количество сравнений: " << hashTable[index].elCount << endl;
	}
}

void removeElement(string _value) {
	int index = hashFunction(_value, global_size);
	int switch_count = 0;
	Node* current = hashTable[index].first;

	switch_count++;
	while (current->value != _value) {
		switch_count++;
		current = current->next;
	}

	if (hashTable[index].first == hashTable[index].last) {
		hashTable[index].first = nullptr;
		hashTable[index].last = nullptr;
		count_hash--;
	}

	else if (current == hashTable[index].first) {
		hashTable[index].first = current->next;
		(hashTable[index].first)->back = nullptr;

	}

	else if (current == hashTable[index].last) {
		hashTable[index].last = current->back;
		(hashTable[index].last)->next = nullptr;
	}

	else {
		Node* back_current = current->back;
		back_current->next = current->next;
	}
	hashTable[index].elCount--;
	cout << "Ключ " << _value << " удалён из хеш-таблицы" << endl;
	cout << "Было произведено " << switch_count << " сравнений по списку при удалении элемента" << endl;

	delete current;
}

int findElement(string _value, int mode, int _hashSize, hashElement _hashTable[]) {
	int index = hashFunction(_value, _hashSize);
	switch_count = 0;
	Node* current = _hashTable[index].first;
	switch_count++;
	while (current != nullptr) {
		if (current->value == _value) {
			break;
		}
		current = current->next;
		switch_count++;
	}
	if (current == nullptr) {
		return -1;
	}
	else {
		if (mode) {
			cout << "Ключ " << _value << " находится в списке #" << index << " под индексом " << switch_count - 1 << endl;
			cout << "Количество сравнений при поиске: " << switch_count << endl;
		}
		return index;
	}
}

void printHash() {
	for (int i = 0; i < global_size; i++) {
		if (hashTable[i].first != nullptr) {
			cout << i << ") ";
			Node* current = hashTable[i].first;
			while (current != nullptr) {
				cout << current->value << " | ";
				current = current->next;
			}
			cout << endl;
		}
	}
}

int addAndFindElementsTest(hashElement hashTableTest[], string testWords[], int hashSize, string randomWord) {
	switch_count = 0;
	int switch_count_add = 0;
	for (int j = 0; j < 20; j++) {
		int index = hashFunction(testWords[j], hashSize);
		Node* new_node = new Node();
		new_node->value = testWords[j];
		if (hashTableTest[index].first == nullptr) {
			hashTableTest[index].first = new_node;
			hashTableTest[index].last = new_node;
		}
		else {
			Node* current = hashTableTest[index].last;
			current->next = new_node;
			new_node->back = current;
			hashTableTest[index].last = new_node;
		}
		hashTableTest[index].elCount += 1;
		switch_count_add += hashTableTest[index].elCount;
	}
	findElement(randomWord, 0, hashSize, hashTableTest);
	for (int j = 0; j < hashSize; j++) {
		Node* current = hashTableTest[j].first;
		Node* temp;
		while (current != nullptr) {
			temp = current;
			current = current->next;
			delete temp;
		}
		hashTableTest[j].first = nullptr;
		hashTableTest[j].last = nullptr;
	}
	return switch_count_add;
}

void testHash() {
	hashElement hashTable9[9];
	hashElement hashTable17[17];
	hashElement hashTable23[23];

	string words[20];
	int random, switch_count_test;
	bool ctn;
	cout << "Набор из 20 случайных добавляемых слов:" << endl;
	for (int i = 0; i < 20; i++) {
		while (true) {
			ctn = false;
			random = rand() % 50;
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
		if (i == 9) { cout << endl; }
	}
	cout << endl << "-----------------------" << endl;
	random = rand() % 20;
	cout << "Будем искать слово: " << words[random] << endl;
	cout << "-----------------------" << endl;
	cout << "Хеш-таблица с размером 9" << endl;
	switch_count_test = addAndFindElementsTest(hashTable9, words, 9, words[random]);
	cout << "Общее количество сравнений при добавлении: " << switch_count_test << endl;
	cout << "Количество сравнений при поиске: " << switch_count << endl;
	cout << "-----------------------" << endl;
	cout << "Хеш-таблица с размером 17" << endl;
	switch_count_test = addAndFindElementsTest(hashTable17, words, 17, words[random]);
	cout << "Общее количество сравнений при добавлении: " << switch_count_test << endl;
	cout << "Количество сравнений при поиске: " << switch_count << endl;
	cout << "-----------------------" << endl;
	cout << "Хеш-таблица с размером 23" << endl;
	switch_count_test = addAndFindElementsTest(hashTable23, words, 23, words[random]);
	cout << "Общее количество сравнений при добавлении: " << switch_count_test << endl;
	cout << "Количество сравнений при поиске: " << switch_count << endl;
}

void clearHash() {
	for (int j = 0; j < global_size; j++) {
		Node* current = hashTable[j].first;
		Node* temp;
		while (current != nullptr) {
			temp = current;
			current = current->next;
			delete temp;
		}
		hashTable[j].first = nullptr;
		hashTable[j].last = nullptr;
	}
}

int main() {
	SetConsoleCP(1251);
	SetConsoleOutputCP(1251);
	srand(time(NULL));
	string inp;
	int index;
	int c = 5;

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
		}
		else if (inp == "5") {
			cout << "Делаем тест..." << endl;
			cout << "-----------------------" << endl;
			testHash();
		}
		else if (inp == "6") {
			cout << "Выходим..." << endl;
			clearHash();
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


