# Isabella
Skripte za pokretanje poslova na računalnom klasteru [Isabella](https://www.srce.unizg.hr/isabella/).

Moje iskustvo implementiranja skripti za pokretanje poslova je da, svaki put kad bi radio novu skriptu, bi ispočetka tražio što i kako sam radio prije, kako se te stare skripte koriste, i opet konzultirao SGE dokumentaciju. Nova skripta bi bila nadogradnja na stare skripte, uglavnom s nekim unapređenjem, koje ne bi bilo propagirano u stare skripte.

Motivi projekta:
* automatizirati i standardizirati pokretanje poslova na klasteru,
* dokumentacija kako se pokreću poslovi,
* podsjetnik kako se general postavlja pokretanje poslova s novim programima.

Imenovanja koja se koriste:
* **program**: executable analize,
* **posao** / **job**: job u SGE-u,
* **obrada** / **processing**: jedan ili više poslova koji rade 'cjelinu'.

## Skripte

Smjernice implementacije:
* Posao je vezan za jedan direktorij. Pokreće se u tom direktoriju, startna skripta i relevantni podaci posla se spremaju u taj direktorij.
* Skripte pokreću i rade s jednom obradom. Opis obrade je zapisan u fajlu.
  * Ako obrada ima jedan posao, onda se podaci obrade zapisuju u direktoriju posla.
  * Ako obrada ima više poslova, onda se podaci obrade zapisuju u direktoriju sadrži direktorije poslova. Obrada je direktorij s podirektorijima za poslove!

Koraci, i skripte, obrada:
* pokretanje obrade; skripte imenovane **`irb_<program>.py`**,
* provjera (čekanje i čekanje) statusa obrade; skripta **`obrada_status.py [obrada]`**,
* kupljenje podataka; ako je sve dobro onda su rezultati u output.zip fajlu obrade; ako ne ili želimo forsirati kupljenje podataka onda ima skripta **`obrada_zip.py [obrada]`**,

Pokretanje poslova (startne skripte) ima korake:
* slanje mejla ako je to prvi pokrenuti posao obrade (ako je zadano),
* zapisivanje vremena pokretanja,
* pokretanje programa,
* zapisivanje vremena završetka,
* slanje mejla ako je to zadnji završeni posao obrade (ako je zadano).


## Dokumentacija

Barem dokumentirati argumente komandne linije.

Osim tog bi bilo dobro znati zašto se odlučilo za specifičnosti (takvu kombinaciju parametara, strategiju pokretanja, ...)

## Podsjetnik

'Standardni' koraci implementiranja skripti za rad s novim programom:
* kompajliranje programa,
* upogonjavanje startne skripte za testnog primjera,
* kreiranje skripte koja koristi testnu startnu skriptu kao šprancu.

Podsjetnik na sva tri dijela. 

