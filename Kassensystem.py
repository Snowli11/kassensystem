import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
import fpdf as FPDF
from ttkthemes import ThemedTk
import os
import webbrowser
import subprocess
import platform

# Initialisierung des Hauptfensters
hauptfenster = ThemedTk(theme="black")
hauptfenster.title('Kassensystem')
hauptfenster.configure(background='black')  # Set the background color to black
hauptfenster.geometry('800x600')

style = ttk.Style()
style.configure("TButton", font=("Arial", 12), background="black", foreground="white")
style.configure("TListbox", font=("Arial", 12), background="black", foreground="white")

# Definition der globalen Variablen
gesamtsumme = 0.0
artikel_bereich = None
kassenliste = None
gesamtsumme_label = None
admin_window = None
items = {}

# Artikel aus der CSV-Datei laden
dateipfad = 'artikelliste.csv'
artikel_df = pd.read_csv(dateipfad)
artikel_db = {str(row['ArtikelID']).zfill(3): {'name': row['Artikelname'], 'price': row['Preis']} for index, row in
              artikel_df.iterrows()}


def artikel_buttons_hinzufuegen():
    global artikel_bereich
    for widget in artikel_bereich.winfo_children():
        widget.destroy()

    max_buttons_per_line = 5  # Maximale Anzahl von Buttons pro Zeile
    current_button_count = 0  # Aktuelle Anzahl von Buttons in der Zeile
    current_frame = None  # Aktueller Frame für die Buttons

    for item_code, item in artikel_db.items():
        # Erstelle einen neuen Frame, falls benötigt
        if current_button_count % max_buttons_per_line == 0:
            current_frame = tk.Frame(artikel_bereich)
            current_frame.pack(fill=tk.X)

        # Erstelle den Button und füge ihn zum aktuellen Frame hinzu
        button = ttk.Button(current_frame, text=f"{item['name']} - ${item['price']}",
                            command=lambda code=item_code: bei_artikel_button_klick(code), width=20, style="TButton")
        button.pack(side=tk.LEFT)

        # Erhöhe die Button-Anzahl
        current_button_count += 1


def bei_artikel_button_klick(item_code):
    global kassenliste
    menge = simpledialog.askinteger("Menge", f"Wie viele {artikel_db[item_code]['name']}?", minvalue=1,
                                    maxvalue=100)
    if menge is not None:
        scan_item(item_code, menge)


def delete_warenkorb(item_frame):
    global items
    # Hole den Artikeltext aus dem Frame
    item_text = item_frame.item_text

    # Überprüfe, ob der Artikel in der Liste ist
    if item_text in items:
        # Aktualisiere den Gesamtbetrag
        item_price = float(item_text.split(' - $')[1])
        update_gesamtsumme(-item_price)

        # Reduziere die Menge des Artikels
        items[item_text]['menge'] -= 1

        # Entferne den Frame aus der Liste der Frames für diesen Artikel
        items[item_text]['frames'].remove(item_frame)

        # Wenn die Menge des Artikels jetzt 0 ist, entferne den Artikel aus der Artikel-Liste
        if items[item_text]['menge'] == 0:
            del items[item_text]

        # Andernfalls aktualisiere das Label des ersten verbleibenden Frames für diesen Artikel
        elif items[item_text]['frames']:
            items[item_text]['frames'][0].winfo_children()[0].config(text=f"{items[item_text]['menge']}x {item_text}")

        # Entferne den Frame aus der Listbox
        item_frame.pack_forget()


def scan_item(item_code, menge=1):
    global gesamtsumme, kassenliste, gesamtsumme_label, items
    item = artikel_db.get(item_code)
    if item:
        gesamtsumme_price = item['price'] * menge  # Multipliziere den Preis mit der Menge
        item_text = f"{item['name']} - ${item['price']:.2f}"

        # Füge den Artikel zur Artikel-Liste hinzu oder erhöhe die Menge
        if item_text in items:
            items[item_text]['menge'] += menge
            # Aktualisiere das Label des ersten verbleibenden Frames für diesen Artikel
            items[item_text]['frames'][0].winfo_children()[0].config(
                text=f"{items[item_text]['menge']}x {item_text} - ${items[item_text]['menge'] * item['price']:.2f}")
        else:
            items[item_text] = {'menge': menge, 'frames': []}

            # Erstelle einen neuen Frame für den Listbox-Eintrag
            item_frame = tk.Frame(kassenliste)
            item_frame.pack(fill=tk.X)

            # Speichere den Artikelcode, die Menge und den Artikeltext als Attribute des Frames
            item_frame.item_code = item_code
            item_frame.quantity = menge
            item_frame.item_text = item_text  # Speichere den Artikeltext

            # Erstelle das Artikel-Label und füge es zum Frame hinzu
            item_label = tk.Label(item_frame,
                                  text=f"{items[item_text]['menge']}x {item_text} - ${gesamtsumme_price:.2f}")
            item_label.pack(side=tk.LEFT)

            # Erstelle den Löschen-Button und füge ihn zum Frame hinzu
            delete_button = tk.Button(item_frame, text='X', command=lambda: delete_warenkorb(item_frame))
            delete_button.pack(side=tk.RIGHT)

            # Füge den Frame zur Liste der Frames für diesen Artikel hinzu
            items[item_text]['frames'].append(item_frame)

        update_gesamtsumme(gesamtsumme_price)
    else:
        messagebox.showerror("Fehler", "Artikel nicht gefunden")


