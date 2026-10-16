# LIFE OS — Dagkompas (VWO 6 Python-project)

## Wat is het?

Een webapp die dagelijkse taken rangschikt op basis van duur, belang, urgentie, deadline en benodigde energie. De app bevat ook een vergelijking met een eenvoudiger algoritme, een gevoeligheidsanalyse en een onderzoekslogboek.

## Starten

1. Installeer Python 3.10 of nieuwer.
2. Pak de zip uit.
3. Open een terminal/command prompt in de uitgepakte map.
4. Installeer de benodigdheden:
`python -m pip install -r requirements.txt`
5. Start de app:
`python -m streamlit run app.py`
6. Open de lokale URL die Streamlit toont, meestal `http://localhost:8501`.

## Inhoud

* `app.py`: webinterface en invoer
* `planner\_core.py`: algoritmen en gevoeligheidsanalyse
* `test\_planner.py`: eenvoudige automatische tests
* `requirements.txt`: benodigde pakketten

## Onderzoeksvraag

Hoe verandert een aanbevolen dagplanning als tijd, energie, urgentie en taakduur veranderen, en in hoeverre zijn de uitkomsten afhankelijk van onze gekozen scoreformule?

## Mogelijke testscenario's

1. **Weinig tijd:** stel vrije tijd in op 45 minuten. Welke taken verdwijnen uit de planning?
2. **Lage energie:** zet energie op 1. Verandert de volgorde?
3. **Deadline vandaag:** maak een taak urgent en zet de deadline op 0 dagen.
4. **Lange versus korte taak:** vergelijk een taak van 60 minuten met twee taken van 30 minuten.
5. **Algoritmevergelijking:** bekijk of LIFE OS en de baseline dezelfde volgorde kiezen.
6. **Modelkritiek:** bedenk een geval waarin de hoogste score niet de beste keuze voor een mens is.

## Reflectie voor een sterk vwo 6-project

* Formuleer vooraf een hypothese.
* Verander steeds één variabele en houd de rest gelijk.
* Leg uit wat je verwachtte, wat er werkelijk gebeurde en waarom.
* Geef een concreet voorbeeld van een onlogische uitkomst.
* Pas één regel aan en vergelijk de oude en nieuwe versie op dezelfde scenario's.
* Bespreek beperkingen: vaste afspraken, reistijd, pauzes, afhankelijkheden tussen taken en de onbetrouwbaarheid van subjectieve scores.
* Trek geen grotere conclusies dan je testresultaten toelaten.

## Belangrijke beperking

Dit is een transparant prototype met zelfgekozen heuristieken, geen wetenschappelijk gevalideerde optimalisatie. Weer en budget worden in de interface getoond maar beïnvloeden de huidige taakscore nog niet. Dat is bewust een mogelijke uitbreiding: voeg bijvoorbeeld een activiteit/boodschappencategorie toe en test of de uitkomst daardoor aantoonbaar beter wordt.

