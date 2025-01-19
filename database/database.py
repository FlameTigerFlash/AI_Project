import aiosqlite


async def start_db():
    async with aiosqlite.connect('users.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER,
                name VARCHAR(30),
                completed INTEGER,
                failed INTEGER
            )
        ''')
        await db.execute('''
             CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                director_id INTEGER,
                name VARCHAR(255),
                team VARCHAR(30),
                executors TEXT,
                description TEXT,
                status VARCHAR(30),
                FOREIGN KEY (director_id) REFERENCES user(id) ON DELETE CASCADE
            )
        ''')
        await db.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(30),
                    password VARCHAR(30)
                )
        ''')
        await db.execute('''
                CREATE TABLE IF NOT EXISTS user_tasks (
                    user_id INTEGER,
                    role TEXT,
                    task_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
        ''')
        await db.execute('''
                CREATE TABLE IF NOT EXISTS review (
                    user_id INTEGER,
                    comment TEXT,
                    task_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
        ''')
        await db.execute('''
                CREATE TABLE IF NOT EXISTS communication (
                    task_id INTEGER,
                    type VARCHAR(30),
                    body TEXT,
                    resolved BOOLEAN,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
                ''')
        await db.execute('''
                CREATE TABLE IF NOT EXISTS completion_log (
                    task_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                    );
        ''')
        await db.execute('''
                CREATE TABLE IF NOT EXISTS command_log (
                    user_id INTEGER NOT NULL,
                    command VARCHAR(255) NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
        ''')
        await db.commit()


async def db_get_items(table: str, **kwargs) -> list:
    async with aiosqlite.connect('users.db') as db:
        req = f"SELECT * FROM {table}"
        params = []
        if kwargs:
            req += " WHERE"
            conditions = []
            for i, (key, value) in enumerate(kwargs.items()):
                if i > 0:
                    conditions.append(" AND")
                conditions.append(f" {key} = ?")
                params.append(value)
            req += ''.join(conditions)
        async with db.execute(req, params) as cursor:
            rows = await cursor.fetchall()
            return rows


async def db_element_exists(table: str, **kwargs) -> bool:
    async with aiosqlite.connect('users.db') as db:
        req = f"SELECT * FROM {table}" + (" WHERE" if len(kwargs) > 0 else "")
        params = []
        if kwargs:
            conditions = []
            for i, (key, value) in enumerate(kwargs.items()):
                if i > 0:
                    conditions.append(" AND")
                conditions.append(f" {key} = ?")
                params.append(value)
            req += ''.join(conditions)
        #print(req, params)
        async with db.execute(req, params) as cursor:
            rows = await cursor.fetchall()
            return len(rows) > 0


async def db_insert_element(table: str, **kwargs) -> None:
    if len(kwargs) == 0:
        return
    async with aiosqlite.connect('users.db') as db:
        columns = ", ".join(kwargs.keys())
        placeholders = ", ".join("?" for _ in kwargs)  # Количество ? соответствует количеству ключей
        req = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        #print(req, kwargs.values())
        await db.execute(req, tuple(kwargs.values()))
        await db.commit()


async def db_create_table(table:str, **kwargs)->None:
    async with aiosqlite.connect('users.db') as db:
        req = f'''
                    CREATE TABLE IF NOT EXISTS {table} ({", ".join([key + " " + kwargs[key] for key in kwargs.keys()])})
                '''
        #print(req.strip())
        await db.execute(req)
        await db.commit()


async def db_delete_element(table: str, **kwargs) -> None:
    if len(kwargs) == 0:
        return
    async with aiosqlite.connect('users.db') as db:
        req = f"DELETE FROM {table}"
        params = []
        if kwargs:
            req += " WHERE"
            conditions = []
            for i, (key, value) in enumerate(kwargs.items()):
                if i > 0:
                    conditions.append(" AND")
                conditions.append(f" {key} = ?")
                params.append(value)
            req += ''.join(conditions)
        await db.execute(req, params)
        await db.commit()


async def db_delete_table(table:str)->None:
    async with aiosqlite.connect('users.db') as db:
        await db.execute(f"DROP TABLE IF EXISTS {table}")
        await db.commit()


