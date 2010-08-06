#include "pixtag.h"

using namespace std;

PixTag::PixTag() : tid(-1), tname("") {
}

PixTag::PixTag(int id, const string& name) : tid(id), tname(name) {
}

PixTag::~PixTag() {
}
