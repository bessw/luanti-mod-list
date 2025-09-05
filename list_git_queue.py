import sqlite3

DB_PATH = 'git_queue.db'

def list_all_entries(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print(f'--- Table: git_repos ---')
    cursor.execute('SELECT * FROM git_repos')
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()

if __name__ == '__main__':
    list_all_entries(DB_PATH)
