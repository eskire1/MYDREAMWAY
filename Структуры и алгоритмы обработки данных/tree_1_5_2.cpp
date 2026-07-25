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
	bool print_checked = false;
};

struct stack {
	stack* next;
	node* tree_node;
	int tree_level;
};

stack* first;
node* root;
int num;

bool stack_is_empty() {
	return (first == nullptr);
}

void add_element(node* _tree_node, int level) {
	stack* new_element = new stack;
	new_element->tree_node = _tree_node;
	new_element->tree_level = level;
	new_element->next = first;
	first = new_element;
}

void pop_element() {
	stack* current = first;
	first = first->next;
	current->next = nullptr;
	delete current;
}

node* create_tree(int cnt, node* &leaf) {
	if (cnt == 0) {
		return nullptr;
	}
	int left = cnt / 2;
	int right = cnt - left - 1;
	leaf = new node();
	leaf->value = 0 + rand() % 100;

	leaf->left = create_tree(left, leaf->left);
	leaf->right = create_tree(right, leaf->right);

	return leaf;
}

void print_symmetric_way(int level) {
	node* current_node = root;
	stack* current_element;
	int current_level;
	add_element(current_node, level);

	while (!stack_is_empty()) {
		current_element = first;
		current_node = current_element->tree_node;
		current_level = current_element->tree_level;
		if (current_node->left != nullptr) {
			if (!(current_node->left)->print_checked) {
				add_element(current_node->left, current_level+1);
				continue;
			}
		}
		pop_element();
		for (int i = 0; i < current_level * 4; i++) {
			cout << " ";
		}
		cout << current_node->value << endl;
		current_node->print_checked = true;

		if (current_node->right != nullptr) {
			add_element(current_node->right, current_level+1);
		}
	}
}

void print_symmetric_way_1(int level, node* leaf) {
	if (leaf == nullptr) {
		return ;
	}
	node* current = leaf;
	leaf->print_checked = false;
	level += 1;
	print_symmetric_way_1(level, current->left);
	for (int i = 0; i < (level-1) * 4; i++) {
		cout << " ";
	}
	cout << current->value << endl;
	print_symmetric_way_1(level, current->right);
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

	while (true) {
		cout << "Введите количество вершин:" << endl;
		cout << "> ";
		getline(cin, inp);
		if (inp == "0") {
			cout << "Нееее, так не интересно :( Нужно количество вершин больше 0" << endl;
		}
		else if (is_good_number(inp)) {
			break;
		}
		else {
			cout << "Что странное..." << endl;
		}
	}

	num = stoi(inp);
	cout << "Генерируем дерево..." << endl;
	root = create_tree(num, root);
	cout << "Готово." << endl;
	cout << "-------------" << endl;
	cout << "Вывод в симметричном порядке:" << endl;
	cout << "-------------" << endl;
	cout << "Цикл:" << endl;
	cout << "-------------" << endl;
	print_symmetric_way(0);
	cout << "-------------" << endl;
	cout << "Рекурсия:" << endl;
	cout << "-------------" << endl;
	print_symmetric_way_1(0, root);
	cout << "-------------" << endl;
	clear_tree(root);
	return 0;
}
