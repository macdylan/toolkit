#ifndef MY_LOCK_H_
#define MY_LOCK_H_

#ifdef WIN32
// TODO win32 lock
#else
// pthread lock
#include <pthread.h>
#endif  // WIN32

class MyLock {

public:
  MyLock() {
#ifdef WIN32
// TODO win32 lock
#else
// pthread lock
  pthread_mutex_init(&mutex, NULL);
#endif  // WIN32
  }

  ~MyLock() {
#ifdef WIN32
// TODO win32 lock
#else
// pthread lock
  pthread_mutex_destroy(&mutex);
#endif  // WIN32
  }

  void acquire() {
#ifdef WIN32
// TODO win32 lock
#else
// pthread lock
  pthread_mutex_lock(&mutex);
#endif  // WIN32
  }

  void release() {
#ifdef WIN32
// TODO win32 lock
#else
// pthread lock
  pthread_mutex_unlock(&mutex);
#endif  // WIN32
  }

private:
  // disallow

  MyLock(const MyLock&) {}
  void operator =(const MyLock&) {}

#ifdef WIN32
// TODO win32 lock
#else
// pthread lock
  pthread_mutex_t mutex;
#endif  // WIN32

};

class MyScopedLock {
public:
  MyScopedLock(MyLock* l) : lock(l) {
    this->lock->acquire();
  }

  ~MyScopedLock() {
    this->lock->release();
  }

private:
  MyLock* lock;
};

#endif  // MY_LOCK_H_
