#ifndef PIX_LIBRARY_H_
#define PIX_LIBRARY_H_

#include <string>

class PixLibrary {

public:
  PixLibrary();
  PixLibrary(int lid, const std::string& lname);
  ~PixLibrary();

  std::string getName() {
    return lname;
  }

  int getId() {
    return lid;
  }

private:

  int lid;
  std::string lname;

};

#endif  // PIX_LIBRARY_H_

