import sqlite3

conn = sqlite3.connect('data/meta/schedule.db')


def empty_schedule():
    query = 'delete from bus_schedule'
    c = conn.cursor()
    c.execute(query)
    conn.commit()
    # query = 'VACUUM'
    # c.execute(query)
    # conn.commit()
    conn.close()


if __name__ == '__main__':
    empty_schedule()
