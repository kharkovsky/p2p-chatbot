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
