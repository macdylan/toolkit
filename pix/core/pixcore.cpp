#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <sstream>
#include <errno.h>

#include "mylock.h"

#include "pixcore.h"

using namespace std;

static void my_exec(sqlite3* conn, const char* sql, MyLock* l) {
  MyScopedLock lock(l);
  char* error_msg = NULL;
  printf("[exec] %s\n", sql);
  int ret = sqlite3_exec(conn, sql, NULL, NULL, &error_msg);
  if (ret != SQLITE_OK) {
    printf("[fatal] sqlite: %s\n", error_msg);
    sqlite3_free(error_msg);
    exit(1);
  } else {
    printf("[info] done: %s\n", sql);
  }
}

static void my_exec(sqlite3* conn, const string& sql, MyLock* l) {
  my_exec(conn, sql.c_str(), l);
}

PixCore::PixCore(const string& fn) : fname(fn), conn(NULL) {
  assert(sqlite3_open(this->fname.c_str(), &this->conn) == SQLITE_OK);

  my_exec(this->conn,
          "create table if not exists libraries("
            "library_id integer primary key,"
            "library_name text unique)",
          &this->connLock);
  
  my_exec(this->conn,
          "create table if not exists albums("
            "album_id integer primary key,"
            "album_name text unique)",
          &this->connLock);

  my_exec(this->conn,
          "create table if not exists images("
            "image_id integer primary key,"
            "id_in_library integer,"
            "library_id integer)",
          &this->connLock);

  my_exec(this->conn,
          "create table if not exists tags("
            "tag_id integer primary key,"
            "tag_name text unique)",
          &this->connLock);

  my_exec(this->conn,
          "create table if not exists images_has_tags("
            "image_id integer,"
            "tag_id integer)",
          &this->connLock);

  my_exec(this->conn,
          "create table if not exists albums_has_images("
            "image_id integer,"
            "album_id integer)",
          &this->connLock);
  
  my_exec(this->conn,
          "create table if not exists settings("
            "key text primary key,"
            "value text)",
          &this->connLock);

  my_exec(this->conn,
          "create table if not exists library_paging("
            "id integer primary key,"
            "library_id integer,"
            "parent_id integer,"
            "subtree_count integer,"
            "first_id_in_library integer,"
            "last_id_in_library integer)",
          &this->connLock);

  my_exec(this->conn,
          "create index if not exists index1 on images(image_id)",
          &this->connLock);

  my_exec(this->conn,
          "create index if not exists index2 on images(id_in_library, library_id)",
          &this->connLock);

  my_exec(this->conn,
          "create index if not exists index3 on tags(tag_id)",
          &this->connLock);

  my_exec(this->conn,
          "create index if not exists index4 on tags(tag_name)",
          &this->connLock);

  my_exec(this->conn,
          "create index if not exists index5 on images_has_tags(image_id)",
          &this->connLock);

  my_exec(this->conn,
          "create index if not exists index6 on images_has_tags(tag_id)",
          &this->connLock);

  my_exec(this->conn,
          "create index if not exists index7 on albums_has_images(album_id)",
          &this->connLock);

  my_exec(this->conn,
          "create index if not exists index8 on albums_has_images(image_id)",
          &this->connLock);

  my_exec(this->conn,
          "create index if not exists index9 on library_paging(id, library_id)",
          &this->connLock);

  my_exec(this->conn,
          "create index if not exists index10 on library_paging(parent_id, library_id)",
          &this->connLock);

  // load cached info
  this->reloadAlbums();
  this->reloadLibraries();
  this->reloadTags();
  this->reloadSettings();
}

PixCore::~PixCore() {
  if (this->conn != NULL) {
    assert(sqlite3_close(this->conn) == SQLITE_OK);
  }
  this->conn = NULL;
}

static int list_albums_into_vector(void* vec_ptr, int n_cols, char* val[], char* col[]) {
  assert(n_cols == 2);
  int aid = -1;
  char* aname = NULL;
  for (int i = 0; i < n_cols; i++) {
    if (strcmp(col[i], "album_id") == 0) {
      aid = atoi(val[i]);
    } else if (strcmp(col[i], "album_name") == 0) {
      aname = val[i];
    }
  }
  assert(aid != -1 && aname != NULL);
  PixAlbum album(aid, aname);
  ((vector<PixAlbum>*) vec_ptr)->push_back(album);
  return 0;
}

