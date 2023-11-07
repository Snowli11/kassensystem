import tkinter as tk
from tkinter import messagebox, simpledialog
import pandas as pd

# Initialize the main application window
root = tk.Tk()
root.title('Self Checkout Register')

# Initialize global variables
total = 0.0
items_frame = None
checkout_list = None
total_label = None

# Load items from CSV file into a dictionary
file_path = 'artikelliste.csv'
items_df = pd.read_csv(file_path)
items_db = {str(row['ArtikelID']).zfill(3): {'name': row['Artikelname'], 'price': row['Preis']} for index, row in items_df.iterrows()}

def add_item_buttons():
    global items_frame
    for widget in items_frame.winfo_children():
        widget.destroy()
    for item_code, item in items_db.items():
        button = tk.Button(items_frame, text=f"{item['name']} - ${item['price']}",
                           command=lambda code=item_code: on_item_button_click(code))
        button.pack(side=tk.LEFT)

def on_item_button_click(item_code):
    global checkout_list
    quantity = simpledialog.askinteger("Quantity", f"How many {items_db[item_code]['name']}s?", minvalue=1, maxvalue=100)
    if quantity is not None:
        scan_item(item_code, quantity)

def scan_item(item_code, quantity=1):
    global total, checkout_list, total_label
    item = items_db.get(item_code)
    if item:
        total_price = item['price'] * quantity
        checkout_list.insert(tk.END, f"{quantity}x {item['name']} - ${total_price:.2f}")
        update_total(total_price)
    else:
        messagebox.showerror("Error", "Item not found")

def update_total(amount):
    global total, total_label
    total += amount
    total_label.config(text=f'Total: ${total:.2f}')

def checkout():
    global total, checkout_list, total_label
    messagebox.showinfo("Checkout", f"Your total is {total_label.cget('text')}")
    checkout_list.delete(0, tk.END)
    total_label.config(text='Total: $0.00')
    total = 0

def open_admin():
    admin_window = tk.Toplevel(root)
    admin_window.title('Admin Panel')

    # Add Item section
    add_name_label = tk.Label(admin_window, text='Name')
    add_name_label.pack()
    add_name_entry = tk.Entry(admin_window)
    add_name_entry.pack()

    add_price_label = tk.Label(admin_window, text='Price')
    add_price_label.pack()
    add_price_entry = tk.Entry(admin_window)
    add_price_entry.pack()

    add_button = tk.Button(admin_window, text='Add Item', command=lambda: add_item(add_name_entry.get(), add_price_entry.get()))
    add_button.pack()

    # Delete Item section
    delete_label = tk.Label(admin_window, text='Enter item code to delete')
    delete_label.pack()
    delete_entry = tk.Entry(admin_window)
    delete_entry.pack()

    delete_button = tk.Button(admin_window, text='Delete Item', command=lambda: delete_item(delete_entry.get()))
    delete_button.pack()

def add_item(name, price_entry):
    try:
        price = float(price_entry)
        item_code = str(max([int(code) for code in items_db.keys()], default=0) + 1).zfill(3)
        items_db[item_code] = {'name': name, 'price': price}
        messagebox.showinfo("Success", f"Added {name} with price ${price:.2f}")
        save_items_to_csv()
        add_item_buttons()
    except ValueError:
        messagebox.showerror("Error", "Invalid price")

def delete_item(item_code):
    global items_db
    item_code = item_code.zfill(3)
    if item_code in items_db:
        del items_db[item_code]
        reassign_ids()
        save_items_to_csv()
        add_item_buttons()
        messagebox.showinfo("Success", "Item deleted")
    else:
        messagebox.showerror("Error", "Item not found")

def reassign_ids():
    global items_db
    new_items_db = {}
    for new_id, code in enumerate(sorted(items_db, key=int), start=1):
        new_items_db[str(new_id).zfill(3)] = items_db[code]
    items_db = new_items_db

def save_items_to_csv():
    new_df = pd.DataFrame.from_dict({
        'ArtikelID': [int(code) for code in items_db.keys()],
        'Artikelname': [item['name'] for item in items_db.values()],
        'Preis': [item['price'] for item in items_db.values()]
    })
    new_df.sort_values(by='ArtikelID', inplace=True)
    new_df.to_csv(file_path, index=False)

# GUI Layout
checkout_list = tk.Listbox(root)
checkout_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

checkout_button = tk.Button(root, text='Checkout', command=checkout)
checkout_button.pack(side=tk.BOTTOM, fill=tk.X)

total_label = tk.Label(root, text='Total: $0.00')
total_label.pack(side=tk.BOTTOM, fill=tk.X)

items_frame = tk.Frame(root)
items_frame.pack(side=tk.TOP, fill=tk.X)
add_item_buttons()

admin_button = tk.Button(root, text='Admin', command=open_admin)
admin_button.pack(side=tk.BOTTOM, fill=tk.X)

# Start the application
root.mainloop()

