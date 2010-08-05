#include "pixlibrary.h"

using namespace std;

PixLibrary::PixLibrary() : lid(-1), lname("") {
}

PixLibrary::PixLibrary(int id, const string& name) : lid(id), lname(name) {
}

PixLibrary::~PixLibrary() {
}

