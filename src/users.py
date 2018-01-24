from enum import Enum
import sqlite3


class Database:
    connection = None

    @staticmethod
    def init():
        Database.connection = Database.get()
        Database.connection.execute("""
                            CREATE TABLE IF NOT EXISTS users (
                                id INTEGER PRIMARY KEY
                            );
                            """)
        Database.connection.commit()

    @staticmethod
    def get():
        """
        :rtype: sqlite3.Connection
        """
        if Database.connection is None:
            Database.connection = sqlite3.connect('users.sqlite3', check_same_thread=False)
        return Database.connection

    @staticmethod
    def cursor():
        """
        :rtype: sqlite3.Cursor
        """
        return Database.get().cursor()

    @staticmethod
    def save():
        Database.get().commit()

    @staticmethod
    def add_user(user_id):
        """
        :rtype: bool
        """
        cursor = Database.cursor()
        try:
            cursor.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
            Database.save()

            cursor.execute('SELECT changes()')
            changes = cursor.fetchone()
            success = changes[0] > 0
        except sqlite3.IntegrityError:
            return False
        else:
            return success
        finally:
            cursor.close()

    @staticmethod
    def exists(user_id):
        """
        :rtype: bool
        """
        cursor = Database.cursor()

        try:
            cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))

            result = cursor.fetchall()
        except:
            return False
        else:
            return len(result) == 1
        finally:
            cursor.close()

    @staticmethod
    def remove_user(user_id):
        """
        :rtype: bool
        """
        cursor = Database.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
            Database.save()

            cursor.execute('SELECT changes()')
            changes = cursor.fetchone()
            success = changes[0] == 1
        except sqlite3.OperationalError:
            return False
        else:
            return success
        finally:
            cursor.close()

    @staticmethod
    def user_list():
        cursor = Database.cursor()

        try:
            cursor.execute("SELECT * FROM users")
            result = cursor.fetchall()

            return map(lambda row: row[0], result)
        except:
            return []
        finally:
            cursor.close()

    @staticmethod
    def close():
        if Database.connection is not None:
            Database.connection.close()
            Database.connection = None


class User:
    class State(Enum):
        IDLE, SEARCHING, CHATTING = range(3)

    def __init__(self, user_id, state=None, target=None):
        if type(target) is not User and target is not None:
            raise TypeError("Target must be another User or None!")
        if type(state) is not User.State and state is not None:
            raise TypeError("State must constant from User.State or None!")

        self.id = user_id
        self.state = User.State.IDLE if state is None else state
        self.target = target

        Database.add_user(user_id)
        print("Added user: {}".format(user_id))

    def is_idle(self):
        return self.state == User.State.IDLE

    def is_searching(self):
        return self.state == User.State.SEARCHING

    def is_chatting(self):
        return self.state == User.State.CHATTING

    def set_chatting_with(self, another_user):
        if type(another_user) is not User:
            raise TypeError("Illegal type for another_user! Must be User!")

        self.target = another_user
        self.state = User.State.CHATTING

    def __del__(self):
        Database.remove_user(self.id)
        print("Removed user {}".format(self.id))


class Users:
    active = {}  # id: User
    searching = []  # id's

    def __init__(self, users):
        for user_id in users:
            self.active[user_id] = User(user_id)

    def add(self, user_id):
        self.active[user_id] = User(user_id)

    def remove(self, user_id):
        del self.active[user_id]

    def get(self, user_id):
        return self.active.get(user_id)

    def search_list(self):
        return self.searching

    def search_empty(self):
        return len(self.searching) == 0

    def search_add(self, user_id):
        if user_id not in self.active:
            raise IndexError("user_id not in active list!")

        self.searching.append(user_id)
        self.active[user_id].state = User.State.SEARCHING
        print("[SEARCH] - Added to queue: {}".format(user_id))

    def create_chat(self, another_user_id, user_id=None):
        if user_id is None:
            if self.search_empty():
                raise IndexError("Search list is empty and not specified 2nd user!")
            if another_user_id not in self.active:
                raise TypeError("Another user not in active list!")

            user = self.active[self.searching.pop()]
            another_user = self.active[another_user_id]

            user.set_chatting_with(another_user)
            another_user.set_chatting_with(user)

            print("[CHAT] - Started between {} and {}".format(user.id, another_user.id))
            return user.id, another_user.id
        else:
            raise InterruptedError("NO_ACTIONS_SPECIFIED::TODO")

    def stop_chat(self, user_id):
        if user_id not in self.active:
            raise IndexError("user_id not in active list!")
        if self.active[user_id].target is None:
            raise TypeError("User has no chat target!")

        users = self.active[user_id], self.active[user_id].target

        for i, user in enumerate(users):
            if not user.is_chatting():
                raise IndexError("user{} not chatting!".format(i))
            user.state = User.State.IDLE
            user.target = None

        print("Chat stopped by {}".format(user_id))
        return map(lambda usr: usr.id, users)

    def in_search(self, user_id):
        return user_id in self.searching

    def search_remove(self, user_id):
        if user_id not in self.active:
            raise IndexError("user_id not in active list!")

        self.searching.remove(user_id)
        self.active[user_id].state = User.State.IDLE
        print("[SEARCH] - Removed to queue: {}".format(user_id))

    def is_idle(self, user_id):
        return self.active[user_id].is_idle()

    def is_chatting(self, user_id):
        return self.active[user_id].is_chatting()

    def exists(self, user_id):
        return user_id in self.active


class Debug:
    @staticmethod
    def users_searching():
        """
        :rtype: list
        """
        return Users.searching

    @staticmethod
    def users_active():
        """
        :rtype: list
        """
        return map(lambda key: Users.active[key].id, Users.active.keys())

    @staticmethod
    def users_chatting():
        """
        :rtype: list
        """
        return map(lambda usr: usr.id, filter(lambda key: Users.active[key].state == User.State.CHATTING,
                                              Users.active.keys()))