def update_gesamtsumme(amount):
    global gesamtsumme, gesamtsumme_label
    gesamtsumme += amount
    gesamtsumme_label.config(text=f'Total: ${gesamtsumme:.2f}')


def checkout():
    global gesamtsumme, kassenliste, gesamtsumme_label, items
    messagebox.showinfo("Bezahlen", f"Dein total ist {gesamtsumme_label.cget('text')}")

    # Lösche den alten Kassenzettel
    if os.path.exists("Kassenzettel.pdf"):
        os.remove("Kassenzettel.pdf")

    # Erstelle eine Liste von Artikeln
    items_list = []
    for item_text, item_info in items.items():
        item_name, item_price = item_text.rsplit(' - $', 1)
        total_price = float(item_price) * item_info['menge']
        items_list.append(
            f"{item_info['menge']}x {item_name} - ${total_price:.2f}")  # Füge die Menge und den Gesamtpreis vor dem Artikeltext hinzu

    kassenzettel(items_list)

    # Zerstöre alle Frames in der Listbox
    for frame in kassenliste.winfo_children():
        frame.destroy()

    gesamtsumme_label.config(text='Total: $0.00')
    gesamtsumme = 0
    items = {}  # Setze die items-Datenstruktur zurück

    pdf_filename = "Kassenzettel.pdf"
    pdf_path = os.path.abspath(pdf_filename)

    if os.path.exists("Kassenzettel.pdf"):
        if platform.system() == 'Windows':
            webbrowser.open_new("Kassenzettel.pdf")
        elif platform.system() == 'Linux':
            subprocess.run(['mupdf', pdf_path], check=True)
        else:
            raise Exception('Platform nicht unterstützt')


def kassenzettel(kassenzettelliste):
    pdf = FPDF.FPDF(format='A4')
    pdf.add_page()
    pdf.set_font("Courier", size=12)

    # Logo
    pdf.image('Coop_einfach_in_besser.png', x=10, y=8, w=30)

    # Titel
    pdf.cell(200, 10, txt="Kassenzettel", ln=True, align='C')

    # Einzelne Artikel
    for item in kassenzettelliste:
        item_description, item_price = item.rsplit(' - $', 1)
        pdf.cell(150, 10, txt=item_description, align='L')
        pdf.cell(50, 10, txt='$' + item_price, ln=True, align='R')

    # Leere Zeile
    pdf.cell(200, 10, txt='', ln=True)

    # Gesamtsumme
    pdf.cell(200, 10, txt=f'Total: ${gesamtsumme:.2f}', align='R')

    pdf.output("Kassenzettel.pdf")


