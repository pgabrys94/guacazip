# guacazip
Narzędzie do archiwizacji sesji guacamole

python3 guacazip.py [parametr]
	arc - automatyczna archiwizacja
	res - TUI przywracania archiwów
	cln - czyszczenie pliku blokady archiwizacji
	
Zależności:
	Wymaga katalogu /var/lib/guacamole/archive:
 
		mkdir -p /var/lib/guacamole/archive
		chown <guacd user>:<tomcat group> /var/lib/guacamole/archive
		chmod 2750 /var/lib/guacamole/archive
	
Struktura archiwizacji: Archiwa przechowują sesje użytkowników wykonane w przedziale czasowym pomiędzy uruchomieniami programu. 
						            Nazwy plików wskazują na nazwę użytkownika, co pozwala uzyskać łatwy dostęp do konkretnych sesji z określonego przedziału czasowego.
	
Uruchomienie skryptu guacazip.py bez parametru  wyświetli listę parametrów a następnie zakończy pracę programu.
		
		guacazip.py arc
  
  1. Skrypt przeskanuje zawartość katalogu /var/lib/guacamole/recordings, utworzy słownik {UUID:nazwa użytkownika} i przekształci ten słownik na słownik {nazwa użytkownika:[lista UUID]}.
  2. Następnie przeniesie katalogi UUID z guacamole/recordings do guacamole/archive do podkatalogów o strukturze "<nazwa użytkownika>-<data najwcześniejszej sesji>-<data najpóźniejszej sesji>".
  3. W dalszej kolejności każdy katalog użytkownika zostaje spakowany do archiwum 7zip z presetem EXTREME (najwyższy stopień kompresji).
  4. Każde archiwum po spakowaniu zostaje przetestowane. Sprawdzana jest suma kontrolna CRC całego archiwum jak i każdego z zawartych w nim plików. Jezeli wystąpi błąd, wadliwe archiwum jest usuwane
    i następuje ponowna jego kompresja. Maksymalna ilość prób wynosi 5. Jeżeli wszystkie próby się nie powiodą, archiwum nie zostanie utworzone a pliki pozostaną w niespakowanym katalogu.
    Jeżeli archiwum przejdzie test, katalog źródłowy zostaje usunięty.
				
  5. SKIPFILE: Plik guacamole/archive/.skipfile przechowuje UUID sesji do pominięcia w procesie archiwizacji/przywracania. UUID sesji zostaje tam umieszczone w momencie, gdy archiwum zostanie rozpakowane parametrem res. Zapobiega to uwzględnianiu takiego UUID przy kolejnej archiwizacji (aby uniknąć niepotrzebnego powielania sesji w archiwach), a także w interfejsie przywracania.
				
	guacazip.py res

  6. Uruchamia interfejs tekstowy przywracania. Pozwala ręcznie wprowadzić ścieżkę do archiwum 7zip, które ma zostać rozpakowane do katalogu /recordings, a także wybrać z listy archiwów umiesczonych w /archive.
  7. Wybranie i zatwierdzenie opcji "Wybierz z listy archiwów" spowoduj przeskanowanie katalogu /archive oraz wylistowanie wszystkich nazw użytkownika, których archiwum zostanie tam znalezione.
  8. Wybranie i zatwierdzenie użytkownika wyświetli zakresy dat dla każdego archiwum przypisanego do użytkownika. Jeżeli któreś z archiwów zawiera UUID, które widnieje w .skipfile, to archiwum nie zostanie wyświetlone.
  9. Wybranie i zatwierdzenie archiwum rozpakuje je do katalogu guacamole/recordings, a następnie umieści w .skipfile UUID wszystkich sesji, które zostały rozpakowane.
			
	guacazip.py cln
 
  10. Usuwa wszystkie sesje z guacamole/recordings, których UUID jest zawarte w .skipfile, a następnie usuwa zawartość skipfile.
