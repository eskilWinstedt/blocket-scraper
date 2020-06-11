import mysql.connector

DB_NAME = "blocket_scraper"
TABLE_NAME = "users"

mydb = mysql.connector.connect(
    host = "localhost",
    user = "root",
    passwd = "ANC:s viktiga partikongress"
)

cursor = mydb.cursor(buffered=True)

cursor.execute("SHOW DATABASES")
exists = False

for database in cursor:
    if database[0] == DB_NAME:
        exists = True
        break

if not exists:
    cursor.execute("CREATE DATABASE {0}".format(DB_NAME))
    print(cursor)

cursor.execute("USE {0}".format(DB_NAME))
print(cursor)

cursor.execute("SHOW TABLES")
exists = False

for table in cursor:
    if table[0] == TABLE_NAME:
        exists = True
        break

if not exists:
    cursor.execute("CREATE TABLE {0} (name VARCHAR(255), email VARCHAR(255), age INTEGER(10), user_id INTEGER AUTO_INCREMENT PRIMARY KEY)".format(TABLE_NAME))

cursor.execute("SHOW TABLES")
for table in cursor:
    print(table[0])

sqlStuff = "INSERT INTO users (name, email, age) VALUES (%s, %s, %s)"
record1 = ("John", "john@codemy.com", 40)

cursor.execute(sqlStuff, record1)

mydb.commit()