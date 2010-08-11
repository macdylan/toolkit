#ifndef UTILS_H_
#define UTILS_H_

#define DISALLOW_ASSIGNMENT(klass)  \
  private:  \
    klass(const klass&) {}  \
    void operator =(const klass&) {}

#endif  // UTILS_H_

