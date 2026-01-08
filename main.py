
from fastmcp import FastMCP
import os
import aiosqlite
import tempfile
import sqlite3
import json

temp_dir = tempfile.gettempdir()
DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("ExpenseTracker")

def init_db():
    try:
        with sqlite3.connect(DB_PATH) as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
                )
        """ )
            print("Database initialized successfully with write access")
    except Exception as e:
        print(f"Database initialization error:{e}")
        raise

init_db()

@mcp.tool()
async def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    '''Add a new expense entry to the database.'''
    try:
        
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (date, amount, category, subcategory, note)
            )
            expense_id = cur.lastrowid
            await c.commit()
            return {"status": "Success", "id": expense_id, "message": "Expense Added Successfully"}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"Database Error: {str(e)}"}


@mcp.tool()
async def list_expenses(start_date, end_date):
    '''List expense entries within an inclusive date range.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """,
            (start_date, end_date)
            )
            rows = await cur.fetchall()  # ✅ CORRECT - inside the async with block
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]
    except Exception as e:
        return {"status": "error", "message": f"Error listing Expense {str(e)}"}

@mcp.tool()
async def summarize(start_date, end_date, category=None):
    '''Summarize expenses by category within an inclusive date range.'''
    async with aiosqlite.connect(DB_PATH) as c:
        query = (
            """
            SELECT category, SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
            """
        )
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY category ASC"

        cur = await c.execute(query, params)
        rows = await cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]
    
@mcp.tool()
async def delete_expenses(date, amount, category, subcategory="", note=""):
    """Delete an expense entry if it was wrongly entered"""
    async with aiosqlite.connect(DB_PATH) as c:
        cur = await c.execute(
            """
            DELETE FROM expenses
            WHERE date = ?
              AND amount = ?
              AND category = ?
              AND subcategory = ?
              AND note = ?
            """,
            (date, amount, category, subcategory, note)
        )
        await c.commit()
    return {"status": "ok", "rows_deleted": await cur.rowcount}

@mcp.tool()
async def update(id, date, amount, category, subcategory ="", note=""):
    """ Edit the entry which one wrongly updated"""
    async with aiosqlite.connect(DB_PATH) as c:
        fields= []
        values= []
        if date:
            fields.append("date = ?")
            values.append(date)
        if amount:
            fields.append("amount = ?")
            values.append(amount)
        if category:
            fields.append("category = ?")
            values.append(category)
        if subcategory is not None:
            fields.append("subcategory = ?")
            values.append(subcategory)
        if note is not None:
            fields.append("note = ?")
            values.append(note)
        values.append(id)   

        # No field passed no update needed
        if not fields:
            return {"status": "no update", "id": id}
        query = f"UPDATE expenses SET {', '.join(fields)} WHERE id = ?"
        cur = await c.execute(query, values)
        await c.commit()
    return {"status": "ok", "id": id, "rows_updated": await cur.rowcount}


@mcp.resource("expense://categories", mime_type="application/json")
async def categories():
    # Read fresh each time so you can edit the file without restarting
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()

# Start the server
#if __name__ == "__main__":
   # mcp.run(transport="http", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8000
    )
