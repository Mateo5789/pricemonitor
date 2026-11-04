import streamlit as st
import pandas as pd

from analytics import (
    wczytaj_dane,
    filtruj_glowny_produkt,
    policz_statystyki,
    przygotuj_historie_cen,
    przygotuj_ostatnie_pomiary,
)

from data_quality import (
    raport_jakosci,
    znajdz_duplikaty_biznesowe,
    znajdz_bledne_ceny,
    znajdz_bledne_alerty,
)


PLIK_CSV = "refurbed_prices.csv"


st.set_page_config(
    page_title="Refurbed Price Tracker 2.0",
    page_icon="📱",
    layout="wide"
)

st.title("📱 Refurbed Price Tracker 2.0")
st.caption(
    "Automatyczny monitoring cen, analiza historii i kontrola jakości danych."
)


@st.cache_data
def zaladuj_dane():
    return wczytaj_dane(PLIK_CSV)


try:
    df = zaladuj_dane()
except FileNotFoundError:
    st.error(
        f"Nie znaleziono pliku {PLIK_CSV}. "
        "Umieść go w tym samym folderze co app.py."
    )
    st.stop()
except Exception as e:
    st.error(f"Błąd podczas wczytywania danych: {e}")
    st.stop()


if df.empty:
    st.warning("Plik CSV nie zawiera danych.")
    st.stop()


zakladka1, zakladka2, zakladka3 = st.tabs(
    [
        "📊 Dashboard",
        "🧹 Data Quality",
        "📋 Dane",
    ]
)


with zakladka1:
    st.subheader("Podsumowanie cen")

    try:
        glowny = filtruj_glowny_produkt(df)
        statystyki = policz_statystyki(glowny)
    except Exception as e:
        st.error(f"Błąd analizy głównego produktu: {e}")
        st.stop()

    if statystyki["liczba_pomiarow"] == 0:
        st.warning("Brak poprawnych pomiarów głównego produktu.")
    else:
        col1, col2, col3, col4 = st.columns(4)

        delta = None
        if statystyki["zmiana_ceny"] is not None:
            delta = f"{statystyki['zmiana_ceny']:.2f} zł"

        col1.metric(
            "Aktualna cena",
            f"{statystyki['aktualna_cena']:.2f} zł",
            delta
        )

        col2.metric(
            "Najniższa cena",
            f"{statystyki['minimalna_cena']:.2f} zł"
        )

        col3.metric(
            "Najwyższa cena",
            f"{statystyki['maksymalna_cena']:.2f} zł"
        )

        col4.metric(
            "Średnia cena",
            f"{statystyki['srednia_cena']:.2f} zł"
        )

        st.write(
            f"**Liczba pomiarów:** {statystyki['liczba_pomiarow']}"
        )

        if statystyki["zmiana_procentowa"] is not None:
            st.write(
                f"**Zmiana względem poprzedniego pomiaru:** "
                f"{statystyki['zmiana_procentowa']:.2f}%"
            )

        st.subheader("Historia ceny")

        historia = przygotuj_historie_cen(glowny)

        if historia.empty:
            st.info("Brak danych do wykresu.")
        else:
            st.line_chart(
                historia.set_index("data")["cena_liczbowo"]
            )

        st.subheader("Alert cenowy")

        alert = statystyki["aktualny_alert"]
        prog = statystyki["prog_alertu"]

        if alert == "TAK":
            if prog is not None:
                st.error(
                    f"🚨 Cena spadła poniżej progu {prog:.2f} zł."
                )
            else:
                st.error("🚨 Alert cenowy jest aktywny.")
        elif alert == "NIE":
            if prog is not None:
                st.success(
                    f"Cena jest powyżej progu {prog:.2f} zł."
                )
            else:
                st.success("Alert cenowy nie jest aktywny.")
        else:
            st.warning("Brak jednoznacznego statusu alertu.")

        st.subheader("Ostatnie pomiary")

        ostatnie = przygotuj_ostatnie_pomiary(
            glowny,
            limit=10
        )

        if ostatnie.empty:
            st.info("Brak pomiarów do wyświetlenia.")
        else:
            st.dataframe(
                ostatnie,
                use_container_width=True,
                hide_index=True
            )


with zakladka2:
    st.subheader("Kontrola jakości danych")

    raport = raport_jakosci(df)

    q1, q2, q3, q4 = st.columns(4)

    q1.metric(
        "Wynik jakości",
        f"{raport['wynik_jakosci']}/100"
    )

    q2.metric(
        "Pełne duplikaty",
        raport["pelne_duplikaty"]
    )

    q3.metric(
        "Błędne ceny",
        raport["bledne_ceny"]
    )

    q4.metric(
        "Błędne alerty",
        raport["bledne_alerty"]
    )

    st.write(
        f"**Liczba rekordów:** {raport['liczba_rekordow']}"
    )
    st.write(
        f"**Liczba kolumn:** {raport['liczba_kolumn']}"
    )
    st.write(
        f"**Duplikaty biznesowe:** "
        f"{raport['duplikaty_biznesowe']}"
    )
    st.write(
        f"**Błędne daty:** {raport['bledne_daty']}"
    )

    st.subheader("Braki danych")

    braki_df = pd.DataFrame(
        [
            {
                "kolumna": kolumna,
                "brakujace_wartosci": liczba
            }
            for kolumna, liczba in raport["braki"].items()
            if liczba > 0
        ]
    )

    if braki_df.empty:
        st.success("Nie wykryto brakujących wartości.")
    else:
        st.dataframe(
            braki_df,
            use_container_width=True,
            hide_index=True
        )

    st.subheader("Duplikaty biznesowe")

    duplikaty = znajdz_duplikaty_biznesowe(df)

    if duplikaty.empty:
        st.success("Nie wykryto duplikatów biznesowych.")
    else:
        st.warning(
            f"Wykryto {len(duplikaty)} rekordów "
            "należących do grup duplikatów."
        )

        st.dataframe(
            duplikaty.head(50),
            use_container_width=True,
            hide_index=True
        )

    st.subheader("Podejrzane ceny")

    bledne_ceny = znajdz_bledne_ceny(df)

    if bledne_ceny.empty:
        st.success("Nie wykryto podejrzanych cen.")
    else:
        st.warning(
            f"Wykryto {len(bledne_ceny)} podejrzanych rekordów."
        )

        st.dataframe(
            bledne_ceny.head(50),
            use_container_width=True,
            hide_index=True
        )

    st.subheader("Niespójne alerty")

    bledne_alerty = znajdz_bledne_alerty(df)

    if bledne_alerty.empty:
        st.success("Alerty są spójne z progami cenowymi.")
    else:
        st.warning(
            f"Wykryto {len(bledne_alerty)} niespójnych alertów."
        )

        st.dataframe(
            bledne_alerty.head(50),
            use_container_width=True,
            hide_index=True
        )


with zakladka3:
    st.subheader("Podgląd danych")

    typy = ["Wszystkie"]

    if "typ" in df.columns:
        typy += sorted(
            [
                str(x)
                for x in df["typ"].dropna().unique()
            ]
        )

    wybrany_typ = st.selectbox(
        "Filtruj po typie rekordu",
        typy
    )

    widok = df.copy()

    if (
        wybrany_typ != "Wszystkie"
        and "typ" in widok.columns
    ):
        widok = widok[
            widok["typ"].astype(str) == wybrany_typ
        ]

    st.write(f"**Liczba widocznych rekordów:** {len(widok)}")

    st.dataframe(
        widok.sort_values(
            "data",
            ascending=False
        )
        if "data" in widok.columns
        else widok,
        use_container_width=True,
        hide_index=True
    )
