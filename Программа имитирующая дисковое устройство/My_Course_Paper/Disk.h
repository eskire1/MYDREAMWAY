#include "Folder.h"
#include <fstream>
#include <string>

class Disk {
private:
	string diskName;
	Folder* head;
	int folderCount;
public:
	Disk() {
		diskName = "";
		head = new Folder();
		head->setNextFolder(head);
		folderCount = 0;
	}
	Disk(string _diskName) {
		diskName = _diskName;
		head = new Folder();
		head->setNextFolder(head);
		folderCount = 0;
	}
	~Disk() {
		if (!isDiskEmpty()) {
			clearFolders();
		}
		delete head;
	}

	string getDiskName() { return diskName; }
	void setDiskName(string _diskName) { diskName = _diskName; }
	bool isDiskEmpty() { return folderCount == 0; }

	void AddFolder(string _folderName) {
		Folder* newFolder = new Folder(_folderName);

		Folder* current = head->getNextFolder();
		Folder* previous = head;

		while (current->getFolderName().compare(_folderName) == -1 && current != head) {
			previous = current;
			current = current->getNextFolder();
		}

		previous->setNextFolder(newFolder);
		newFolder->setNextFolder(current);
		folderCount++;
	}

	Folder* findFolder(string _folderName, int& i) {
		i = 1;
		Folder* current = head->getNextFolder();

		while (current != head) {
			if (current->getFolderName() == _folderName) {
				return current;
			}
			current = current->getNextFolder(); i++;
		}
		return nullptr;
	}

	void removeFolder() {
		cout << "§£§Ó§Ö§Õ§Ú§ä§Ö §Ú§Þ§ñ §á§Ñ§á§Ü§Ú: "; string _folderName; cin >> _folderName;
		Folder* target = head->getNextFolder();
		Folder* previous = head;

		while (target != head) {
			if (target->getFolderName() == _folderName) {
				break;
			}
			previous = target;
			target = target->getNextFolder();
		}

		if (target == head) {
			cout << "§±§Ñ§á§Ü§Ñ §ß§Ö §ß§Ñ§Û§Õ§Ö§ß§Ñ." << endl;
			return;
		}

		previous->setNextFolder(target->getNextFolder());

		delete target; folderCount--;
	}

	void printDisk() {
		int i = 1;

		Folder* current = head->getNextFolder();
		if (current == head) {
			cout << "§¥§Ú§ã§Ü §á§å§ã§ä." << endl;
			return;
		}

		while (current != head) {
			cout << "--- " << i << ") " << current->getFolderName() << endl;
			current = current->getNextFolder();
			i++;
		}
	}

	void findFromAll() {
		if (isDiskEmpty()) { cout << "§¥§Ú§ã§Ü §á§å§ã§ä." << endl; return; }
		cout << "§£§Ó§Ö§Õ§Ú§ä§Ö §ß§Ñ§Ù§Ó§Ñ§ß§Ú§Ö §æ§Ñ§Û§Ý§Ñ, §Ü§à§ä§à§â§í§Û §ç§à§ä§Ú§ä§Ö §ß§Ñ§Û§ä§Ú: "; string _fileName; cin >> _fileName;
		Folder* temp = head->getNextFolder();
		while (temp != head) {
			File* temp_arr = temp->getFilesArray();
			for (int i = 0; i < temp->getFileCount(); i++) {
				if (temp_arr->getFileName() == _fileName) {
					cout << "§¶§Ñ§Û§Ý §ß§Ñ§Û§Õ§Ö§ß §Ó §á§Ñ§á§Ü§Ö \"" << temp->getFolderName() << "\" " << ++i << "-§í§Þ §Ó §à§é§Ö§â§Ö§Õ§Ú." << endl;
					temp_arr = nullptr; temp = nullptr;
					return;
				}
				temp_arr++;
			}
			temp_arr = nullptr;
			temp = temp->getNextFolder();
		}
		cout << "§¶§Ñ§Û§Ý §ß§Ñ §Õ§Ú§ã§Ü§Ö §ß§Ö §ß§Ñ§Û§Õ§Ö§ß." << endl;
		temp = nullptr;
	}
	void clearFolders() {
		Folder* current = head->getNextFolder();
		Folder* temp;
		while (current != head) {
			temp = current;
			current = current->getNextFolder();

			delete temp;
		}
		head->setNextFolder(head);
	}
	void saveToFile(string _file) {
		ofstream out(_file);
		out << "*** " << diskName << " ***" << endl;
		if (head->getNextFolder() != head) {
			Folder* temp = head->getNextFolder();
			while (temp != head) {
				out << "--- " << temp->getFolderName() << endl;
				if (temp->isFolderEmpty()) { out << "(NULL)" << endl; temp = temp->getNextFolder(); }
				else {
					File* temp_arr = temp->getFilesArray();
					for (int i = 0; i < temp->getFileCount(); i++) {
						out << temp_arr->getFileName() << " (" << temp_arr->getSize() << " KB)" << endl;
						temp_arr++;
					}
					temp = temp->getNextFolder();
				}
			}
			temp = nullptr;
		}
		out.close();
	}
	
