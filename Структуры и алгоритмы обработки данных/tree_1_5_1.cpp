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

node* create_tree(int cnt, node* &leaf) {
	if (cnt == 0) {
		return nullptr;
	}
	int left = cnt / 2;
	int right = cnt - left - 1;
	leaf = new node();
	leaf->value = 0 + rand() % 100;
	leaf->left = nullptr;
	leaf->right = nullptr;

	leaf->left = create_tree(left, leaf->left);
	leaf->right = create_tree(right, leaf->right);

	return leaf;
}

void print_straight_way(int level, node* leaf) {
	if (leaf == nullptr) {
		return ;
	}
	node* current = leaf;
	for (int i = 0; i < level * 4; i++) {
		cout << " ";
	}
	cout << current->value << endl;
	level += 1;
	print_straight_way(level, current->left);
	print_straight_way(level, current->right);
}

void print_symmetric_way(int level, node* leaf) {
	if (leaf == nullptr) {
		return ;
	}
	node* current = leaf;
	level += 1;
	print_symmetric_way(level, current->left);
	for (int i = 0; i < (level-1) * 4; i++) {
		cout << " ";
	}
	cout << current->value << endl;
	print_symmetric_way(level, current->right);
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
	cout << "Вывод в прямом порядке:" << endl;
	cout << "-------------" << endl;
	print_straight_way(0, root);
	cout << "-------------" << endl;
	cout << "Вывод в симметричном порядке:" << endl;
	cout << "-------------" << endl;
	print_symmetric_way(0, root);
	cout << "-------------" << endl;
	cout << "Вывод в обратно-симметричном порядке:" << endl;
	cout << "-------------" << endl;
	print_reverse_symmetric_way(0, root);
	cout << "-------------" << endl;
	clear_tree(root);
	return 0;
}
