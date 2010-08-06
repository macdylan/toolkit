#ifndef PIX_CORE_H_
#define PIX_CORE_H_

#include <string>
#include <vector>
#include <map>

#include "sqlite3/sqlite3.h"

#include "mylock.h"
#include "pixlibrary.h"
#include "pixalbum.h"
#include "pixtag.h"
#include "pagingtree.h"

class PixCore {

public:
  explicit PixCore(const std::string& fn);
  ~PixCore();

  std::vector<PixAlbum> listAlbums(bool refresh = false);

  void reloadAlbums() {
    this->listAlbums(true);
  }

  bool hasAlbum(const std::string& aname);

  int addAlbum(const std::string& aname);

  int removeAlbum(const std::string& aname);

  int renameAlbum(const std::string& oldName, const std::string& newName);

  int getAlbum(const std::string& aname, PixAlbum& album);

  std::vector<PixLibrary> listLibraries(bool refresh = false);

  void reloadLibraries() {
    this->listLibraries(true);
  }

  bool hasLibrary(const std::string& lname);

  int addLibrary(const std::string& lname);

  int removeLibrary(const std::string& lname);

  int renameLibrary(const std::string& oldName, const std::string& newName);

  int getLibrary(const std::string& lname, PixLibrary& library);

  std::vector<PixTag> listTags(bool refresh = false);

  void reloadTags() {
    this->listTags(true);
  }

  bool hasTag(const std::string& tname);

  int addTag(const std::string& tname);

  int removeTag(const std::string& tname);

  int renameTag(const std::string& oldName, const std::string& newName);

  int getTag(const std::string& tname, PixTag& tag);

private:

  // disallow
  PixCore(const PixCore&) {};
  void operator =(const PixCore&) {};

  std::string fname;
  std::vector<PixAlbum> cachedAlbums;
  MyLock cachedAlbumsLock;
  std::vector<PixLibrary> cachedLibraries;
  MyLock cachedLibrariesLock;
  std::vector<PixTag> cachedTags;
  MyLock cachedTagsLock;
  sqlite3* conn;
  MyLock connLock;
};

#endif  // PIX_CORE_H_