vector<PixAlbum> PixCore::listAlbums(bool refresh /* = false */) {
  if (refresh) {
    MyScopedLock lock(&this->connLock);
    vector<PixAlbum> albums;
    char* error_msg = NULL;
    int ret = sqlite3_exec(this->conn, "select album_id, album_name from albums",
        list_albums_into_vector,
        &albums, &error_msg);
    if (ret != SQLITE_OK) {
      printf("[fatal] sqlite: %s\n", error_msg);
      sqlite3_free(error_msg);
      exit(1);
    }
    MyScopedLock(&this->cachedAlbumsLock);
    this->cachedAlbums = albums;
  }
  return this->cachedAlbums;
}

bool PixCore::hasAlbum(const string& aname) {
  MyScopedLock(&this->cachedAlbumsLock);
  for (vector<PixAlbum>::iterator it = this->cachedAlbums.begin(); it != this->cachedAlbums.end(); ++it) {
    if (it->getName() == aname) {
      return true;
    }
  }
  return false;
}

int PixCore::addAlbum(const string& aname) {
  if (this->hasAlbum(aname)) {
    return EEXIST;
  } else {
    my_exec(this->conn, "insert into albums(album_name) values(\"" + aname + "\")", &this->connLock);
    this->reloadAlbums();
    return 0;
  }
}

int PixCore::removeAlbum(const string& aname) {
  if (this->hasAlbum(aname)) {
    my_exec(this->conn, "delete from albums where album_name = \"" + aname + "\"", &this->connLock);
    ostringstream oss;
    PixAlbum album;
    this->getAlbum(aname, album);
    oss << album.getId();
    my_exec(this->conn, "delete from albums_has_images where album_id = \"" + oss.str() + "\"", &this->connLock);
    this->reloadAlbums();
    return 0;
  } else {
    return ENOENT;
  }
}

int PixCore::renameAlbum(const string& oldName, const string& newName) {
  if (oldName == newName) {
    return 0;
  }
  if (this->hasAlbum(newName)) {
    return EEXIST;
  }
  MyScopedLock(&this->cachedAlbumsLock);
  for (vector<PixAlbum>::iterator it = this->cachedAlbums.begin(); it != this->cachedAlbums.end(); ++it) {
    if (it->getName() == oldName) {
      my_exec(this->conn, "update albums set album_name = \"" + newName + "\" where album_name = \"" + oldName + "\"", &this->connLock);
      *it = PixAlbum(it->getId(), newName);
      return 0;
    }
  }
  return ENOENT;
}

int PixCore::getAlbum(const string& aname, PixAlbum& album) {
  MyScopedLock(&this->cachedAlbumsLock);
  for (vector<PixAlbum>::iterator it = this->cachedAlbums.begin(); it != this->cachedAlbums.end(); ++it) {
    if (it->getName() == aname) {
      album = *it;
      return 0;
    }
  }
  return ENOENT;
}

static int list_libraries_into_vector(void* vec_ptr, int n_cols, char* val[], char* col[]) {
  assert(n_cols == 2);
  int lid = -1;
  char* lname = NULL;
  for (int i = 0; i < n_cols; i++) {
    if (strcmp(col[i], "library_id") == 0) {
      lid = atoi(val[i]);
    } else if (strcmp(col[i], "library_name") == 0) {
      lname = val[i];
    }
  }
  assert(lid != -1 && lname != NULL);
  PixLibrary library(lid, lname);
  ((vector<PixLibrary>*) vec_ptr)->push_back(library);
  return 0;
}

vector<PixLibrary> PixCore::listLibraries(bool refresh /* = false */) {
  if (refresh) {
    MyScopedLock lock(&this->connLock);
    vector<PixLibrary> libraries;
    char* error_msg = NULL;
    int ret = sqlite3_exec(this->conn, "select library_id, library_name from libraries",
        list_libraries_into_vector,
        &libraries, &error_msg);
    if (ret != SQLITE_OK) {
      printf("[fatal] sqlite: %s\n", error_msg);
      //sqlite3_free(error_msg);
      exit(1);
    }
    MyScopedLock(&this->cachedLibrariesLock);
    this->cachedLibraries = libraries;
  }
  return this->cachedLibraries;
}

