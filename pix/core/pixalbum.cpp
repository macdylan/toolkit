#include "pixalbum.h"

using namespace std;

PixAlbum::PixAlbum() : aid(-1), aname("") {
}

PixAlbum::PixAlbum(int id, const string& name) : aid(id), aname(name) {
}

PixAlbum::~PixAlbum() {
}

