import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
import fpdf as FPDF
from ttkthemes import ThemedTk

# Initialisierung des Hauptfensters
hauptfenster = ThemedTk(theme="black")
hauptfenster.title('Kassensystem')

style = ttk.Style()
style.configure("TButton", font=("Arial", 12), background="black", foreground="white")
style.configure("TListbox", font=("Arial", 12), background="black", foreground="white")

# Definition der globalen Variablen
gesamtsumme = 0.0
artikel_bereich = None
kassenliste = None
gesamtsumme_label = None

# Artikel aus der CSV-Datei laden
dateipfad = 'artikelliste.csv'
artikel_df = pd.read_csv(dateipfad)
artikel_db = {str(row['ArtikelID']).zfill(3): {'name': row['Artikelname'], 'price': row['Preis']} for index, row in
              artikel_df.iterrows()}

def artikel_buttons_hinzufuegen():
    global artikel_bereich
    for widget in artikel_bereich.winfo_children():
        widget.destroy()

    max_buttons_per_line = 5  # Maximum number of buttons per line
    current_button_count = 0  # Current number of buttons on the line
    current_frame = None  # Current frame for the buttons

    for item_code, item in artikel_db.items():
        # Create a new frame if needed
        if current_button_count % max_buttons_per_line == 0:
            current_frame = tk.Frame(artikel_bereich)
            current_frame.pack(fill=tk.X)

        # Create the button and add it to the current frame
        button = ttk.Button(current_frame, text=f"{item['name']} - ${item['price']}",
                            command=lambda code=item_code: bei_artikel_button_klick(code), width=20, style="TButton")
        button.pack(side=tk.LEFT)

        # Increment the button count
        current_button_count += 1


def bei_artikel_button_klick(item_code):
    global kassenliste
    menge = simpledialog.askinteger("Menge", f"Wie viele {artikel_db[item_code]['name']}?", minvalue=1,
                                    maxvalue=100)
    if menge is not None:
        scan_item(item_code, menge)

def delete_warenkorb(item_frame):
    # Retrieve the item code and quantity from the frame
    item_code = item_frame.item_code.zfill(3)
    quantity = item_frame.quantity

    # Get the item details from the artikel_db
    item = artikel_db.get(item_code)

    if item:
        # Calculate the total price of the item
        total_price = item['price'] * quantity

        # Check if the item is in the list
        if item_frame.winfo_ismapped():
            # Update the total
            update_gesamtsumme(-total_price)

    # Remove the frame from the listbox
    item_frame.pack_forget()

def scan_item(item_code, menge=1):
    global gesamtsumme, kassenliste, gesamtsumme_label
    item = artikel_db.get(item_code)
    if item:
        gesamtsumme_price = item['price'] * menge
        item_text = f"{menge}x {item['name']} - ${gesamtsumme_price:.2f}"

        # Create a new frame for the listbox entry
        item_frame = tk.Frame(kassenliste)
        item_frame.pack(fill=tk.X)

        # Store the item code and quantity as attributes of the frame
        item_frame.item_code = item_code
        item_frame.quantity = menge

        # Create the item label and add it to the frame
        item_label = tk.Label(item_frame, text=item_text)
        item_label.pack(side=tk.LEFT)

        # Create the delete button and add it to the frame
        delete_button = tk.Button(item_frame, text='X', command=lambda: delete_warenkorb(item_frame))
        delete_button.pack(side=tk.RIGHT)

        update_gesamtsumme(gesamtsumme_price)
    else:
        messagebox.showerror("Error", "Item not found")

def update_gesamtsumme(amount):
    global gesamtsumme, gesamtsumme_label
    gesamtsumme += amount
    gesamtsumme_label.config(text=f'Total: ${gesamtsumme:.2f}')


def kassenzettel(kassenzettelliste):
    pdf = FPDF.FPDF(format='letter')
    pdf.add_page()
    pdf.set_font("Courier", size=12)

    # Logo
    pdf.image('Coop_einfach_in_besser.png', x=10, y=8, w=30)  # Adjust x, y, w as needed

    # Titel
    pdf.cell(200, 10, txt="Kassenzettel", ln=True, align='C')

    # Einzelne Artikel
    for item in kassenzettelliste.get(0, tk.END):
        item_description, item_price = item.rsplit(' - $', 1)
        pdf.cell(150, 10, txt=item_description, align='L')
        pdf.cell(50, 10, txt='$' + item_price, ln=True, align='R')

    # Leere Zeile
    pdf.cell(200, 10, txt='', ln=True)

    # Gesamtsumme
    pdf.cell(200, 10, txt=f'Total: ${gesamtsumme:.2f}', align='R')

    pdf.output("Kassenzettel.pdf")


