import requests
from bs4 import BeautifulSoup
import re
import csv
import os
from datetime import datetime


URL = "https://www.refurbed.pl/p/iphone-13/14165b/?offer=17263393"
PLIK_CSV = "refurbed_prices.csv"
PROG_ALERTU = 1100


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


def dodaj_info_o_alercie(wiersz):
    cena = wiersz.get("cena_liczbowo")

    wiersz["prog_alertu"] = PROG_ALERTU

    if cena == "":
        wiersz["alert"] = "BRAK_CENY"
    elif cena < PROG_ALERTU:
        wiersz["alert"] = "TAK"
    else:
        wiersz["alert"] = "NIE"

    return wiersz


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

    wiersz = {
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

    return dodaj_info_o_alercie(wiersz)


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
        wiersz = {
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
        }

        wyniki.append(dodaj_info_o_alercie(wiersz))

    return wyniki


def zamien_date_na_obiekt(data_tekst):
    try:
        return datetime.strptime(data_tekst, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.min


def wczytaj_stare_wiersze(nazwa_pliku=PLIK_CSV):
    if not os.path.exists(nazwa_pliku):
        return []

    with open(nazwa_pliku, "r", encoding="utf-8-sig", newline="") as plik:
        reader = csv.DictReader(plik)
        return list(reader)


def pobierz_poprzedni_pomiar(nazwa_pliku=PLIK_CSV):
    stare_wiersze = wczytaj_stare_wiersze(nazwa_pliku)

    glowne_pomiary = [
        wiersz for wiersz in stare_wiersze
        if wiersz.get("typ") == "glowny_produkt" and wiersz.get("cena_liczbowo")
    ]

    if not glowne_pomiary:
        return None

    glowne_pomiary.sort(
        key=lambda wiersz: zamien_date_na_obiekt(wiersz.get("data", "")),
        reverse=True
    )

    return glowne_pomiary[0]


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


def sprawdz_alert_cenowy(aktualny_pomiar):
    cena = aktualny_pomiar.get("cena_liczbowo")
    alert = aktualny_pomiar.get("alert")

    print("\n--- ALERT CENOWY ---")
    print(f"Próg alertu: {PROG_ALERTU} zł")

    if cena == "":
        print("Brak ceny, nie można sprawdzić alertu.")
        return

    print(f"Aktualna cena: {cena} zł")
    print(f"Alert w CSV: {alert}")

    if alert == "TAK":
        print(f"🚨 ALERT: cena spadła poniżej {PROG_ALERTU} zł!")
        print(f"Produkt: {aktualny_pomiar.get('model')}")
        print(f"Cena: {aktualny_pomiar.get('cena')}")
        print(f"Link: {aktualny_pomiar.get('url')}")
    else:
        print("Cena nadal powyżej progu alertu.")


def zapisz_do_csv_najnowsze_na_gorze(nowe_wiersze, nazwa_pliku=PLIK_CSV):
    pola = [
        "data",
        "typ",
        "model",
        "kolor",
        "pamiec",
        "stan",
        "cena",
        "cena_liczbowo",
        "alert",
        "prog_alertu",
        "dostepnosc",
        "url"
    ]

    stare_wiersze = wczytaj_stare_wiersze(nazwa_pliku)

    wszystkie_wiersze = nowe_wiersze + stare_wiersze

    wszystkie_wiersze.sort(
        key=lambda wiersz: zamien_date_na_obiekt(wiersz.get("data", "")),
        reverse=True
    )

    with open(nazwa_pliku, "w", newline="", encoding="utf-8-sig") as plik:
        writer = csv.DictWriter(plik, fieldnames=pola)
        writer.writeheader()

        for wiersz in wszystkie_wiersze:
            poprawiony_wiersz = {}

            for pole in pola:
                poprawiony_wiersz[pole] = wiersz.get(pole, "")

            writer.writerow(poprawiony_wiersz)


html = pobierz_strone(URL)

soup = BeautifulSoup(html, "html.parser")
tekst = soup.get_text("\n", strip=True)

glowny = pobierz_glowny_produkt(soup, tekst)
sugerowane = pobierz_sugerowane_konfiguracje(tekst)

poprzedni_pomiar = pobierz_poprzedni_pomiar()
pokaz_porownanie(glowny, poprzedni_pomiar)
sprawdz_alert_cenowy(glowny)

wszystkie_nowe_wiersze = [glowny] + sugerowane

print("\n--- NOWE WIERSZE ---")
for wiersz in wszystkie_nowe_wiersze:
    print(wiersz)

zapisz_do_csv_najnowsze_na_gorze(wszystkie_nowe_wiersze)

print("\nZapisano dane do refurbed_prices.csv")
print("Najnowsze wyniki są teraz na górze pliku.")
print("Kolumny alert i prog_alertu zostały dodane do CSV.")