#include "Disk.h"

Disk* mainDisk = nullptr;

void ShowMenu() {
	cout << "-----------------------------" << endl
		<< "m - §Ó§í§Ó§à§Õ §Þ§Ö§ß§ð." << endl
		<< "newdisk - §ã§à§Ù§Õ§Ñ§ß§Ú§Ö §ß§à§Ó§à§Ô§à §Õ§Ú§ã§Ü§Ñ." << endl
		<< "mdir - §ã§à§Ù§Õ§Ñ§ß§Ú§Ö §á§Ñ§á§Ü§Ú §ß§Ñ §Õ§Ú§ã§Ü§Ö." << endl
		<< "mfile - §ã§à§Ù§Õ§Ñ§ß§Ú§Ö §ß§à§Ó§à§Ô§à §æ§Ñ§Û§Ý§Ñ §Ó §á§Ñ§á§Ü§Ö." << endl
		<< "findd - §á§à§Ú§ã§Ü §á§Ñ§á§Ü§Ú §ß§Ñ §Õ§Ú§ã§Ü§Ö." << endl
		<< "findf - §á§à§Ú§ã§Ü §æ§Ñ§Û§Ý§Ñ §ß§Ñ §Õ§Ú§ã§Ü§Ö." << endl
		<< "show - §Ó§í§Ó§à§Õ §Õ§Ñ§ß§ß§í§ç §Õ§Ú§ã§Ü§Ñ." << endl
		<< "showdir - §Ó§í§Ó§à§Õ §Õ§Ñ§ß§ß§í§ç §á§Ñ§á§Ü§Ú." << endl
		<< "rmdir - §å§Õ§Ñ§Ý§Ö§ß§Ú§Ö §á§Ñ§á§Ü§Ú §ß§Ñ §Õ§Ú§ã§Ü§Ö." << endl
		<< "rm - §å§Õ§Ñ§Ý§Ö§ß§Ú§Ö §æ§Ñ§Û§Ý§Ñ §Ú§Ù §á§Ñ§á§Ü§Ú." << endl
		<< "clear - §à§é§Ú§ë§Ö§ß§Ú§Ö §Õ§Ú§ã§Ü§Ñ." << endl
		<< "save - §ã§à§ç§â§Ñ§ß§Ö§ß§Ú§Ö §Õ§Ñ§ß§ß§í§ç §Õ§Ú§ã§Ü§Ñ §Ó §æ§Ñ§Û§Ý." << endl
		<< "read - §ã§é§Ú§ä§í§Ó§Ñ§ß§Ú§Ö §Õ§Ñ§ß§ß§í§ç §Õ§Ú§ã§Ü§Ñ §Ú§Ù §æ§Ñ§Û§Ý§Ñ." << endl
		<< "exit - §Ó§í§ç§à§Õ." << endl;
	cout << "-----------------------------" << endl;
}

