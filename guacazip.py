# Autor: Paweł Gabryś, UŚ-DASIUS
# Github: github.com/pgabrys94/guacazip
# Wersja : v1.0

import os
import shutil
import time
import sys
import datetime
from py7zr import FILTER_LZMA2, SevenZipFile, PRESET_EXTREME


def arc():
    """
    Funkcja archiwizująca nagrania.
    :return:
    """
    def pack(t_dir):
        """
        Pakowanie sesji do archiwum 7zip
        :param t_dir: obiekt path-like
        :return:
        """
        os.chdir(archive)
        if not len(os.listdir(t_dir)) == 0:
            with SevenZipFile(f"{t_dir}.7z", "w", filters=flist) as archive_file:
                print("pakowanie {}...".format(t_dir))
                archive_file.writeall(t_dir)
            print("ZARCHIWIZOWANO: {}".format(t_dir))
        else:
            print("folder archiwizacji pusty, pomijam...")

    if len(os.listdir(recordings)) > 0:
        popped = 0
        with open(skipfile, "r") as skip:
            session_list = os.listdir(recordings)
            for session in session_list:
                if session in skip.read():
                    session_list.pop(session_list.index(session))
                    popped += 1
            print("\nznaleziono {} nagrań sesji, pominięto {}".format(len(session_list,), popped))
            if len(session_list) == 0:
                print("\nNIC DO ZROBIENIA")
                sys.exit()
            else:
                print("\nROZPOCZĘCIE PROCESU ARCHIWIZACJI...")
            time.sleep(1)

            # odczyt zawartości katalogu i przypisanie do słownika
            for uuid in session_list:
                full_content[uuid] = os.listdir(os.path.join(recordings, uuid))[0]

        # konwersja słownika zawartości katalogu na słownik uuid sesji użytkownika
        for uuid, session in full_content.items():
            username = session.split("-")[0]
            if username not in user_content:
                user_content[username] = [uuid]
            else:
                user_content[username].append(uuid)

        for user, uuid_list in user_content.items():
            print("użytkownik: {}, sesji: {}".format(user, len(uuid_list)))

        time.sleep(2)

        # określenie konwencji nazewniczej katalogów:
        for uuid, filename in full_content.items():
            username = filename.split("-")[0]
            session_date = filename.split("-")[1]
            if username not in user_session_dates:
                user_session_dates[username] = [filename.split("-")[1], filename.split("-")[1]]

            else:
                if session_date < user_session_dates[username][0]:
                    user_session_dates[username][0] = session_date
                elif session_date > user_session_dates[username][0]:
                    user_session_dates[username][1] = session_date

        print("ARCHIWIZACJA...\n")

        # tworzenie katalogu przed archiwizacją:
        for user in list(user_content):
            earliest = user_session_dates[user][0]
            latest = user_session_dates[user][1]
            dir_name = f"{user}-{earliest}-{latest}"
            target_dir = os.path.join(archive, dir_name)
            print("tworzenie katalogu {}".format(dir_name))
            os.mkdir(target_dir)

            # przenoszenie katalogów UUID do katalogu archiwum:
            if os.path.exists(skipfile):
                with open(skipfile, "r") as skip:
                    for uuid in user_content[user]:
                        if uuid not in skip.read():
                            print("przenoszenie sesji {}".format(uuid))
                            shutil.move(os.path.join(recordings, uuid), target_dir)
                        else:
                            print("pomijam sesję {}: sesja z rozpakowanego archiwum".format(uuid))
            else:
                for uuid in user_content[user]:
                    if uuid not in skip.readlines():
                        print("przenoszenie sesji {}".format(uuid))
                        shutil.move(os.path.join(recordings, uuid), target_dir)

            # archiwizacja LZMA2:
            i = 5
            while True:
                pack(dir_name)
                time.sleep(1)
                print("testowanie archiwum...")
                with SevenZipFile(f"{target_dir}.7z", "r") as test_archive:
                    if test_archive.test() and test_archive.testzip() is None:
                        print("test OK")
                        print("czyszczenie...\n")
                        shutil.rmtree(target_dir)
                        break
                    else:
                        print("\nniepowodzenie testu archiwum, ponawiam archiwizację")
                        if i != 0:
                            i -= 1
                            print("pozostało prób: {}".format(i))
                            os.remove(f"{target_dir}.7z")
                            continue
                        else:
                            print("BŁĄD ARCHIWIZACJI {}\n".format(target_dir))
                            os.remove(f"{target_dir}.7z")
                            break
    else:
        print("Brak nagrań sesji.")

    print("\n{}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    print("{}".format("#" * 60))


def res():
    """
    Funkcja przywracająca nagrania z archiwum.
    :return:
    """
    def unpack(chosen_archive):
        """
        Rozpakowywanie archiwum.
        :param chosen_archive: String -> nazwa archiwum w lokalizacji /var/lib/guacamole/archive
        :return:
        """
        print("rozpakowywanie...")
        try:
            # rozpakuj archiwum
            archive_path = os.path.join(archive, chosen_archive)
            unzip_path = os.path.join(archive, chosen_archive.rstrip(".7z"))
            with SevenZipFile(archive_path, "r") as zipped_file:
                zipped_file.extractall(path=archive)
            print("rozpakowano {}\ndo katalogu\n{}\n".format(chosen_archive, unzip_path))
            time.sleep(2)

            # przenieś rozpakowane katalogi UUID do katalogu nagrań
            print("przenoszenie...")
            contents = os.listdir(unzip_path)
            with open(skipfile, "r+") as skip:
                data = skip.read()
                for content in contents:
                    # jeżeli UUID nie znajduje się w skipfile, przenieś katalog UUID i dopisz go do skipfile
                    if content not in data:
                        shutil.move(os.path.join(unzip_path, content), recordings)
                        skip.seek(0, os.SEEK_END)
                        skip.write(content + "\n")
                        print("przeniesiono.")
                        time.sleep(1)
                    else:
                        # jeżeli UUID jest w skipfile, nie przenoś i usuń rozpakowany katalog UUID
                        # NIE POWINNO ZADZIAŁAĆ - zawartość archiwum jest sprawdzana PRZED jego rozpakowaniem.
                        shutil.rmtree(os.path.join(unzip_path, content))
                        print("sesja {} obecna w .skiparc, pomijam...".format(content))
            # usuń rozpakowany katalog (który powinien być pusty)
            shutil.rmtree(unzip_path)

        except Exception as unzip_error:
            print("Błąd: ", unzip_error)

    def choose_by_user():
        """
        Menu wyboru archiwów względem nazwy użytkownika.
        :return:
        """
        def choose_user_archive(username):
            """
            Wybranie archiwum do rozpakowania.
            :param username: String -> nazwa użytkownika, któego dotyczy archiwum
            :return:
            """
            try:
                # konstruowanie listy archiwów
                archives = []
                with open(skipfile, "r") as skip:
                    data = skip.read().splitlines()
                for zipfile in os.listdir(archive):
                    # odczytaj katalogi UUID z nierozpakowanego archiwum
                    if zipfile.endswith(".7z"):
                        with SevenZipFile(os.path.join(archive, zipfile), "r") as zipped_archive:
                            zipped_uuids = [item.filename.split("/")[1] for item in zipped_archive.list()
                                            if len(item.filename.split("/")) == 2]
                            if (                                    # Jeżeli:
                                    zipfile.startswith(username)    # nazwa pliku rozpoczyna się od nazwy użytkownika i
                                    and zipfile.split(".")[0] not in archives   # nazwa pliku nie się nie powtarza i
                                    and not any(session in data      # żadne UUID nie jest w skipfile
                                                for session in zipped_uuids)
                            ):
                                # przypisz archiwum do wyświetlanej listy archiwów
                                archives.append(zipfile)

                column = 3
                width = 18
                if len(archives) == 0:
                    print("\n<brak archiwów do wyświetlenia>")
                else:
                    for i, x in enumerate(sorted(archives), start=1):
                        date_range = x.split("-", 1)[1].rstrip(".7z")
                        formatted_start = datetime.datetime.strptime(date_range.split("-")[0], "%Y%m%d").strftime("%Y-%m-%d")
                        formatted_end = datetime.datetime.strptime(date_range.split("-")[1], "%Y%m%d").strftime("%Y-%m-%d")
                        formatted = ("[{}] - {} > {:<{}}"
                                     .format(archives.index(x) + 1, formatted_start, formatted_end, width))
                        print("\n")
                        print(formatted, end="\n" if i % column == 0 else " ")

                restore_choice = input("\nWybierz archiwum do przywrócenia: ")
                if not restore_choice.isdigit() and restore_choice not in range(1, len(archives) + 1):
                    print("spróbuj ponownie.")
                else:
                    # wywołanie funkcji rozpakowującej wybrane archiwum
                    unpack(archives[int(restore_choice) - 1])
            except Exception as archive_menu_error:
                print(archive_menu_error)

        # odczyt użytkowników z nazw archiwów
        user_base = []
        for file in os.listdir(archive):
            if file.endswith(".7z") and len(file.split("-")) == 3:
                user_base.append(file.split("-")[0])

        print("\nZnalezionych użytkowników: {}\n".format(len(user_base)))

        if len(user_base) == 0:
            print("powrót...")
            time.sleep(1)
            return
        else:
            while True:
                for user in user_base:
                    print("[{}] - {}".format(user_base.index(user) + 1, user))

                # menu wyboru użytkownika
                print("\n[q] - powrót")
                user_choice = input("Wybierz użytkownika - [enter] zatwierdza: ")

                if user_choice.lower() == "q":
                    break
                elif user_choice.isdigit() and int(user_choice) in range(1, len(user_base) + 1):
                    choose_user_archive(user_base[int(user_choice) - 1])

    def input_file_path():
        """
        Pozwala ręcznie wprowadzić ścieżkę do wybranego archiwum.
        :return:
        """
        path_input = input(r"\nWprowadź ścieżkę absolutną do archiwum: ")

        try:
            if os.path.exists(path_input) and path_input.endswith(".7z"):
                unpack(path_input)
            else:
                raise Exception("ścieżka musi prowadzić do archiwum 7z")
        except Exception as path_input_error:
            print("Błąd: ", path_input_error)

    menu = {
        "Wybierz z listy archiwów": choose_by_user,
        "Wpisz ścieżkę do pliku": input_file_path
    }

    # menu główne
    while True:
        for mpos in list(menu):
            print("[{}] - {}\n".format(list(menu).index(mpos) + 1, mpos))

        print("\n[q] - wyjście")
        u_in = input("Wybierz opcję i zatwierdź [enter]: ")

        try:
            if u_in.lower() == "q":
                sys.exit()
            elif u_in.isdigit() and int(u_in) in range(1, len(menu) + 1):
                menu[list(menu)[int(u_in) - 1]]()
            else:
                print("Spróbuj ponownie.")
        except Exception as error:
            print(error)
            break


def cln():
    """
    Funkcja usuwająca zawartość pliku archive/.skipfile oraz katalogi sesji odpowiadające tym UUID.
    Jeżeli w pliku znajduje się UUID, to uniemożliwi to rozpakowanie archiwum zawierającego takie UUID.
    Taki katalog UUID nie będzie także brany pod uwagę przy wykonywaniu archiwizacji - zostanie pominięty.
    :return:
    """
    try:
        with open(skipfile, "r+") as skip:
            data = skip.read().strip().splitlines()
            for uuid in data:
                shutil.rmtree(os.path.join(recordings, uuid))
            skip.seek(0)
            skip.truncate()
        print("Plik {} został wyczyszczony, sesje zostały usunięte.".format(skipfile))
        sys.exit()
    except Exception as error:
        print("Błąd: ", error)


recordings = r"/var/lib/guacamole/recordings"    # ścieżka do katalogu nagrań guacamole,
archive = r"/var/lib/guacamole/archive"          # Ścieżka do archiwum nagrań,
skipfile = os.path.join(archive, ".skiparc")     # Ścieżka do pliku przechowującego informacje o wypakowanych archiwach.
full_content = {}                                # słownik zawartości katalogu nagrań (UUID:nazwa pliku sesji),
user_content = {}                                # słownik sesji należących do użytkownika (login:[UUID]),
user_session_dates = {}                          # słownik najstarszej i najnowszej sesji danego użytkownika,
flist = [{                                       # parametry określające metodę kompresji i jej preset,
    'id': FILTER_LZMA2, 'preset': PRESET_EXTREME
}]
params = {"arc": arc, "res": res, "cln": cln}

# kod wyświetlający parametry programu i umożliwiający korzystanie z nich
try:
    if len(sys.argv) == 2 and sys.argv[1] in params:
        print("\n*** {} ***".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        print("\n### GUACAZIP ###")
        time.sleep(1)
        params[sys.argv[1]]()
    else:
        raise Exception("Nieprawidłowy parametr")
except Exception as err:
    print(err)
    print("\nUżycie: guacazip [PARAMETR]")
    print("\t'arc' archiwizuj obecną zawartość katalogu nagrań")
    print("\t'res' przywróć archiwum do katalogu nagrań (otwiera interfejs tekstowy)")
    print("\t'cln' wyczyść plik /var/lib/guacamole/archive/.skiparc")
