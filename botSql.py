import sqlite3
import string
import random


class bot_sql:
    sql_create_table = """CREATE TABLE IF NOT EXISTS users (
                                        user_id integer PRIMARY KEY,
                                        first_name text,
                                        last_name text,
                                        username text,
                                        blocks_completed integer,
                                        banned integer DEFAULT 0 NOT NULL                                        
                                    );"""

    sql_create_password_table = """CREATE TABLE IF NOT EXISTS passwords (
                                        password text,
                                        used integer                                   
                                    );"""

    def __init__(self):
        self.con = sqlite3.connect('data.db', isolation_level=None, check_same_thread=False)
        self.cur = self.con.cursor()
        self.cur.execute(self.sql_create_table)
        self.cur.execute(self.sql_create_password_table)
        self.con.commit()

    def add_new_user(self, user_id, first_name, last_name, username, blocks_completed):
        self.cur.execute('''INSERT OR IGNORE INTO users(user_id, first_name, last_name, username, blocks_completed)
                          VALUES(?,?,?,?,?)''', [user_id, first_name, last_name, username, blocks_completed])
        self.con.commit()

    def is_user_already_in_table(self, id):
        self.cur.execute("SELECT user_id FROM users WHERE user_id = ?", (id,))
        data = self.cur.fetchall()
        if len(data) == 0:
            return False
        else:
            return True

    def get_user(self, id):
        self.cur.execute(
            "SELECT user_id, first_name, last_name, username, blocks_completed, banned FROM users WHERE user_id = ?",
            (id,))
        return self.cur.fetchall()[0]

    def is_user_banned(self, id):
        self.cur.execute("SELECT banned FROM users WHERE user_id = ?", (id,))
        try:
            return self.cur.fetchall()[0][0]
        except:
            return False

    def update_user(self, user_id, first_name, last_name, username, blocks_completed):
        self.cur.execute(
            "UPDATE users SET first_name = ?,last_name = ?,username= ?, blocks_completed=? WHERE user_id = ?",
            [first_name, last_name, username, blocks_completed, user_id])
        self.con.commit()

    def update_user_blocks(self, user_id, blocks_completed):
        self.cur.execute("UPDATE users SET blocks_completed=? WHERE user_id = ?", [blocks_completed, user_id])
        self.con.commit()

    def ban_user(self, user_id, ban=True):
        if ban:
            flag = 0
        else:
            flag = 1
        self.cur.execute("UPDATE users SET banned=? WHERE user_id = ?", [flag, user_id])
        self.con.commit()

    def get_all_users(self):
        self.cur.execute("SELECT user_id, first_name, last_name, username, blocks_completed,banned FROM users")
        return self.cur.fetchall()

    def delete_all(self):
        self.cur.execute("DELETE FROM users")
        self.cur.execute("VACUUM")

    def add_password(self, passw):
        self.cur.execute('''INSERT OR IGNORE INTO passwords(password,used)
                          VALUES(?,?)''', [passw, 0])
        self.con.commit()

    def password_proc(self, passw):
        self.cur.execute("SELECT password,used FROM passwords WHERE password = ?", (passw,))
        data = self.cur.fetchall()
        if len(data) == 0:
            return False
        else:
            if data[0][1] == 0:
                self.cur.execute("UPDATE passwords SET used=1 WHERE password = ?", [passw])
                self.con.commit()
                return True
        return False

    def get_all_passwd(self):
        self.cur.execute("SELECT password,used FROM passwords ")
        return self.cur.fetchall()

    def delate_all_passw(self):
        self.cur.execute("DELETE FROM passwords")
        self.cur.execute("VACUUM")

    def randomString(self, stringLength=10):
        letters = string.ascii_lowercase + string.ascii_uppercase + "1234567890"
        return ''.join(random.choice(letters) for i in range(stringLength))


#print(randomString())
#s = bot_sql()
# for i in range(5):
#     s.add_password(randomString(12))


#print(s.get_all_passwd())
#s.delate_all_passw()
#print(s.get_all_passwd())
#s.add_password(randomString())
#print(s.get_all_passwd())
#print(s.get_all_passwd())
# print(s.password_proc('lLF86sAev1SgDU'))
#s.update_user_blocks(228534214, 0)
#user_id_list = (users_id[0] for users_id in s.get_all_users())
#for i in user_id_list:
#    print(i)

# s.add_new_user(3435,"dd","ds","",1)
# print(s.get_user(3435))
# s.ban_user(343)
