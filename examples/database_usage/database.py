_db_instance = None


class FakeDatabase:
    def __init__(self):
        self.contents = {}

    def insert(self, table: str, *data):
        current_contents = self.contents.get(table, [])
        current_contents.append(*data)
        self.contents[table] = current_contents

    def query(self, table: str, target_value):
        table_values = self.contents.get(table, [])
        for key_value, *other_values in table_values:
            if key_value == target_value:
                return key_value, *other_values
        return None


# Typically here you would create a session with whatever database
# library you're using. For example, with pymysql, this function could
# return a cursor. With SQLAlchemy, this could instead return a session.
def get_session():
    global _db_instance

    if _db_instance is None:
        _db_instance = FakeDatabase()

    return _db_instance
