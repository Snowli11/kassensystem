import pandas as pd


# Importing the dataset
def importer(filename):
    l_dataset = pd.read_csv(filename)
    l_dataset.set_index('ArtikelID', inplace=True)
    print(l_dataset)
    return l_dataset


# Get the price of an article
def get_price(datastructures, artikel_id):
    price = datastructures.loc[artikel_id, 'Preis']
    return price


# Get sum of all articles
def get_sum(einkaufsliste):
    einkaufssumme = 0

    return einkaufssumme


dataset = importer('artikelliste.csv')

print(get_price(dataset, 1))
