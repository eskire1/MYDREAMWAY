#include <iostream>

using namespace std;

class File {
private:
	int size;
	string fileName;
public:
	File() {
		size = -1;
		fileName = "";
	}
	
	File(string _fileName, int _size) {
		size = _size;
		fileName = _fileName;
	}

	string getFileName() { return fileName; }
	void setFileName(string _fileName) { fileName = _fileName; }
	int getSize() { return size; }
	void setSize(int _size) { size = _size; }
};