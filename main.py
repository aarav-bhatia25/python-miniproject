import sqlite3
import tkinter as tk
from tkinter import messagebox

from database import open_database
from dashboard import Dashboard


def main():
    root = tk.Tk()
    root.withdraw()
    try:
        connection = open_database()
    except (sqlite3.Error, OSError) as error:
        messagebox.showerror("Database error", str(error), parent=root)
        root.destroy()
        return

    try:
        Dashboard(root, connection)
        root.deiconify()
        root.mainloop()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
