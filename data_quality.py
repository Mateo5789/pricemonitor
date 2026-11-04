import pandas as pd

PLIK_CSV = "refurbed_prices.csv"


def wczytaj_dane(nazwa_pliku=PLIK_CSV):
    df = pd.read_csv(nazwa_pliku)

    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")

    if "cena_liczbowo" in df.columns:
        df["cena_liczbowo"] = pd.to_numeric(
            df["cena_liczbowo"],
            errors="coerce"
        )

    if "prog_alertu" in df.columns:
        df["prog_alertu"] = pd.to_numeric(
            df["prog_alertu"],
            errors="coerce"
        )

    return df


def policz_braki(df):
    """
    Zwraca liczbę brakujących wartości per kolumna.
    """
    return (
        df.isna()
        .sum()
        .sort_values(ascending=False)
        .to_dict()
    )


def policz_pelne_duplikaty(df):
    """
    Liczy rekordy, które są pełnymi duplikatami.
    """
    maska = df.duplicated(keep=False)
    return int(maska.sum())


def znajdz_duplikaty_biznesowe(df):
    """
    Szuka duplikatów po kluczowych polach biznesowych.
    """
    kandydaci = [
        "data",
        "typ",
        "model",
        "kolor",
        "pamiec",
        "stan",
        "cena_liczbowo",
        "dostepnosc",
    ]

    klucze = [kolumna for kolumna in kandydaci if kolumna in df.columns]

    if not klucze:
        return pd.DataFrame()

    maska = df.duplicated(
        subset=klucze,
        keep=False
    )

    return (
        df.loc[maska]
        .sort_values(klucze)
        .copy()
    )


def znajdz_bledne_ceny(df, minimum=500, maksimum=5000):
    """
    Zwraca rekordy z pustą, zerową albo podejrzaną ceną.
    """
    if "cena_liczbowo" not in df.columns:
        return pd.DataFrame()

    maska = (
        df["cena_liczbowo"].isna()
        | (df["cena_liczbowo"] <= 0)
        | (df["cena_liczbowo"] < minimum)
        | (df["cena_liczbowo"] > maksimum)
    )

    return df.loc[maska].copy()


def znajdz_bledne_alerty(df):
    """
    Sprawdza spójność wartości alert z progiem alertu.
    """
    wymagane = {"cena_liczbowo", "prog_alertu", "alert"}

    if not wymagane.issubset(df.columns):
        return pd.DataFrame()

    roboczy = df.dropna(
        subset=["cena_liczbowo", "prog_alertu"]
    ).copy()

    oczekiwany_alert = roboczy.apply(
        lambda wiersz: (
            "TAK"
            if wiersz["cena_liczbowo"] < wiersz["prog_alertu"]
            else "NIE"
        ),
        axis=1
    )

    maska = roboczy["alert"].astype(str) != oczekiwany_alert

    wynik = roboczy.loc[maska].copy()
    wynik["oczekiwany_alert"] = oczekiwany_alert[maska]

    return wynik


def znajdz_bledne_daty(df):
    """
    Zwraca rekordy, których data nie została poprawnie odczytana.
    """
    if "data" not in df.columns:
        return pd.DataFrame()

    return df[df["data"].isna()].copy()


def policz_wynik_jakosci(df):
    """
    Prosty wynik jakości danych 0-100.
    To wskaźnik pomocniczy do dashboardu, nie formalny standard jakości.
    """
    if df.empty:
        return 0.0

    liczba_rekordow = len(df)

    braki = int(df.isna().sum().sum())
    pelne_duplikaty = policz_pelne_duplikaty(df)
    bledne_ceny = len(znajdz_bledne_ceny(df))
    bledne_alerty = len(znajdz_bledne_alerty(df))
    bledne_daty = len(znajdz_bledne_daty(df))

    maks_punkty = max(liczba_rekordow * max(len(df.columns), 1), 1)

    kara = (
        braki
        + pelne_duplikaty
        + bledne_ceny
        + bledne_alerty
        + bledne_daty
    )

    wynik = 100 - (kara / maks_punkty * 100)

    return round(max(0, min(100, wynik)), 2)


def raport_jakosci(df):
    """
    Zwraca kompletne podsumowanie jakości danych.
    """
    duplikaty_biznesowe = znajdz_duplikaty_biznesowe(df)
    bledne_ceny = znajdz_bledne_ceny(df)
    bledne_alerty = znajdz_bledne_alerty(df)
    bledne_daty = znajdz_bledne_daty(df)

    return {
        "liczba_rekordow": int(len(df)),
        "liczba_kolumn": int(len(df.columns)),
        "pelne_duplikaty": policz_pelne_duplikaty(df),
        "duplikaty_biznesowe": int(len(duplikaty_biznesowe)),
        "braki": policz_braki(df),
        "bledne_ceny": int(len(bledne_ceny)),
        "bledne_alerty": int(len(bledne_alerty)),
        "bledne_daty": int(len(bledne_daty)),
        "wynik_jakosci": policz_wynik_jakosci(df),
    }


def podsumowanie_jakosci(nazwa_pliku=PLIK_CSV):
    df = wczytaj_dane(nazwa_pliku)
    raport = raport_jakosci(df)

    print("--- RAPORT JAKOŚCI DANYCH ---")
    print(f"Rekordy: {raport['liczba_rekordow']}")
    print(f"Kolumny: {raport['liczba_kolumn']}")
    print(f"Pełne duplikaty: {raport['pelne_duplikaty']}")
    print(f"Duplikaty biznesowe: {raport['duplikaty_biznesowe']}")
    print(f"Błędne ceny: {raport['bledne_ceny']}")
    print(f"Błędne alerty: {raport['bledne_alerty']}")
    print(f"Błędne daty: {raport['bledne_daty']}")
    print(f"Wynik jakości: {raport['wynik_jakosci']}/100")
    print("Braki per kolumna:")

    for kolumna, liczba in raport["braki"].items():
        if liczba > 0:
            print(f"  - {kolumna}: {liczba}")


if __name__ == "__main__":
    podsumowanie_jakosci()
