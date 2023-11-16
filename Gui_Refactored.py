import tkinter as tk
from tkinter import messagebox, simpledialog
import pandas as pd
import fpdf as FPDF

# Initialisierung des Hauptfensters
hauptfenster = tk.Tk()
hauptfenster.title('Kassensystem')

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
    for item_code, item in artikel_db.items():
        button = tk.Button(artikel_bereich, text=f"{item['name']} - ${item['price']}",
                           command=lambda code=item_code: bei_artikel_button_klick(code))
        button.pack(side=tk.LEFT)


def bei_artikel_button_klick(item_code):
    global kassenliste
    menge = simpledialog.askinteger("Menge", f"Wie viele {artikel_db[item_code]['name']}?", minvalue=1,
                                    maxvalue=100)
    if menge is not None:
        scan_item(item_code, menge)


def scan_item(item_code, menge=1):
    global gesamtsumme, kassenliste, gesamtsumme_label
    item = artikel_db.get(item_code)
    if item:
        gesamtsumme_price = item['price'] * menge
        kassenliste.insert(tk.END, f"{menge}x {item['name']} - ${gesamtsumme_price:.2f}")
        print(kassenliste)
        update_gesamtsumme(gesamtsumme_price)
    else:
        messagebox.showerror("Error", "Item not found")


def update_gesamtsumme(amount):
    global gesamtsumme, gesamtsumme_label
    gesamtsumme += amount
    gesamtsumme_label.config(text=f'Total: ${gesamtsumme:.2f}')


def kassenzettel(kassenzettelliste):
    print(kassenzettelliste)
    #pdf = FPDF.FPDF(format='letter')
    #pdf.add_page()
    #pdf.set_font("Arial", size=12)
    #pdf.cell(200, 10, txt=kassenzettelliste,
    #         ln=1, align='C')
    #pdf.output("Kassenzettel.pdf")


def checkout():
    global gesamtsumme, kassenliste, gesamtsumme_label
    messagebox.showinfo("Checkout", f"Your gesamtsumme is {gesamtsumme_label.cget('text')}")
    kassenzettel(kassenliste)
    kassenliste.delete(0, tk.END)
    gesamtsumme_label.config(text='Total: $0.00')
    gesamtsumme = 0


def open_admin():
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
    delete_label = tk.Label(admin_window, text='Enter item code to delete')
    delete_label.pack()
    delete_entry = tk.Entry(admin_window)
    delete_entry.pack()

    delete_button = tk.Button(admin_window, text='Delete Item', command=lambda: delete_item(delete_entry.get()))
    delete_button.pack()


def add_item(name, price_entry):
    try:
        price = float(price_entry)
        item_code = str(max([int(code) for code in artikel_db.keys()], default=0) + 1).zfill(3)
        artikel_db[item_code] = {'name': name, 'price': price}
        messagebox.showinfo("Success", f"Added {name} with price ${price:.2f}")
        save_items_to_csv()
        artikel_buttons_hinzufuegen()
    except ValueError:
        messagebox.showerror("Error", "Invalid price")


def delete_item(item_code):
    global artikel_db
    item_code = item_code.zfill(3)
    if item_code in artikel_db:
        del artikel_db[item_code]
        reassign_ids()
        save_items_to_csv()
        artikel_buttons_hinzufuegen()
        messagebox.showinfo("Success", "Item deleted")
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
kassenliste = tk.Listbox(hauptfenster)
kassenliste.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

checkout_button = tk.Button(hauptfenster, text='Checkout', command=checkout)
checkout_button.pack(side=tk.BOTTOM, fill=tk.X)

# noinspection PyRedeclaration,SpellCheckingInspection
gesamtsumme_label = tk.Label(hauptfenster, text='Total: $0.00')
gesamtsumme_label.pack(side=tk.BOTTOM, fill=tk.X)

# noinspection PyRedeclaration,SpellCheckingInspection
artikel_bereich = tk.Frame(hauptfenster)
artikel_bereich.pack(side=tk.TOP, fill=tk.X)
artikel_buttons_hinzufuegen()

admin_button = tk.Button(hauptfenster, text='Admin', command=open_admin)
admin_button.pack(side=tk.BOTTOM, fill=tk.X)

# Starten der GUI
hauptfenster.mainloop()