async def db_update_element(table: str, where: dict, **kwargs) -> None:
    if len(kwargs) == 0 or len(where) == 0:
        return
    async with aiosqlite.connect('users.db') as db:
        set_clause = ", ".join(f"{key} = ?" for key in kwargs)
        where_clause = " AND ".join(f"{key} = ?" for key in where)
        req = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        await db.execute(req, tuple(kwargs.values()) + tuple(where.values()))
        await db.commit()


async def db_get_task_employees(task_id: int) -> list:
    async with aiosqlite.connect('users.db') as db:
        query = ("""
            SELECT users.id, users.name, users.completed, users.failed, user_tasks.role, review.comment
            FROM tasks
            INNER JOIN user_tasks ON tasks.id = user_tasks.task_id
            INNER JOIN users ON user_tasks.user_id = users.id
            LEFT JOIN review ON review.task_id = tasks.id AND review.user_id = users.id
            WHERE tasks.id = ?
        """)
        async with db.execute(query, (task_id,)) as cursor:
            rows = await cursor.fetchall()
            return rows


async def db_get_employee_tasks(user_id:int) -> list:
    async with aiosqlite.connect('users.db') as db:
        query = ("""
            SELECT tasks.id, tasks.director_id, tasks.name, tasks.team, tasks.description, tasks.status, user_tasks.role
            FROM tasks
            INNER JOIN user_tasks ON tasks.id = user_tasks.task_id
            INNER JOIN users ON user_tasks.user_id = users.id
            WHERE users.id = ?
        """)
        async with db.execute(query, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return rows


async def db_finish_task(task_id: int, success: bool) -> None:
    async with aiosqlite.connect('users.db') as db:
        if success:
            query = """
                UPDATE users
                SET completed = completed + 1
                WHERE id IN (
                    SELECT user_id FROM user_tasks WHERE task_id = ?
                )
            """
        else:
            query = """
                UPDATE users
                SET failed = failed + 1
                WHERE id IN (
                    SELECT user_id FROM user_tasks WHERE task_id = ?
                )
            """

        await db.execute(query, (task_id,))
        await db.commit()


async def db_get_notifications(user_id:int):
    async with aiosqlite.connect('users.db') as db:
        rows = []
        query = ("""
                    SELECT tasks.id, tasks.name, communication.type, communication.body
                    FROM tasks
                    INNER JOIN user_tasks ON tasks.id = user_tasks.task_id
                    INNER JOIN communication ON tasks.id = communication.task_id
                    WHERE user_tasks.user_id = ? AND user_tasks.role = 'Директор' AND communication.type = 'Ответ' AND communication.resolved = 'FALSE'
                """)
        async with db.execute(query, (user_id,)) as cursor:
            managers_answers = await cursor.fetchall()
            rows.extend(managers_answers)
        query = ("""
                    SELECT tasks.id, tasks.name, communication.type, communication.body
                    FROM tasks
                    INNER JOIN user_tasks ON tasks.id = user_tasks.task_id
                    INNER JOIN communication ON tasks.id = communication.task_id
                    WHERE user_tasks.user_id = ? AND user_tasks.role = 'Менеджер' AND communication.type = 'Запрос' AND communication.resolved = 'FALSE'
                """)
        async with db.execute(query, (user_id,)) as cursor:
            directors_requests = await cursor.fetchall()
            rows.extend(directors_requests)
        query = ("""
                    SELECT tasks.id, tasks.name, communication.type, communication.body
                    FROM tasks
                    INNER JOIN user_tasks ON tasks.id = user_tasks.task_id
                    INNER JOIN communication ON tasks.id = communication.task_id
                    WHERE user_tasks.user_id = ? AND user_tasks.role = 'Директор' AND communication.type = 'Запрос' AND communication.resolved = 'FALSE'
                """)
        async with db.execute(query, (user_id,)) as cursor:
            outcoming_requests = await cursor.fetchall()
            for i,el in enumerate(outcoming_requests):
                el = [el[j] if j != 2 else 'Исходящий' for j in range(len(el))]
                outcoming_requests[i] = el
            rows.extend(outcoming_requests)
        return rows


async def db_clear_notifications(user_id:int):
    async with aiosqlite.connect('users.db') as db:
        query = ("""
                    UPDATE communication 
                    SET resolved = 'TRUE' 
                    WHERE task_id IN (SELECT task_id FROM user_tasks WHERE user_id = ? AND role = 'Менеджер')
                """)
        await db.execute(query, (user_id,))
        await db.commit()