bool PixCore::hasLibrary(const std::string& lname) {
  MyScopedLock(&this->cachedLibrariesLock);
  for (vector<PixLibrary>::iterator it = this->cachedLibraries.begin(); it != this->cachedLibraries.end(); ++it) {
    if (it->getName() == lname) {
      return true;
    }
  }
  return false;
}

int PixCore::addLibrary(const string& lname) {
  if (this->hasLibrary(lname)) {
    return EEXIST;
  } else {
    my_exec(this->conn, "insert into libraries(library_name) values(\"" + lname + "\")", &this->connLock);
    this->reloadLibraries();
    return 0;
  }
}

int PixCore::removeLibrary(const string& lname) {
  if (this->hasLibrary(lname)) {
    my_exec(this->conn, "delete from libraries where library_name = \"" + lname + "\"", &this->connLock);
    ostringstream oss;
    PixLibrary library;
    this->getLibrary(lname, library);
    oss << library.getId();
    my_exec(this->conn, "delete from images where library_id = \"" + oss.str() + "\"", &this->connLock);
    this->reloadLibraries();
    return 0;
  } else {
    return ENOENT;
  }
}

int PixCore::renameLibrary(const string& oldName, const string& newName) {
  if (oldName == newName) {
    return 0;
  }
  if (this->hasLibrary(newName)) {
    return EEXIST;
  }
  MyScopedLock(&this->cachedLibrariesLock);
  for (vector<PixLibrary>::iterator it = this->cachedLibraries.begin(); it != this->cachedLibraries.end(); ++it) {
    if (it->getName() == oldName) {
      my_exec(this->conn, "update libraries set library_name = \"" + newName +
                        "\" where library_name = \"" + oldName + "\"", &this->connLock);
      *it = PixLibrary(it->getId(), newName);
      return 0;
    }
  }
  return ENOENT;
}

int PixCore::getLibrary(const string& lname, PixLibrary& library) {
  MyScopedLock(&this->cachedLibrariesLock);
  for (vector<PixLibrary>::iterator it = this->cachedLibraries.begin(); it != this->cachedLibraries.end(); ++it) {
    if (it->getName() == lname) {
      library = *it;
      return 0;
    }
  }
  return ENOENT;
}

static int list_tags_into_vector(void* vec_ptr, int n_cols, char* val[], char* col[]) {
  assert(n_cols == 2);
  int tid = -1;
  char* tname = NULL;
  for (int i = 0; i < n_cols; i++) {
    if (strcmp(col[i], "tag_id") == 0) {
      tid = atoi(val[i]);
    } else if (strcmp(col[i], "tag_name") == 0) {
      tname = val[i];
    }
  }
  assert(tid != -1 && tname != NULL);
  PixTag tag(tid, tname);
  ((vector<PixTag>*) vec_ptr)->push_back(tag);
  return 0;
}

vector<PixTag> PixCore::listTags(bool refresh /* = false */) {
  if (refresh) {
    MyScopedLock lock(&this->connLock);
    vector<PixTag> tags;
    char* error_msg = NULL;
    int ret = sqlite3_exec(this->conn, "select tag_id, tag_name from tags",
        list_tags_into_vector,
        &tags, &error_msg);
    if (ret != SQLITE_OK) {
      printf("[fatal] sqlite: %s\n", error_msg);
      sqlite3_free(error_msg);
      exit(1);
    }
    MyScopedLock(&this->cachedTagsLock);
    this->cachedTags = tags;
  }
  return this->cachedTags;
}

bool PixCore::hasTag(const string& tname) {
  MyScopedLock(&this->cachedTagsLock);
  for (vector<PixTag>::iterator it = this->cachedTags.begin(); it != this->cachedTags.end(); ++it) {
    if (it->getName() == tname) {
      return true;
    }
  }
  return false;
}

int PixCore::addTag(const string& tname) {
  if (this->hasTag(tname)) {
    return EEXIST;
  } else {
    my_exec(this->conn, "insert into tags(tag_name) values(\"" + tname + "\")", &this->connLock);
    this->reloadTags();
    return 0;
  }
}

