#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <sstream>
#include <errno.h>

using namespace std;

#include "pixcore.h"

using namespace std;

static void my_exec(sqlite3* conn, const char* sql) {
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

static void my_exec(sqlite3* conn, const string& sql) {
  my_exec(conn, sql.c_str());
}

PixCore::PixCore(const string& fn) : fname(fn), conn(NULL) {
  assert(sqlite3_open(this->fname.c_str(), &this->conn) == SQLITE_OK);

  my_exec(this->conn,
          "create table if not exists libraries("
            "library_id integer primary key,"
            "library_name text)");
  
  my_exec(this->conn,
          "create table if not exists albums("
            "album_id integer primary key,"
            "album_name text unique)");

  my_exec(this->conn,
          "create table if not exists images("
            "image_id integer primary key,"
            "id_in_library integer,"
            "library_id integer)");

  my_exec(this->conn,
          "create table if not exists tags("
            "tag_id integer primary key,"
            "tag_name text)");

  my_exec(this->conn,
          "create table if not exists images_has_tags("
            "image_id integer,"
            "tag_id integer)");

  my_exec(this->conn,
          "create table if not exists albums_has_images("
            "image_id integer,"
            "album_id integer)");
  
  my_exec(this->conn,
          "create table if not exists settings("
            "key text primary key,"
            "value text)");

  my_exec(this->conn,
          "create table if not exists library_paging("
            "id integer primary key,"
            "library_id integer,"
            "parent_id integer,"
            "subtree_count integer,"
            "first_id_in_library integer,"
            "last_id_in_library integer)");

  my_exec(this->conn,
          "create index if not exists index1 on images(image_id)");

  my_exec(this->conn,
          "create index if not exists index2 on images(id_in_library, library_id)");

  my_exec(this->conn,
          "create index if not exists index3 on tags(tag_id)");

  my_exec(this->conn,
          "create index if not exists index4 on tags(tag_name)");

  my_exec(this->conn,
          "create index if not exists index5 on images_has_tags(image_id)");

  my_exec(this->conn,
          "create index if not exists index6 on images_has_tags(tag_id)");

  my_exec(this->conn,
          "create index if not exists index7 on albums_has_images(album_id)");

  my_exec(this->conn,
          "create index if not exists index8 on albums_has_images(image_id)");

  my_exec(this->conn,
          "create index if not exists index9 on library_paging(id, library_id)");

  my_exec(this->conn,
          "create index if not exists index10 on library_paging(parent_id, library_id)");

  // load albums into cache
  this->reloadAlbums();
  this->reloadLibraries();
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

vector<PixAlbum> PixCore::listAlbums(bool nocache /* = false */) {
  if (nocache) {
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
    this->cachedAlbums = albums;
  }
  return this->cachedAlbums;
}

bool PixCore::hasAlbum(const string& aname) {
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
    my_exec(this->conn, "insert into albums(album_name) values(\"" + aname + "\")");
    this->reloadAlbums();
    return 0;
  }
}

int PixCore::removeAlbum(const string& aname) {
  if (this->hasAlbum(aname)) {
    my_exec(this->conn, "delete from albums where album_name = \"" + aname + "\"");
    ostringstream oss;
    PixAlbum album;
    this->getAlbum(aname, album);
    oss << album.getId();
    my_exec(this->conn, "delete from albums_has_images where album_id = \"" + oss.str() + "\"");
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
  for (vector<PixAlbum>::iterator it = this->cachedAlbums.begin(); it != this->cachedAlbums.end(); ++it) {
    if (it->getName() == oldName) {
      my_exec(this->conn, "update albums set album_name = \"" + newName + "\" where album_name = \"" + oldName + "\"");
      *it = PixAlbum(it->getId(), newName);
      return 0;
    }
  }
  return ENOENT;
} 
int PixCore::getAlbum(const string& aname, PixAlbum& album) {
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

vector<PixLibrary> PixCore::listLibraries(bool nocache /* = false */) {
  if (nocache) {
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
    this->cachedLibraries = libraries;
  }
  return this->cachedLibraries;
}

bool PixCore::hasLibrary(const std::string& lname) {
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
    my_exec(this->conn, "insert into libraries(library_name) values(\"" + lname + "\")");
    this->reloadLibraries();
    return 0;
  }
}

int PixCore::removeLibrary(const string& lname) {
  if (this->hasLibrary(lname)) {
    my_exec(this->conn, "delete from libraries where library_name = \"" + lname + "\"");
    ostringstream oss;
    PixLibrary library;
    this->getLibrary(lname, library);
    oss << library.getId();
    my_exec(this->conn, "delete from images where library_id = \"" + oss.str() + "\"");
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
  for (vector<PixLibrary>::iterator it = this->cachedLibraries.begin(); it != this->cachedLibraries.end(); ++it) {
    if (it->getName() == oldName) {
      my_exec(this->conn, "update libraries set library_name = \"" + newName + "\" where library_name = \"" + oldName + "\"");
      *it = PixLibrary(it->getId(), newName);
      return 0;
    }
  }
  return ENOENT;
}

int PixCore::getLibrary(const string& lname, PixLibrary& library) {
  for (vector<PixLibrary>::iterator it = this->cachedLibraries.begin(); it != this->cachedLibraries.end(); ++it) {
    if (it->getName() == lname) {
      library = *it;
      return 0;
    }
  }
  return ENOENT;
}

