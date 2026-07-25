#include "File.h"

int const maxCountFiles = 5;

class Folder {
private:
	string folderName;
	Folder* nextFolder;
	File files[maxCountFiles];
	int fileCount;
	int first;
	int last;
public:
	Folder() {
		folderName = "";
		nextFolder = nullptr;
		fileCount = 0;
		first = 0;
		last = 0;
	}
	
	Folder(string _folderName) {
		folderName = _folderName;
		nextFolder = nullptr;
		fileCount = 0;
		first = 0;
		last = 0;
	}

	~Folder() {
		folderName = "";
		nextFolder = nullptr;
		for (int i = 0; i < fileCount; i++) {
			files[i].setFileName("");
			files[i].setSize(-1);
		}
		fileCount = 0;
		first = 0;
		last = 0;
	}
	
	string getFolderName() { return folderName; }
	void setFolderName(string _folderName) { folderName = _folderName; }
	Folder* getNextFolder() { return nextFolder; }
	void setNextFolder(Folder* _nextFolder) { nextFolder = _nextFolder; }
	File* getFilesArray() { return &(files[0]); }
	int getFileCount() { return fileCount; }
	bool isFolderEmpty() { return fileCount == 0; }
	bool isFolderFull() { return fileCount == maxCountFiles; }

	void AddFile() {
		if (isFolderFull()) {
			cout << "§±§Ñ§á§Ü§Ñ §Ù§Ñ§á§à§Ý§ß§Ö§ß§Ñ. §¥§à§Ò§Ñ§Ó§Ý§Ö§ß§Ú§Ö §ß§Ö§Ó§à§Ù§Þ§à§Ø§ß§à." << endl;
			return;
		}
		cout << "§£§Ó§Ö§Õ§Ú§ä§Ö §Ú§Þ§ñ §æ§Ñ§Û§Ý§Ñ: "; string _fileName; cin >> _fileName;
		cout << "§£§Ó§Ö§Õ§Ú§ä§Ö §â§Ñ§Ù§Þ§Ö§â §æ§Ñ§Û§Ý§Ñ: "; int _size; cin >> _size;

		int pos = last;  // §±§à§Ù§Ú§è§Ú§ñ §Õ§Ý§ñ §Ó§ã§ä§Ñ§Ó§Ü§Ú
		if (!isFolderEmpty()) {
			// §±§à§Ú§ã§Ü §á§à§Ù§Ú§è§Ú§Ú §Õ§Ý§ñ §Ó§ã§ä§Ñ§Ó§Ü§Ú
			int current = first;
			do {
				if (files[current].getFileName() > _fileName) { pos = current; break; }
				current = (current + 1) % maxCountFiles;
			} while (current != last);
		}

		// §³§Õ§Ó§Ú§Ô §ï§Ý§Ö§Þ§Ö§ß§ä§à§Ó §Ó§á§â§Ñ§Ó§à §Õ§Ý§ñ §Ó§ã§ä§Ñ§Ó§Ü§Ú
		if (pos != last) {
			int i = last;
			do {
				int prev = (i - 1 + maxCountFiles) % maxCountFiles;
				files[i] = files[prev];
				i = prev;
			} while (i != pos);
		}

		// §£§ã§ä§Ñ§Ó§Ü§Ñ §ï§Ý§Ö§Þ§Ö§ß§ä§Ñ
		files[pos].setFileName(_fileName);
		files[pos].setSize(_size);
		last = (last + 1) % maxCountFiles;
		fileCount++;
	}

	void DeleteFile() {
		if (isFolderEmpty()) { cout << "§±§Ñ§á§Ü§Ñ §á§å§ã§ä§Ñ. §µ§Õ§Ñ§Ý§Ú§ä§î §ß§Ö§Ó§à§Ù§Þ§à§Ø§ß§à." << endl; return; }
		// §µ§Õ§Ñ§Ý§Ö§ß§Ú§Ö §Ú§Ù §ß§Ñ§é§Ñ§Ý§Ñ §à§é§Ö§â§Ö§Õ§Ú
		files[first].setFileName("");
		files[first].setSize(-1);
		first = (first + 1) % maxCountFiles;
		fileCount--;
	}

	void ShowFolder() {
		if (isFolderEmpty()) {
			cout << "§±§Ñ§á§Ü§Ñ §á§å§ã§ä§Ñ." << endl;
			return;
		}
		int current = first;
		for (int i = 0; i < fileCount; i++) {
			cout << "- " << files[current].getFileName() << " (" << files[current].getSize() << " KB)" << endl;
			current = (current + 1) % maxCountFiles;
		}
	}

	int FindFile() {
		if (isFolderEmpty()) {
			cout << "§±§Ñ§á§Ü§Ñ §á§å§ã§ä§Ñ." << endl;
			return -1;
		}
		cout << "§£§Ó§Ö§Õ§Ú§ä§Ö §Ú§Þ§ñ §æ§Ñ§Û§Ý§Ñ: "; string _fileName; cin >> _fileName;

		int current = first;
		for (int i = 0; i < fileCount; i++) {
			if (files[current].getFileName() == _fileName) {
				return current;
			}
			current = (current + 1) % maxCountFiles;
		}
		cout << "§¶§Ñ§Û§Ý §ß§Ö §ß§Ñ§Û§Õ§Ö§ß." << endl;
		return -1;
	}

	void AddFileFrom(string _fileName, int _size) {
		if (isFolderFull()) {
			cout << "§±§Ñ§á§Ü§Ñ §Ù§Ñ§á§à§Ý§ß§Ö§ß§Ñ. §¥§à§Ò§Ñ§Ó§Ý§Ö§ß§Ú§Ö §ß§Ö§Ó§à§Ù§Þ§à§Ø§ß§à." << endl;
			return;
		}
		int pos = last;  // §±§à§Ù§Ú§è§Ú§ñ §Õ§Ý§ñ §Ó§ã§ä§Ñ§Ó§Ü§Ú
		if (!isFolderEmpty()) {
			// §±§à§Ú§ã§Ü §á§à§Ù§Ú§è§Ú§Ú §Õ§Ý§ñ §Ó§ã§ä§Ñ§Ó§Ü§Ú
			int current = first;
			do {
				if (files[current].getFileName() > _fileName) { pos = current; break; }
				current = (current + 1) % maxCountFiles;
			} while (current != last);
		}

		// §³§Õ§Ó§Ú§Ô §ï§Ý§Ö§Þ§Ö§ß§ä§à§Ó §Ó§á§â§Ñ§Ó§à §Õ§Ý§ñ §Ó§ã§ä§Ñ§Ó§Ü§Ú
		if (pos != last) {
			int i = last;
			do {
				int prev = (i - 1 + maxCountFiles) % maxCountFiles;
				files[i] = files[prev];
				i = prev;
			} while (i != pos);
		}

		// §£§ã§ä§Ñ§Ó§Ü§Ñ §ï§Ý§Ö§Þ§Ö§ß§ä§Ñ
		files[pos].setFileName(_fileName);
		files[pos].setSize(_size);
		last = (last + 1) % maxCountFiles;
		fileCount++;
	}
};
