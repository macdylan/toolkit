# one script to manage all my pictures

import sqlite3

class Moe:
  
  def __init__(self, db_fn):
    self.__db_conn = sqlite3.connect(db_fn)
  
  def db_exec(self, query):
    print "[sql] %s" % query
    return self.__db_conn.execute(query)
  
  def setting(self, key, value = None):
    self.db_exec("create table if not exists settings(key text, value text)")
    if value == None:
      cur = self.__db_conn.cursor()
      cur.execute("select value from settings where key = '%s'" % key)
      ret = cur.fetchone()[0]
      cur.close()
      return ret
    else:
      cur = self.__db_conn.cursor()
      cur.execute("select value from settings where key = '%s'" % key)
      key_exists = cur.fetchone() != None
      cur.close()
      if key_exists:
        self.db_exec("update settings set value = '%s' where key = '%s'" % (value, key))
      else:
        self.db_exec("insert into settings values('%s', '%s')" % (key, value))
      self.__db_conn.commit();
      
if __name__ == "__main__":
  moe = Moe("moe.db3")
  ret = moe.setting("images_root", "..")
  print moe.setting("images_root")
