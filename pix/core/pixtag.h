#ifndef PIX_TAG_H_
#define PIX_TAG_H_

#include <string>

class PixTag {

public:
  PixTag();
  PixTag(int tid, const std::string& tname);
  ~PixTag();

  std::string getName() {
    return tname;
  }

  int getId() {
    return tid;
  }

private:

  int tid;
  std::string tname;
};

#endif  // PIX_TAG_H_

