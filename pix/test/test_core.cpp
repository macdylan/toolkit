#include <cstdio>
#include <vector>
#include <sstream>

#include "pixcore.h"

using namespace std;

void do_test() {
  PixCore pc("pix");
  pc.hasAlbum("blah");
  pc.addAlbum("album1");
  pc.addAlbum("album2");
  pc.addAlbum("album3");
  pc.addAlbum("album4");
  vector<PixAlbum> albums = pc.listAlbums();
  for (vector<PixAlbum>::iterator it = albums.begin(); it != albums.end(); ++it) {
    printf("album: (%d) %s\n", it->getId(), it->getName().c_str());
  }
  pc.removeAlbum("album4");
  pc.addAlbum("album4");
  pc.renameAlbum("album4", "album2");
  pc.renameAlbum("a", "b");
  pc.removeAlbum("album7");
  albums = pc.listAlbums();
  for (vector<PixAlbum>::iterator it = albums.begin(); it != albums.end(); ++it) {
    printf("album: (%d) %s\n", it->getId(), it->getName().c_str());
  }
  pc.renameAlbum("album4", "album2");
  pc.addLibrary("lib1");
  pc.addLibrary("lib2");
  pc.renameLibrary("lib2", "lib1");
  pc.renameLibrary("lib1", "lib4");
  pc.renameLibrary("a", "x");
  vector<PixLibrary> libraries = pc.listLibraries();
  for (vector<PixLibrary>::iterator it = libraries.begin(); it != libraries.end(); ++it) {
    printf("library: (%d) %s\n", it->getId(), it->getName().c_str());
  }
  pc.removeLibrary("lib2");
  for (int i = 4; i < 1000; i++) {
    ostringstream o1;
    ostringstream o2;
    o1 << "lib" << i;
    o2 << "lib" << (i + 1);
    pc.renameLibrary(o1.str().c_str(), o2.str().c_str());
  }
  libraries = pc.listLibraries();
  for (vector<PixLibrary>::iterator it = libraries.begin(); it != libraries.end(); ++it) {
    printf("library: (%d) %s\n", it->getId(), it->getName().c_str());
  }
}

int main(int argc, char* argv[]) {
  do_test();
  return 0;
}