int main() {
	ShowMenu();
	while (true) {
		string inpCommand;
		while (mainDisk == nullptr) {
			cout << endl << "*** §¥§Ý§ñ §â§Ñ§Ò§à§ä§í §ã §Õ§Ú§ã§Ü§à§Ó§í§Þ §å§ã§ä§â§à§Û§ã§ä§Ó§à§Þ §ß§Ö§à§Ò§ç§à§Õ§Ú§Þ§à §ã§à§Ù§Õ§Ñ§ä§î §Õ§Ú§ã§Ü. ***" << endl;
			cin >> inpCommand;
			if (inpCommand == "newdisk") { cout << "§£§Ó§Ö§Õ§Ú§ä§Ö §Ú§Þ§ñ §ß§à§Ó§à§Ô§à §Õ§Ú§ã§Ü§Ñ: "; string newDisk; cin >> newDisk; mainDisk = new Disk(newDisk); cout << "§µ§ã§á§Ö§ê§ß§à." << endl; }
			else if (inpCommand == "read") {
				int result = 0;
				mainDisk = new Disk(); result = mainDisk->readFromFile(result, "input.txt", mainDisk);
				if (result == 1) { mainDisk->readFromFile(result, "save_temp.txt", mainDisk); }
			}
			else if (inpCommand == "exit") {
				cout << "§£§í§ç§à§Õ..." << endl; return 0;
			}
		}
		while (mainDisk != nullptr) {
			cout << mainDisk->getDiskName() << ":\\> ";
			cin >> inpCommand;

			if (inpCommand == "newdisk") {
				if (mainDisk != nullptr) {
					cout << "§¥§Ñ§ß§ß§í§Ö §Õ§Ú§ã§Ü§Ñ §Ò§å§Õ§å§ä §å§Õ§Ñ§Ý§Ö§ß§í. §¢§å§Õ§Ö§ä §ã§à§Ù§Õ§Ñ§ß §ß§à§Ó§í§Û §Õ§Ú§ã§Ü." << endl
						<< "§µ§Ó§Ö§â§Ö§ß§í, §é§ä§à §ç§à§ä§Ú§ä§Ö §á§â§à§Õ§à§Ý§Ø§Ú§ä§î?" << endl
						<< "§¥§Ñ/§¯§Ö§ä: "; string answer; cin >> answer;
					if (answer == "§¥§Ñ" || answer == "§Õ§Ñ") {
						mainDisk->clearFolders();
						cout << "§£§Ó§Ö§Õ§Ú§ä§Ö §Ú§Þ§ñ §ß§à§Ó§à§Ô§à §Õ§Ú§ã§Ü§Ñ: "; string newDisk; cin >> newDisk; mainDisk = new Disk(newDisk); cout << "§µ§ã§á§Ö§ê§ß§à." << endl;
					}
					else if (answer == "§¯§Ö§ä" || answer == "§ß§Ö§ä") { continue; }
					else { cout << "§£§Ó§Ö§Õ§×§ß §ß§Ö§Ó§Ö§â§ß§í§Û §à§ä§Ó§Ö§ä." << endl; continue; }
				}
			}
			
			else if (inpCommand == "mdir") { cout << "§£§Ó§Ö§Õ§Ú§ä§Ö §Ú§Þ§ñ §á§Ñ§á§Ü§Ú: "; string _folderName; cin >> _folderName; mainDisk->AddFolder(_folderName); continue; }
			
			else if (inpCommand == "mfile") { 
				cout << "§£§Ó§Ö§Õ§Ú§ä§Ö §Ú§Þ§ñ §á§Ñ§á§Ü§Ú, §Ó §Ü§à§ä§à§â§å§ð §ç§à§ä§Ú§ä§Ö §Õ§à§Ò§Ñ§Ó§Ú§ä§î §æ§Ñ§Û§Ý: ";
				string _folderName; cin >> _folderName; int i;
				Folder* temp = mainDisk->findFolder(_folderName, i);
				if (temp == nullptr) { cout << "§±§Ñ§á§Ü§Ñ §ß§Ö §ß§Ñ§Û§Õ§Ö§ß§Ñ." << endl; continue; }
				temp->AddFile(); temp = nullptr;
			}
			
			else if (inpCommand == "findd") {
				cout << "§£§Ó§Ö§Õ§Ú§ä§Ö §Ú§Þ§ñ §á§Ñ§á§Ü§Ú §ß§Ñ §Õ§Ú§ã§Ü§Ö, §Ü§à§ä§à§â§å§ð §ç§à§ä§Ú§ä§Ö §ß§Ñ§Û§ä§Ú: ";
				string _folderName; cin >> _folderName; int i;
				Folder* temp = mainDisk->findFolder(_folderName, i);
				if (temp == nullptr) { cout << "§±§Ñ§á§Ü§Ñ §ß§Ö §ß§Ñ§Û§Õ§Ö§ß§Ñ." << endl; continue; }
				cout << "§±§Ñ§á§Ü§Ñ \"" << temp->getFolderName() << "\" §Ú§Õ§×§ä " << i << "-§à§Û §á§à §ã§á§Ú§ã§Ü§å." << endl;
				temp = nullptr;
			}
			
			else if (inpCommand == "findf") { mainDisk->findFromAll(); }

			else if (inpCommand == "show") { mainDisk->printDisk(); }
			
			else if (inpCommand == "showdir") {
				cout << "§£§Ó§Ö§Õ§Ú§ä§Ö §Ú§Þ§ñ §á§Ñ§á§Ü§Ú, §Ü§à§ä§à§â§å§ð §ç§à§ä§Ú§ä§Ö §Ó§í§Ó§Ö§ã§ä§Ú: "; string _fileName; cin >> _fileName; int i;
				Folder* temp = mainDisk->findFolder(_fileName, i);
				if (temp == nullptr) { cout << "§±§Ñ§á§Ü§Ñ §ß§Ö §ß§Ñ§Û§Õ§Ö§ß§Ñ." << endl; continue; }
				temp->ShowFolder();
				temp = nullptr;
			}

			else if (inpCommand == "rmdir") { mainDisk->removeFolder(); }

			else if (inpCommand == "rm") {
				cout << "§£§Ó§Ö§Õ§Ú§ä§Ö §Ú§Þ§ñ §á§Ñ§á§Ü§Ú, §Ú§Ù §Ü§à§ä§à§â§à§Û §ç§à§ä§Ú§ä§Ö §å§Õ§Ñ§Ý§Ú§ä§î §æ§Ñ§Û§Ý: ";
				string _folderName; cin >> _folderName; int i;
				Folder* temp = mainDisk->findFolder(_folderName, i);
				if (temp == nullptr) { cout << "§±§Ñ§á§Ü§Ñ §ß§Ö §ß§Ñ§Û§Õ§Ö§ß§Ñ." << endl; continue; }
				temp->DeleteFile(); temp = nullptr;
			}
			
			else if (inpCommand == "clear") { mainDisk->clearFolders(); }

			else if (inpCommand == "m") { ShowMenu(); }

			else if (inpCommand == "save") { cout << "§£§Ó§Ö§Õ§Ú§ä§Ö §Ú§Þ§ñ §æ§Ñ§Û§Ý§Ñ, §Ó §Ü§à§ä§à§â§í§Û §ç§à§ä§Ú§ä§Ö §ã§à§ç§â§Ñ§ß§Ú§ä§î §Õ§Ñ§ß§ß§í§Ö §Õ§Ú§ã§Ü§Ñ: "; string _file; cin >> _file; mainDisk->saveToFile(_file); }

			else if (inpCommand == "read") {
				int result = 0;
				result = mainDisk->readFromFile(result, "input.txt", mainDisk);
				if (result == 1) { mainDisk->readFromFile(result, "save_temp.txt", mainDisk); }
			}

			else if (inpCommand == "exit") {
				if (mainDisk != nullptr && !(mainDisk->isDiskEmpty())) {
					cout << "§¥§Ñ§ß§ß§í§Ö §Õ§Ú§ã§Ü§Ñ §Ò§å§Õ§å§ä §å§Õ§Ñ§Ý§Ö§ß§í." << endl
						<< "§£§ã§Ö §â§Ñ§Ó§ß§à §Ø§Ö§Ý§Ñ§Ö§ä§Ö §ã§Õ§Ö§Ý§Ñ§ä§î §ï§ä§à?" << endl
						<< "§¥§Ñ/§¯§Ö§ä: ";
					string answer; cin >> answer;
					if (answer == "§¥§Ñ" || answer == "§Õ§Ñ") {
						delete mainDisk; cout << "§£§í§ç§à§Õ..." << endl;
						return 0;
					}
					else if (answer == "§¯§Ö§ä" || answer == "§ß§Ö§ä") { continue; }
					else { cout << "§£§Ó§Ö§Õ§×§ß §ß§Ö§Ó§Ö§â§ß§í§Û §à§ä§Ó§Ö§ä." << endl; continue; }
				}
				cout << "§£§í§ç§à§Õ..." << endl; return 0;
			}

			else { cout << "§£§Ó§Ö§Õ§Ö§ß§Ñ §ß§Ö§Ó§Ö§â§ß§Ñ§ñ §Ü§à§Þ§Ñ§ß§Õ§Ñ." << endl; }
		}
	}
}