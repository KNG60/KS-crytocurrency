# Prosta Kryptowaluta w Pythonie

Projekt implementuje uproszczony system kryptowaluty oparty na technologii **blockchain**.  
System składa się z dwóch głównych komponentów:

- **Node (Węzeł):** Utrzymuje łańcuch bloków, zarządza siecią i walidacją transakcji.
- **Wallet (Portfel):** Zarządza tożsamością użytkownika, kluczami kryptograficznymi i tworzeniem transakcji.

---

## Plan Projektu

### **Etap 1: Sieć i bezpieczny portfel**

- [ ] **Wallet:** Generowanie i przechowywanie pary kluczy kryptograficznych
- [ ] **Wallet:** Podpisywanie danych (transakcji) przy użyciu klucza prywatnego
- [ ] **Wallet:** Zapisywanie i wczytywanie portfela z pliku
- [x] **Node:** Możliwość komunikacji z innymi węzłami w sieci
- [x] **Node:** Rejestracja i przechowywanie informacji o innych węzłach w sieci

### **Etap 2: Prosty łańcuch bloków**

- [ ] **Node:** Tworzenie bloków z listą transakcji i powiązaniem do poprzedniego bloku
- [ ] **Node:** Utworzenie pierwszego bloku (bloku genezy)
- [ ] **Node:** Generowanie haszy bloków w celu zapewnienia integralności
- [ ] **Node:** Sprawdzanie poprawności i spójności łańcucha bloków
- [ ] **Node:** Rozgłaszanie nowych bloków do innych węzłów i odbieranie ich od sieci

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

---

## Instrukcja

### Środowisko

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Uruchomienie węzłów

```bash
python run_node.py --host 127.0.0.1 --port 5000

python run_node.py --host 127.0.0.1 --port 5001 --seeds 127.0.0.1:5000

python run_node.py --host 127.0.0.1 --port 5002 --seeds 127.0.0.1:5001
```

### Pomoc

```bash
python run_node.py --help
```

### Lista peerów

```bash
curl http://127.0.0.1:5000/peers
```

### Ping węzła

```bash
curl http://127.0.0.1:5000/ping
```

### Dodanie peera

```bash
curl -X POST http://127.0.0.1:5000/peers \
  -H "Content-Type: application/json" \
  -d '{"host": "127.0.0.1", "port": 5001}'
```
## Uwagi
Dodanie poźniejsze wezła do istniejącego już nie aktualizuje listy peersów dodawanego wezła.
Podczas dodwania nowego wezła dodawana jest tez lista jego węzłów.W przyszłosci rozważyć zapytanie też wezłow z tej listy. Tym samym zwiekszac rozpoznianie sieci. 
 
---

## Portfel (Wallet) – jak działa

Portfel jest lokalny i przechowywany w jednym pliku SQLite per użytkownik. Nie istnieje żaden globalny rejestr wszystkich portfeli w sieci.

- Lokalizacja pliku: `db/wallet_<LABEL>.db` (np. `db/wallet_My_Wallet.db`)
- Wewnątrz znajdują się dwie tabele:
  - `wallet_meta` – jeden wiersz z metadanymi portfela
    - `id=1` (stałe), `label`, `balance`, `created_at`, `salt` (BLOB), `verifier` (BLOB)
  - `accounts` – konta/rachunki należące do portfela
    - `id`, `label`, `balance`, `created_at`, `address`, `public_key_pem`, `encrypted_private_key`

### Bezpieczeństwo klucza prywatnego

- Użytkownik podaje passphrase (hasło‑fraza). Z passphrase i losowej soli (`salt`) dla danego portfela wyprowadzany jest klucz (PBKDF2‑HMAC‑SHA256, 390k iteracji),
  który służy do szyfrowania klucza prywatnego kont (Fernet).
- W `wallet_meta.verifier` zapisywany jest zaszyfrowany token kontrolny (np. „wallet‑unlock”), który pozwoli w przyszłości zweryfikować poprawność passphrase bez odsłaniania klucza.

### Użycie z CLI

Utwórz portfel i automatycznie dodaj kilka kont (Windows/PowerShell: użyj `py` zamiast `python`):

```bash
py wallet_node.py --label "My Wallet" --passphrase "twoja długa passphrase" --accounts 2
```

Polecenie:
- tworzy (jeśli nie istnieje) plik bazy `db/wallet_My_Wallet.db`,
- inicjuje `wallet_meta` z losową solą i weryfikatorem,
- tworzy podaną liczbę kont, szyfrując klucze prywatne passphrase.

Aby wyświetlić konta w portfelu, uruchom ponownie to samo polecenie (inicjalizacja jest idempotentna) – na końcu zobaczysz listę kont.

### API (Python)

Minimalny przykład programistyczny:

```python
from wallet.manager import WalletManager

wm = WalletManager("db/wallet_My_Wallet.db")
wm.create_wallet("My Wallet", "very long passphrase")
acc = wm.create_account("Main", "very long passphrase")
for a in wm.list_accounts():
    print(a.id, a.address)
```

### Uwagi i ograniczenia

- Brak centralnej bazy `wallets.db` – każdy portfel to osobny plik.
- Adres konta to skrót: `ks` + pierwsze 38 znaków SHA‑256 z klucza publicznego (PEM).
- Zmiana passphrase i tryb „odblokuj portfel” mogą zostać dodane później, wykorzystując pole `verifier` w `wallet_meta`.