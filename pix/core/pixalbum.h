#ifndef PIX_ALBUM_H_
#define PIX_ALBUM_H_

#include <string>

class PixAlbum {

public:
  PixAlbum();
  PixAlbum(int aid, const std::string& aname);
  ~PixAlbum();

  std::string getName() {
    return aname;
  }

  int getId() {
    return aid;
  }

private:

  int aid;
  std::string aname;
};

#endif  // PIX_ALBUM_H_

