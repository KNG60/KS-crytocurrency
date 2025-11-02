## Plan Projektu

### **Etap 1: Sieć i bezpieczny portfel**

- [x] **Wallet:** Generowanie i przechowywanie pary kluczy kryptograficznych
- [x] **Node:** Możliwość komunikacji z innymi węzłami w sieci
- [x] **Node:** Rejestracja i przechowywanie informacji o innych węzłach w sieci

### **Etap 2: Prosty łańcuch bloków**

- [ ] **Node:** Tworzenie bloków z listą transakcji i powiązaniem do poprzedniego bloku - <span style="color:red">listy transakcji pojawią sie dopiero na KM3?</span>
- [x] **Node:** Utworzenie pierwszego bloku (bloku genezy)
- [x] **Node:** Generowanie haszy bloków w celu zapewnienia integralności
- [x] **Node:** Sprawdzanie poprawności i spójności łańcucha bloków
- [x] **Node:** Rozgłaszanie nowych bloków do innych węzłów i odbieranie ich od sieci


---

**Co nowego:**
- Trudność PoW w projekcie jest stała i ustawiona w kodzie na 5 (liczba zer w hexach). 
- Węzeł górniczy po wykopaniu bloku automatycznie rozgłasza go do znanych peerów `broadcast_block()`.
- W momencie uruchamiania wezła sprawdza on kto ma najdłuższy blockchain `_init_chain()`, (z własej bazy i zapisanych peersów)
- walidacja  łańcucha sprawdza `validate_chain()`:
	- poprzedni hash
	- długość blockchain "height"
	- wynik funkcji hashującej
	- Wynik i liczbę zer rozwiązania wezględem difficulty
	- Nie sprawdza skumulowanej pracy.
	- Jesli nowy blockchain jest dłuższy adaptuje go
	- W przypadku tej samej długości blockchian nie wykonuje forku tylko zostaje przy swoim!
- Blok genezy jest generowany gdy nowy wezeł nie połączy się z istniejacą siecią. 
- Spora część rozwiązań pokrywa wymagania etapu 4. Hura!
- Endpointy HTTP:
	- `GET /blocks` – zwraca cały łańcuch,
	- `POST /blocks` – przyjmuje nowy blok i waliduje go,
	- `POST /mine` – (tylko rola miner) wydobywa nowy blok.
- Nowe parametr : `--role`
	- ` normal` bez zmian, zwykły wezeł.
	- `miner` może wykopywać bloki.

**Co omówić, dodać :**
- Rozwinąć o organiczne/czasowe zwiększanie difficuty i synchronizaje miedzy węzłami.
- Czy walidacja blockchaina powinna brać po uwagę skumulowaną pracy jako kryterium.
- Ulepszyć sposób zlecania wykonykopywania bloków na ciągły.
- Przygotować test przedstawiający ciągłą symulację.
- Dodać do Network Topology info o węzłach :
	- Role (mp. zmienić kopalnie na trójkąty)
	- Aktualną liczbę bloków w blockchainie 
	- Status pracy koparek
- Namierzyć potencjalne nieprawidłowości.


### **Etap 3: Transakcje i konsensus**

- [ ] **Wallet:** Tworzenie i podpisywanie transakcji między użytkownikami
- [ ] **Node:** Gromadzenie oczekujących transakcji w sieci
- [ ] **Node:** Mechanizm kopania bloków i ustalania konsensusu (Proof-of-Work)
- [ ] **Node:** Dodawanie nagród dla górników (transakcje coinbase)
- [ ] **Node:** Weryfikacja transakcji (poprawność podpisu, wystarczające saldo, ochrona przed podwójnym wydatkowaniem)
- [ ] **Node:** Obliczanie sald użytkowników na podstawie historii transakcji

### **Etap 4: Kopanie asynchroniczne i obsługa forków**

- [ ] **Node:** Zasada „najdłuższego łańcucha” w przypadku konfliktów między węzłami
- [ ] **Node:** Synchronizacja i zastępowanie lokalnego łańcucha, jeśli pojawi się dłuższy
- [ ] **Node:** Symulacja działania złośliwego węzła tworzącego konkurencyjny łańcuch

### **Etap 5: Sprawozdanie końcowe**

- [ ] **Wallet:** Wyjaśnienie zastosowanej kryptografii i podpisów cyfrowych
- [ ] **Node:** Opis architektury systemu i sposobu działania węzłów
- [ ] **Node:** Podsumowanie wyników testów, bezpieczeństwa i symulacji działania sieci