	int readFromFile(int res, string out_file, Disk*& mainDisk) {
		if (mainDisk != nullptr && !(mainDisk->isDiskEmpty()) && res == 0) {
			cout << "§¯§Ö §Ø§Ö§Ý§Ñ§Ö§ä§Ö §á§Ö§â§Ö§Õ §ï§ä§Ú§Þ §ã§à§ç§â§Ñ§ß§Ú§ä§î §Õ§Ñ§ß§ß§í§Ö?" << endl
				<< "(§¦§ã§Ý§Ú §ã§à§ç§â§Ñ§ß§Ö§ß§Ú§Ö §Õ§Ñ§ß§ß§í§ç §å§Ø§Ö §á§â§à§Ú§ã§ç§à§Õ§Ú§Ý§à, §à§á§Ö§â§Ñ§è§Ú§ñ §ß§Ö§à§Ò§ñ§Ù§Ñ§ä§Ö§Ý§î§ß§Ñ)" << endl
				<< "§¥§Ñ/§¯§Ö§ä: "; string answer; cin >> answer;
			if (answer == "§¥§Ñ" || answer == "§Õ§Ñ") { 
				cout << "§£§Ó§Ö§Õ§Ú§ä§Ö §Ú§Þ§ñ §æ§Ñ§Û§Ý§Ñ, §Ó §Ü§à§ä§à§â§í§Û §ç§à§ä§Ú§ä§Ö §ã§à§ç§â§Ñ§ß§Ú§ä§î §Õ§Ñ§ß§ß§í§Ö §Õ§Ú§ã§Ü§Ñ: "; string _file; cin >> _file; 
				saveToFile(_file); mainDisk->clearFolders(); 
			}
			else if (answer == "§¯§Ö§ä" || answer == "§ß§Ö§ä") { saveToFile("save_temp.txt"); mainDisk->clearFolders(); }
			else { cout << "§£§Ó§Ö§Õ§×§ß §ß§Ö§Ó§Ö§â§ß§í§Û §à§ä§Ó§Ö§ä." << endl; return 1; }
			
			cout << "-------------------" << endl
				<< "§¶§à§â§Þ§Ñ§ä §é§ä§Ö§ß§Ú§ñ §Õ§à§Ý§Ø§Ö§ß §Ò§í§ä§î §ä§Ñ§Ü§Ú§Þ:" << endl
				<< "1) *** §Ú§Þ§ñ §Õ§Ú§ã§Ü§Ñ ***" << endl
				<< "2) ---§Ú§Þ§ñ §á§Ñ§á§Ü§Ú" << endl
				<< "3) <§Ú§Þ§ñ §á§Ñ§á§Ü§Ú> (<§â§Ñ§Ù§Þ§Ö§â> KB)" << endl
				<< "-------------------" << endl;
		}
		else if (res == 1) { cout << "§£§í§á§à§Ý§ß§ñ§Ö§ä§ã§ñ §Ó§à§ã§ã§ä§Ñ§ß§à§Ó§Ý§Ö§ß§Ú§Ö..." << endl; }

		ifstream in(out_file);
		if (!in) {
			cerr << "§¯§Ö §å§Õ§Ñ§Ý§à§ã§î §à§ä§Ü§â§í§ä§î §æ§Ñ§Û§Ý input.txt" << std::endl;
			return 1;
		}

		string input_line = "";
		string disk_name = "";
		string folder_name = "";
		bool folder_empty = false;

		while (getline(in, input_line)) {
			// §µ§Õ§Ñ§Ý§ñ§Ö§Þ §Ý§Ú§ê§ß§Ú§Ö §á§â§à§Ò§Ö§Ý§í §Ó §ß§Ñ§é§Ñ§Ý§Ö §Ú §Ü§à§ß§è§Ö §ã§ä§â§à§Ü§Ú
			input_line.erase(0, input_line.find_first_not_of(" \t\n\r\f\v"));
			input_line.erase(input_line.find_last_not_of(" \t\n\r\f\v") + 1);

			if (input_line.substr(0, 3) == "***") {
				// §ª§Þ§ñ §Õ§Ú§ã§Ü§Ñ
				disk_name = input_line.substr(4, input_line.size() - 8);
				mainDisk->setDiskName(disk_name);
			}
			else if (input_line.substr(0, 3) == "---") {
				// §ª§Þ§ñ §á§Ñ§á§Ü§Ú
				folder_name = input_line.substr(4);
				//cout << "  §±§Ñ§á§Ü§Ñ: " << folder_name << endl;
				mainDisk->AddFolder(folder_name);
				folder_empty = false;
			}
			else if (input_line == "(NULL)") {
				// §±§å§ã§ä§Ñ§ñ §á§Ñ§á§Ü§Ñ
				folder_empty = true;
			}
			else if (!input_line.empty()) {
				// §ª§Þ§ñ §æ§Ñ§Û§Ý§Ñ §Ú §Ö§Ô§à §â§Ñ§Ù§Þ§Ö§â
				size_t pos = input_line.find('(');
				if (pos != string::npos) {
					string file_name = input_line.substr(0, pos - 1);
					string size_str = input_line.substr(pos + 1, input_line.size() - pos - 5); // §å§Õ§Ñ§Ý§ñ§Ö§Þ ' KB)'
					int file_size = stoi(size_str);
					if (!folder_empty) {
						int i; Folder* temp = mainDisk->findFolder(folder_name, i); temp->AddFileFrom(file_name, file_size);
					}
					else {
						cerr << "§°§ê§Ú§Ò§Ü§Ñ: §±§Ñ§á§Ü§Ñ §Ò§í§Ý§Ñ §à§ä§Þ§Ö§é§Ö§ß§Ñ §Ü§Ñ§Ü §á§å§ã§ä§Ñ§ñ, §ß§à §ã§à§Õ§Ö§â§Ø§Ú§ä §æ§Ñ§Û§Ý§í." << endl;
						return 1;
					}
				}
				else {
					cerr << "§°§ê§Ú§Ò§Ü§Ñ: §¯§Ö§Ó§Ö§â§ß§í§Û §æ§à§â§Þ§Ñ§ä §ã§ä§â§à§Ü§Ú §æ§Ñ§Û§Ý§Ñ." << endl;
					return 1;
				}
			}
		}

		cout << "§µ§ã§á§Ö§ê§ß§à." << endl;
	}
};
