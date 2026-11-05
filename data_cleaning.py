import pandas as pd

PLIK_WEJSCIOWY = "refurbed_prices.csv"
PLIK_WYJSCIOWY = "refurbed_prices_clean.csv"

MIN_CENA = 500
MAX_CENA = 5000


def wczytaj_dane(nazwa_pliku=PLIK_WEJSCIOWY):
    df = pd.read_csv(nazwa_pliku)

    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")

    if "cena_liczbowo" in df.columns:
        df["cena_liczbowo"] = pd.to_numeric(
            df["cena_liczbowo"],
            errors="coerce"
        )

    return df


def usun_duplikaty_w_tym_samym_pomiarze(df):
    """
    Usuwa powtarzające się rekordy w ramach tego samego pomiaru.
    Powtórzenia tego samego wariantu w różnych dniach zostają.
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

    klucze = [
        kolumna
        for kolumna in kandydaci
        if kolumna in df.columns
    ]

    if len(klucze) < 2:
        return df.copy(), 0

    przed = len(df)

    wynik = df.drop_duplicates(
        subset=klucze,
        keep="first"
    ).copy()

    usunieto = przed - len(wynik)

    return wynik, usunieto


def usun_bledne_ceny(df):
    """
    Usuwa rekordy z ceną pustą albo spoza sensownego zakresu.
    """
    if "cena_liczbowo" not in df.columns:
        return df.copy(), 0

    przed = len(df)

    maska_poprawna = (
        df["cena_liczbowo"].notna()
        & (df["cena_liczbowo"] >= MIN_CENA)
        & (df["cena_liczbowo"] <= MAX_CENA)
    )

    wynik = df.loc[maska_poprawna].copy()

    usunieto = przed - len(wynik)

    return wynik, usunieto


def zapisz_clean(df, nazwa_pliku=PLIK_WYJSCIOWY):
    df_do_zapisu = df.copy()

    if "data" in df_do_zapisu.columns:
        df_do_zapisu["data"] = df_do_zapisu["data"].dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    df_do_zapisu.to_csv(
        nazwa_pliku,
        index=False,
        encoding="utf-8-sig"
    )


def main():
    df = wczytaj_dane()

    print("--- DATA CLEANING ---")
    print(f"Rekordy RAW: {len(df)}")

    df_bez_duplikatow, duplikaty_usuniete = (
        usun_duplikaty_w_tym_samym_pomiarze(df)
    )

    print(
        f"Usunięte duplikaty w tym samym pomiarze: "
        f"{duplikaty_usuniete}"
    )

    df_clean, bledne_ceny_usuniete = (
        usun_bledne_ceny(df_bez_duplikatow)
    )

    print(
        f"Usunięte rekordy z błędną ceną: "
        f"{bledne_ceny_usuniete}"
    )

    print(f"Rekordy CLEAN: {len(df_clean)}")

    zapisz_clean(df_clean)

    print(
        f"Zapisano oczyszczone dane do: "
        f"{PLIK_WYJSCIOWY}"
    )


if __name__ == "__main__":
    main()