def psswd_test():
    versuche = 0
    anzahl_versuche = 3
    korrekt_passwd = os.getenv("admin_passwort")
    for i in range(anzahl_versuche):
        if versuche <= anzahl_versuche:
            psswd = simpledialog.askstring("Passwort", "Passwort eingeben", show="*")
            if psswd == korrekt_passwd:
                return True
            else:
                messagebox.showerror("Fehler", "Falsches Passwort")
                versuche += 1
                print(versuche)
    if versuche >= anzahl_versuche:
        webbrowser.open_new("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        exit()


def admin_ja_nein():
    if messagebox.askyesno("Admin", "Admin Panel öffnen?"):
        return True
    else:
        return False


def open_admin():
    global admin_window, delete_dropdown, selected_item_name  # Deklariere delete_dropdown und selected_item_name als global
    if admin_window is None or not tk.Toplevel.winfo_exists(admin_window):
        admin_window = tk.Toplevel(hauptfenster)
        admin_window.title('Admin Panel')

    # Artikel hinzufügen Bereich
    add_name_label = tk.Label(admin_window, text='Name')
    add_name_label.pack()
    add_name_entry = tk.Entry(admin_window)
    add_name_entry.pack()

    add_price_label = tk.Label(admin_window, text='Preis')
    add_price_label.pack()
    add_price_entry = tk.Entry(admin_window)
    add_price_entry.pack()

    add_button = tk.Button(admin_window, text='Artikel hinzufügen',
                           command=lambda: add_item(add_name_entry.get(), add_price_entry.get()))
    add_button.pack()

    # Artikel löschen Bereich
    delete_label = tk.Label(admin_window, text='Wähle einen Artikel zum Löschen')
    delete_label.pack()

    # Erstelle eine Liste von Artikelnamen
    item_names = [item['name'] for item in artikel_db.values()]

    # Erstelle ein StringVar-Objekt, um den ausgewählten Artikelnamen zu speichern
    selected_item_name = tk.StringVar(admin_window)
    if item_names:
        selected_item_name.set(item_names[0])  # Setze den Standardwert auf den ersten Artikelnamen

    # Erstelle das Dropdown-Menü
    delete_dropdown = tk.OptionMenu(admin_window, selected_item_name, *item_names)
    delete_dropdown.pack()

    delete_button = tk.Button(admin_window, text='Artikel löschen',
                              command=lambda: delete_item_by_name(selected_item_name.get()))
    delete_button.pack()


def delete_item_by_name(item_name):
    # Finde den Artikelcode, der zum Artikelnamen gehört
    item_code = next((code for code, item in artikel_db.items() if item['name'] == item_name), None)

    if item_code:
        delete_item(item_code)
    else:
        messagebox.showerror("Fehler", "Artikel nicht gefunden")


def add_item(name, price_entry):
    global delete_dropdown, selected_item_name  # Deklariere delete_dropdown und selected_item_name als global
    try:
        price = float(price_entry)  # Versuche, den Preis in eine Gleitkommazahl umzuwandeln
        item_code = str(max([int(code) for code in artikel_db.keys()], default=0) + 1).zfill(
            3)  # Generiere einen neuen Artikelcode
        artikel_db[item_code] = {'name': name, 'price': price}  # Füge den neuen Artikel zur artikel_db hinzu
        messagebox.showinfo("Erfolg",
                            f"Artikel {name} mit Preis ${price:.2f} hinzugefügt")  # Zeige eine Nachricht an, dass der Artikel erfolgreich hinzugefügt wurde
        save_items_to_csv()  # Speichere die artikel_db in der CSV-Datei
        artikel_buttons_hinzufuegen()  # Aktualisiere die Artikel-Buttons

        # Aktualisiere das Dropdown-Menü
        item_names = [item['name'] for item in artikel_db.values()]  # Erstelle eine Liste von Artikelnamen
        delete_dropdown['menu'].delete(0, 'end')  # Lösche alle Einträge im Dropdown-Menü
        for item_name in item_names:  # Füge jeden Artikelnamen zum Dropdown-Menü hinzu
            delete_dropdown['menu'].add_command(label=item_name, command=tk._setit(selected_item_name, item_name))

    except ValueError:  # Falls der Preis nicht in eine Gleitkommazahl umgewandelt werden kann
        messagebox.showerror("Fehler", "Ungültiger Preis")  # Zeige eine Fehlermeldung an


def delete_item(item_code):
    global artikel_db, delete_dropdown, selected_item_name  # Deklariere delete_dropdown und selected_item_name als global
    item_code = item_code.zfill(3)  # Fülle den Artikelcode mit führenden Nullen auf, bis er drei Stellen hat
    if item_code in artikel_db:  # Überprüfe, ob der Artikelcode in der artikel_db vorhanden ist
        del artikel_db[item_code]  # Lösche den Artikel aus der artikel_db
        reassign_ids()  # Weise die IDs neu zu
        save_items_to_csv()  # Speichere die artikel_db in der CSV-Datei
        artikel_buttons_hinzufuegen()  # Aktualisiere die Artikel-Buttons
        messagebox.showinfo("Erfolg",
                            "Artikel gelöscht")  # Zeige eine Nachricht an, dass der Artikel erfolgreich gelöscht wurde

        # Aktualisiere das Dropdown-Menü
        item_names = [item['name'] for item in artikel_db.values()]  # Erstelle eine Liste von Artikelnamen
        delete_dropdown['menu'].delete(0, 'end')  # Lösche alle Einträge im Dropdown-Menü
        for item_name in item_names:  # Füge jeden Artikelnamen zum Dropdown-Menü hinzu
            delete_dropdown['menu'].add_command(label=item_name, command=tk._setit(selected_item_name, item_name))
    else:
        messagebox.showerror("Fehler",
                             "Artikel nicht gefunden")  # Zeige eine Fehlermeldung an, wenn der Artikel nicht gefunden wurde


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


# GUI-Layout
kassenliste = tk.Listbox(hauptfenster, font=("Arial", 12), background="black",
                         foreground="white")  # Verwende die Listbox-Klasse von tkinter
kassenliste.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

checkout_button = ttk.Button(hauptfenster, text='Checkout', command=checkout)  # Verwende ttk.Button
checkout_button.pack(side=tk.BOTTOM, fill=tk.X)

gesamtsumme_label = ttk.Label(hauptfenster, text='Total: $0.00')  # Verwende ttk.Label
gesamtsumme_label.pack(side=tk.BOTTOM, fill=tk.X)

artikel_bereich = ttk.Frame(hauptfenster)  # Verwende ttk.Frame
artikel_bereich.pack(side=tk.TOP, fill=tk.X)
artikel_buttons_hinzufuegen()

if admin_ja_nein() and psswd_test():
    admin_button = ttk.Button(hauptfenster, text='Admin', command=open_admin)  # Verwende ttk.Button
    admin_button.pack(side=tk.BOTTOM, fill=tk.X)

# Starte die GUI
hauptfenster.mainloop()
