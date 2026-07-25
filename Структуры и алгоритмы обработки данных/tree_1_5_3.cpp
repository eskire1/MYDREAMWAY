#include <iostream>
#include <string>
#include <windows.h>
#include <time.h>
#include <cmath>

using namespace std;

bool is_good_number(string number) {
	bool flag = true;
	for (int i = 0; i < number.length(); i++) {
		if (!isdigit(number[i])) {
			flag = false;
			break;
		}
	}
	if (flag && number.length() > 0) {
		return true;
	}
	else {
		return false;
	}
}

struct node {
	int value;
	node* left;
	node* right;
};

node* root;
int num;

bool tree_is_empty() {
	return (root == nullptr);
}

node* find_element(int _value, node* leaf) {
	if (leaf == nullptr) {
		return leaf;
	}
	if (leaf->value == _value) {
		return leaf;
	}

	node* left = find_element(_value, leaf->left);
	if (left != nullptr) {
		return left;
	}
	node* right = find_element(_value, leaf->right);
	if (right != nullptr) {
		return right;
	}
	return nullptr;
 }

void add_leaf(int _value, node* target) {
	string inp = "";
	if (tree_is_empty()) {
		cout << "Дерево пустое, поэтому добавим корень." << endl;
		node* new_element = new node; new_element->left = nullptr; new_element->right = nullptr; new_element->value = _value;
		root = new_element;
		return ;
	}
	if (target->left == nullptr && target->right != nullptr) {
		cout << "У этой вершины свободен левый потомок, поэтому добавим элемент туда." << endl;
		node* new_element = new node; new_element->left = nullptr; new_element->right = nullptr; new_element->value = _value;
		target->left = new_element;
	}
	else if (target->left != nullptr && target->right == nullptr) {
		cout << "У этой вершины свободен правый потомок, поэтому добавим элемент туда." << endl;
		node* new_element = new node; new_element->left = nullptr; new_element->right = nullptr; new_element->value = _value;
		target->right = new_element;
	}
	else {
		cout << "Выберите, куда нужно добавить элемент:" << endl;
		cout << "1) В правого потомка." << endl;
		cout << "2) В левого потомка." << endl;
		while (true) {
			cout << "> ";
			getline(cin, inp);
			if (inp == "1") {
				node* new_element = new node; new_element->left = nullptr; new_element->right = nullptr; new_element->value = _value;
				target->right = new_element;
				break;
			}
			else if (inp == "2") {
				node* new_element = new node; new_element->left = nullptr; new_element->right = nullptr; new_element->value = _value;
				target->left = new_element;
				break;
			}
			else {
				cout << "Что-то не то" << endl;
			}
		}
	}
}

void print_reverse_symmetric_way(int level, node* leaf) {
	if (leaf == nullptr) {
		return ;
	}
	node* current = leaf;
	level += 1;
	print_reverse_symmetric_way(level, current->right);
	for (int i = 0; i < (level-1) * 4; i++) {
		cout << " ";
	}
	cout << current->value << endl;
	print_reverse_symmetric_way(level, current->left);
}

void clear_tree(node* &leaf) {
	if (leaf == nullptr) {
		return ;
	}
	node* current = leaf;
	clear_tree(current->left);
	current->left = nullptr;
	clear_tree(current->right);
	current->right = nullptr;
	delete current;
}

int main() {
	SetConsoleCP(1251);
	SetConsoleOutputCP(1251);
	srand(time(NULL));
	string inp = "";
	string target = "";
	int c = 5;
	node* target_node;

	while (true) {
		if (c == 5) {
			cout << "---------------------" << endl;
			cout << "Выберите команду:" << endl;
			cout << "1) Добавить элемент в качестве потомка заданной вершины" << endl << "2) Показать дерево" << endl << "3) Поиск элемента" << endl << "4) Очистить дерево" << endl << "5) Выход" << endl;
			c = 0;
		}
		cout << "Команда:" << endl;
		cout << "> ";
		getline(cin, inp);
		if (inp == "1") {
			cout << "Введите значение числа для элемента:" << endl;
			while (true) {
				cout << "> ";
				getline(cin, inp);
				if (is_good_number(inp)) {
					break;
				}
				else {
					cout << "Что-то не то." << endl;
				}
			}
			cout << "--------------------" << endl;
			if (tree_is_empty()) {
				add_leaf(stoi(inp), nullptr);
				continue;
			}
			cout << "После какой вершины добавить элемент:" << endl;
			while (true) {
				cout << "> ";
				getline(cin, target);
				if (!is_good_number(target)) {
					cout << "Что-то не то" << endl;
					continue;
				}
				target_node = find_element(stoi(target), root);
				if (target_node == nullptr) {
					cout << "Элемент не найден." << endl;
				}
				else {
					cout << "Элемент найден." << endl;
					if (target_node->left != nullptr && target_node->right != nullptr) {
						cout << "У этой вершины уже есть два потомка, нельзя добавить элемент." << endl;
						continue;
					}
					break;
				}
			}
			add_leaf(stoi(inp), target_node);
		}
		else if (inp == "2") {
			if (tree_is_empty()) {
				cout << "Дерево пусто." << endl;
				continue;
			}
			cout << "-------" << endl;
			print_reverse_symmetric_way(0, root);
			cout << "-------" << endl;
		}
		else if (inp == "3") {
			if (tree_is_empty()) {
				cout << "Дерево пусто" << endl;
				continue;
			}
			cout << "Введите значение вершины, которую нужно найти:" << endl;
			while (true) {
				cout << "> ";
				getline(cin, target);
				if (is_good_number(target)) {
					break;
				}
				else {
					cout << "Что-то не то" << endl;
				}
			}
			target_node = find_element(stoi(target), root);
			if (target_node == nullptr) {
				cout << "Элемент не найден." << endl;
			}
			else {
				cout << "Элемент найден." << endl;
				cout << "Его правый потомок: ";
				if (target_node->right != nullptr) {
					cout << (target_node->right)->value << endl;
				}
				else {
					cout << "ПУСТО" << endl;
				}
				cout << "Его левый потомок: ";
				if (target_node->left != nullptr) {
					cout << (target_node->left)->value << endl;
				}
				else {
					cout << "ПУСТО" << endl;
				}

			}
		}
		else if (inp == "4") {
			if (tree_is_empty()) {
				cout << "Дерево пусто." << endl;
				continue;
			}
			cout << "Очищаем..." << endl;
			clear_tree(root);
			root = nullptr;
		}
		else if (inp == "5") {
			cout << "Выходим." << endl;
			if (!tree_is_empty()) {
				clear_tree(root);
				root = nullptr;
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

