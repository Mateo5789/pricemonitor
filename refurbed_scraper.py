import requests
from bs4 import BeautifulSoup
import re
import csv
import os
from datetime import datetime


URL = "https://www.refurbed.pl/p/iphone-13/14165b/?offer=17263393"
PLIK_CSV = "refurbed_prices.csv"


def wyczysc_cene(cena_tekst):
    if not cena_tekst:
        return ""

    cena_tekst = cena_tekst.replace("zł", "")
    cena_tekst = cena_tekst.replace(" ", "")
    cena_tekst = cena_tekst.replace("\xa0", "")
    cena_tekst = cena_tekst.replace(",", ".")

    return float(cena_tekst)


def pobierz_strone(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=15)
    print("Status strony:", response.status_code)

    if response.status_code != 200:
        raise Exception("Nie udało się pobrać strony")

    return response.text


def pobierz_glowny_produkt(soup, tekst):
    naglowek = soup.find("h1")
    model = naglowek.get_text(" ", strip=True) if naglowek else "iPhone 13"

    ceny = re.findall(r"\d+\s\d+,\d{2}\s*zł", tekst)

    ceny_liczbowe = []

    for cena_tekst in ceny:
        cena_float = wyczysc_cene(cena_tekst)

        if 500 <= cena_float <= 5000:
            ceny_liczbowe.append((cena_float, cena_tekst))

    cena = min(ceny_liczbowe)[1] if ceny_liczbowe else None
    cena_liczbowo = wyczysc_cene(cena) if cena else ""

    dostepnosc = "W magazynie" if "W magazynie" in tekst else "Brak danych"

    return {
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "typ": "glowny_produkt",
        "model": model,
        "kolor": "do_odczytania",
        "pamiec": "do_odczytania",
        "stan": "do_odczytania",
        "cena": cena,
        "cena_liczbowo": cena_liczbowo,
        "dostepnosc": dostepnosc,
        "url": URL
    }


def pobierz_sugerowane_konfiguracje(tekst):
    wyniki = []

    wzor = re.compile(
        r"([A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻż ]+)\s+"
        r"(\d+\sGB)\s+"
        r"(Dobry|Bardzo dobry|Jak nowy|Premium)\s+"
        r"(\d+\s\d+,\d{2}\s*zł)"
    )

    dopasowania = wzor.findall(tekst)

    for kolor, pamiec, stan, cena in dopasowania:
        wyniki.append({
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "typ": "sugerowana_konfiguracja",
            "model": "iPhone 13",
            "kolor": kolor.strip(),
            "pamiec": pamiec.strip(),
            "stan": stan.strip(),
            "cena": cena.strip(),
            "cena_liczbowo": wyczysc_cene(cena),
            "dostepnosc": "sugerowana konfiguracja",
            "url": URL
        })

    return wyniki


def pobierz_poprzedni_pomiar(nazwa_pliku=PLIK_CSV):
    if not os.path.exists(nazwa_pliku):
        return None

    with open(nazwa_pliku, "r", encoding="utf-8-sig", newline="") as plik:
        reader = csv.DictReader(plik)
        wiersze = list(reader)

    # Bierzemy tylko główny produkt, nie sugerowane konfiguracje
    glowne_pomiary = [
        wiersz for wiersz in wiersze
        if wiersz.get("typ") == "glowny_produkt" and wiersz.get("cena_liczbowo")
    ]

    if not glowne_pomiary:
        return None

    return glowne_pomiary[-1]


def pokaz_porownanie(aktualny_pomiar, poprzedni_pomiar):
    aktualna_cena = aktualny_pomiar["cena_liczbowo"]

    print("\n--- PORÓWNANIE CENY ---")
    print(f"Aktualna cena: {aktualna_cena} zł")

    if poprzedni_pomiar is None:
        print("Brak poprzedniego pomiaru.")
        print("To jest pierwszy zapis ceny.")
        return

    poprzednia_cena = float(poprzedni_pomiar["cena_liczbowo"])
    poprzednia_data = poprzedni_pomiar["data"]

    roznica = round(aktualna_cena - poprzednia_cena, 2)

    print(f"Poprzednia cena: {poprzednia_cena} zł")
    print(f"Poprzedni pomiar: {poprzednia_data}")
    print(f"Zmiana: {roznica} zł")

    if roznica < 0:
        print("Cena spadła ✅")
    elif roznica > 0:
        print("Cena wzrosła ⚠️")
    else:
        print("Cena bez zmian ➖")


def zapisz_do_csv(wiersze, nazwa_pliku=PLIK_CSV):
    pola = [
        "data",
        "typ",
        "model",
        "kolor",
        "pamiec",
        "stan",
        "cena",
        "cena_liczbowo",
        "dostepnosc",
        "url"
    ]

    with open(nazwa_pliku, "a", newline="", encoding="utf-8-sig") as plik:
        writer = csv.DictWriter(plik, fieldnames=pola)

        if plik.tell() == 0:
            writer.writeheader()

        writer.writerows(wiersze)


html = pobierz_strone(URL)

soup = BeautifulSoup(html, "html.parser")
tekst = soup.get_text("\n", strip=True)

glowny = pobierz_glowny_produkt(soup, tekst)
sugerowane = pobierz_sugerowane_konfiguracje(tekst)

poprzedni_pomiar = pobierz_poprzedni_pomiar()
pokaz_porownanie(glowny, poprzedni_pomiar)

wszystkie_wiersze = [glowny] + sugerowane

print("\n--- ZAPISYWANE WIERSZE ---")
for wiersz in wszystkie_wiersze:
    print(wiersz)

zapisz_do_csv(wszystkie_wiersze)

print("\nZapisano dane do refurbed_prices.csv")