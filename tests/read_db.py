import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

conn = get_db_connection()
cart = conn.execute('SELECT * FROM cart').fetchall()

conn.close()
print(cart[0])
# for i in cart:      
#     print(i["product_id"])
#     print(i["product_name"])
#     print(i["product_price"])