def checkout():
    global gesamtsumme, kassenliste, gesamtsumme_label
    messagebox.showinfo("Bezahlen", f"Dein total ist {gesamtsumme_label.cget('text')}")
    kassenzettel(kassenliste)

    # Remove all frames from the listbox
    for frame in kassenliste.winfo_children():
        frame.pack_forget()

    gesamtsumme_label.config(text='Total: $0.00')
    gesamtsumme = 0


def open_admin():
    global delete_dropdown, selected_item_name  # Declare delete_dropdown and selected_item_name as global
    admin_window = tk.Toplevel(hauptfenster)
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

    add_button = tk.Button(admin_window, text='Add Item',
                           command=lambda: add_item(add_name_entry.get(), add_price_entry.get()))
    add_button.pack()

    # Delete Item section
    delete_label = tk.Label(admin_window, text='Select item to delete')
    delete_label.pack()

    # Create a list of item names
    item_names = [item['name'] for item in artikel_db.values()]

    # Create a StringVar object to hold the selected item name
    selected_item_name = tk.StringVar(admin_window)
    if item_names:
        selected_item_name.set(item_names[0])  # Set the default value to the first item name

    # Create the dropdown menu
    delete_dropdown = tk.OptionMenu(admin_window, selected_item_name, *item_names)
    delete_dropdown.pack()

    delete_button = tk.Button(admin_window, text='Delete Item',
                              command=lambda: delete_item_by_name(selected_item_name.get()))
    delete_button.pack()

def delete_item_by_name(item_name):
    # Find the item code that corresponds to the item name
    item_code = next((code for code, item in artikel_db.items() if item['name'] == item_name), None)

    if item_code:
        delete_item(item_code)
    else:
        messagebox.showerror("Error", "Item not found")

def add_item(name, price_entry):
    global delete_dropdown, selected_item_name  # Declare delete_dropdown and selected_item_name as global
    try:
        price = float(price_entry)
        item_code = str(max([int(code) for code in artikel_db.keys()], default=0) + 1).zfill(3)
        artikel_db[item_code] = {'name': name, 'price': price}
        messagebox.showinfo("Success", f"Added {name} with price ${price:.2f}")
        save_items_to_csv()
        artikel_buttons_hinzufuegen()

        # Update the dropdown menu
        item_names = [item['name'] for item in artikel_db.values()]
        delete_dropdown['menu'].delete(0, 'end')
        for item_name in item_names:
            delete_dropdown['menu'].add_command(label=item_name, command=tk._setit(selected_item_name, item_name))

    except ValueError:
        messagebox.showerror("Error", "Invalid price")


def delete_item(item_code):
    global artikel_db, delete_dropdown, selected_item_name  # Declare delete_dropdown and selected_item_name as global
    item_code = item_code.zfill(3)
    if item_code in artikel_db:
        del artikel_db[item_code]
        reassign_ids()
        save_items_to_csv()
        artikel_buttons_hinzufuegen()
        messagebox.showinfo("Success", "Item deleted")

        # Update the dropdown menu
        item_names = [item['name'] for item in artikel_db.values()]
        delete_dropdown['menu'].delete(0, 'end')
        for item_name in item_names:
            delete_dropdown['menu'].add_command(label=item_name, command=tk._setit(selected_item_name, item_name))
    else:
        messagebox.showerror("Error", "Item not found")


def reassign_ids():
    global artikel_db
    new_artikel_db = {}
    for new_id, code in enumerate(sorted(artikel_db, key=int), start=1):
        new_artikel_db[str(new_id).zfill(3)] = artikel_db[code]
    artikel_db = new_artikel_db


def save_items_to_csv():
    new_df = pd.DataFrame.from_dict({
        'ArtikelID': [int(code) for code in artikel_db.keys()],
        'Artikelname': [item['name'] for item in artikel_db.values()],
        'Preis': [item['price'] for item in artikel_db.values()]
    })
    new_df.sort_values(by='ArtikelID', inplace=True)
    new_df.to_csv(dateipfad, index=False)


# GUI Layout
# noinspection PyRedeclaration,SpellCheckingInspection
kassenliste = tk.Listbox(hauptfenster, font=("Arial", 12), background="black", foreground="white")  # Use the Listbox class from tkinter
kassenliste.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

checkout_button = ttk.Button(hauptfenster, text='Checkout', command=checkout)  # Use ttk.Button
checkout_button.pack(side=tk.BOTTOM, fill=tk.X)

gesamtsumme_label = ttk.Label(hauptfenster, text='Total: $0.00')  # Use ttk.Label
gesamtsumme_label.pack(side=tk.BOTTOM, fill=tk.X)

artikel_bereich = ttk.Frame(hauptfenster)  # Use ttk.Frame
artikel_bereich.pack(side=tk.TOP, fill=tk.X)
artikel_buttons_hinzufuegen()

admin_button = ttk.Button(hauptfenster, text='Admin', command=open_admin)  # Use ttk.Button
admin_button.pack(side=tk.BOTTOM, fill=tk.X)

# Start the GUI
hauptfenster.mainloop()