int PixCore::removeTag(const string& tname) {
  if (this->hasTag(tname)) {
    my_exec(this->conn, "delete from tags where tag_name = \"" + tname + "\"", &this->connLock);
    ostringstream oss;
    PixTag tag;
    this->getTag(tname, tag);
    oss << tag.getId();
    my_exec(this->conn, "delete from images_has_tags where tag_id = \"" + oss.str() + "\"", &this->connLock);
    this->reloadTags();
    return 0;
  } else {
    return ENOENT;
  }
}

int PixCore::renameTag(const string& oldName, const string& newName) {
  if (oldName == newName) {
    return 0;
  }
  if (this->hasTag(newName)) {
    return EEXIST;
  }
  MyScopedLock(&this->cachedTagsLock);
  for (vector<PixTag>::iterator it = this->cachedTags.begin(); it != this->cachedTags.end(); ++it) {
    if (it->getName() == oldName) {
      my_exec(this->conn, "update tags set tag_name = \"" + newName + "\" where tag_name = \"" + oldName + "\"", &this->connLock);
      // TODO handle error. renaming might fail
      *it = PixTag(it->getId(), newName);
      return 0;
    }
  }
  return ENOENT;
}

int PixCore::getTag(const string& tname, PixTag& tag) {
  MyScopedLock(&this->cachedTagsLock);
  for (vector<PixTag>::iterator it = this->cachedTags.begin(); it != this->cachedTags.end(); ++it) {
    if (it->getName() == tname) {
      tag = *it;
      return 0;
    }
  }
  return ENOENT;
}

bool PixCore::hasSetting(const string& key) {
  MyScopedLock lock(&this->cachedSettingsLock);
  if (this->cachedSettings.find(key) == this->cachedSettings.end()) {
    return false;
  } else {
    return true;
  }
}

int PixCore::getSetting(const string& key, string& value) {
  MyScopedLock lock(&this->cachedSettingsLock);
  map<string, string>::iterator it = this->cachedSettings.find(key);
  if (it == this->cachedSettings.end()) {
    return ENOENT;
  } else {
    value = it->second;
    return 0;
  }
}

int PixCore::setSetting(const string& key, const string& value) {
  MyScopedLock lock(&this->cachedSettingsLock);
  this->cachedSettings[key] = value;
  // TODO what if value has ""?
  my_exec(this->conn, "update settings set value = \"" + value + "\" where key = \"" + key + "\"", &this->connLock);
  // TODO handle error
  return 0;
}

static int list_settings_into_vector(void* vec_ptr, int n_cols, char* val[], char* col[]) {
  assert(n_cols == 2);
  char* key = NULL;
  char* value = NULL;
  for (int i = 0; i < n_cols; i++) {
    if (strcmp(col[i], "key") == 0) {
      key = col[i];
    } else if (strcmp(col[i], "value") == 0) {
      value = col[i];
    }
  }
  assert(key != NULL && value != NULL);
  ((vector<pair<string, string> >*) vec_ptr)->push_back(make_pair<string, string>(key, value));
  return 0;
}

vector<pair<string, string> > PixCore::listSettings(bool refresh /* = false */) {
  vector<pair<string, string> > settings;
  if (refresh) {
    MyScopedLock lock(&this->connLock);
    char* error_msg = NULL;
    int ret = sqlite3_exec(this->conn, "select key, value from settings",
        list_settings_into_vector,
        &settings, &error_msg);
    if (ret != SQLITE_OK) {
      printf("[fatal] sqlite: %s\n", error_msg);
      sqlite3_free(error_msg);
      exit(1);
    }
    MyScopedLock(&this->cachedSettingsLock);
    this->cachedSettings.clear();
    for (vector<pair<string, string> >::iterator it = settings.begin(); it != settings.end(); ++it) {
      this->cachedSettings[it->first] = it->second;
    }
  } {
    MyScopedLock(&this->cachedSettingsLock);
    for (map<string, string>::iterator it = this->cachedSettings.begin(); it != this->cachedSettings.end(); ++it) {
      settings.push_back(*it);
    }
  }
  return settings;
}

