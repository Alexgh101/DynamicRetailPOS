import tkinter
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
import mysql.connector
from datetime import datetime
import requests
from io import BytesIO
import threading

conn = mysql.connector.connect(host="50.6.18.240",
                                 user="ukjirumy_er_app",
                                 password="dbPa$$Capstone26",
                                 database="ukjirumy_ElevateRetail")

cursor = conn.cursor()

if (conn.is_connected()):
        print("Connection Successful!")
else:
        print("Connection Failed.")


def getProducts():
        cursor.execute(""" SELECT Product.Product_Name, Product.Product_Description, Product_Category.Category_Name, Inventory.Quantity, Inventory.Unit_Price, Product.Image_URL
        FROM Product
        INNER JOIN Inventory
        ON Product.Product_ID = Inventory.Product_ID
        INNER JOIN Product_Category
        ON Product.Category_ID = Product_Category.Category_ID 
        """)
        return cursor.fetchall()

inventory = getProducts()

def create_product_grid(parent, products):
    canvas = tkinter.Canvas(parent)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scroll_frame = ttk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e:canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left",fill="both", expand=True)
    scrollbar.pack(side="right",fill="y")

    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

    COLUMNS = 3

    for i, products in enumerate(products):
        row = i // COLUMNS
        col = i % COLUMNS

        card = ttk.Frame(scroll_frame, borderwidth=2, relief="groove", padding=10)
        card.grid(row=row, column=col,padx=10,pady=10)



        img_label = tkinter.Label(card, bg="lightgray", width=15, height=7)


        img_label.pack()

        load_Image_async(products[5], img_label)

        name_label = tkinter.Label(card, text=products[0], font=("Arial", 11, "bold"))
        name_label.pack(pady=(8,2))

        price_label = tkinter.Label(card, text=f"${products[4]:.2f}", foreground="green")
        price_label.pack()
def load_Image_async(url, label, size=(90,90)):
    def fetch():
        try:
            response = requests.get(url, timeout=5)
            img = Image.open(BytesIO(response.content)).resize(size)
            photo = ImageTk.PhotoImage(img)

            label.after(0, lambda: update_label(label, photo))
        except Exception as e:
            print(f"Failed to load image: {e}")
            return None
    threading.Thread(target=fetch, daemon=True).start()

def update_label(label, photo):
    label.config(image=photo)
    label.image = photo

root = Tk()
root.title=("Retail POS")
root.geometry("800x600")
create_product_grid(root, inventory)

root.mainloop()