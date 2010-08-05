#ifndef PIX_CORE_H_
#define PIX_CORE_H_

#include <string>
#include <vector>
#include <map>

#include "sqlite3/sqlite3.h"

#include "pixlibrary.h"
#include "pixalbum.h"
#include "pagingtree.h"

class PixCore {

public:
  explicit PixCore(const std::string& fn);
  ~PixCore();

  std::vector<PixAlbum> listAlbums(bool nocache = false);

  void reloadAlbums() {
    this->listAlbums(true);
  }

  bool hasAlbum(const std::string& aname);

  int addAlbum(const std::string& aname);

  int removeAlbum(const std::string& aname);

  int renameAlbum(const std::string& oldName, const std::string& newName);

  int getAlbum(const std::string& aname, PixAlbum& album);

  std::vector<PixLibrary> listLibraries(bool nocache = false);

  void reloadLibraries() {
    this->listLibraries(true);
  }

  bool hasLibrary(const std::string& lname);

  int addLibrary(const std::string& lname);

  int removeLibrary(const std::string& lname);

  int renameLibrary(const std::string& oldName, const std::string& newName);

  int getLibrary(const std::string& lname, PixLibrary& library);

private:

  // disallow
  PixCore(const PixCore&) {};
  void operator =(const PixCore&) {};

  std::string fname;
  std::vector<PixAlbum> cachedAlbums;
  std::vector<PixLibrary> cachedLibraries;
  sqlite3* conn;
};

#endif  // PIX_CORE_H_

