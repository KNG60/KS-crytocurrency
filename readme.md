# Prosta Kryptowaluta w Pythonie

Projekt implementuje uproszczony system kryptowaluty oparty na technologii **blockchain**.  
System składa się z dwóch głównych komponentów:

- **Node (Węzeł):** Utrzymuje łańcuch bloków, zarządza siecią i walidacją transakcji.
- **Wallet (Portfel):** Zarządza tożsamością użytkownika, kluczami kryptograficznymi i tworzeniem transakcji.

---

## Plan Projektu

### **Etap 1: Sieć i bezpieczny portfel**

- [x] **Wallet:** Generowanie i przechowywanie pary kluczy kryptograficznych
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
```

### Instalacja zależności

```bash
pip install -r requirements.txt
```

### Wyczyszczenie baz danych

```bash
rm -r db/*
```

---

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

---

### Wallet (Portfel)

Portfel umożliwia zarządzanie kontami kryptowalutowymi z kluczami ECDSA secp256k1.

### Tworzenie portfela

```bash
python run_wallet.py --name crypto_bro_wallet init
```

### Dodanie konta

```bash
python run_wallet.py --name crypto_bro_wallet add Bill_Gates
# Zostaniesz poproszony o hasło do zaszyfrowania klucza prywatnego
```

#### Lista wszystkich kont

```bash
python run_wallet.py --name crypto_bro_wallet list
```

#### Szczegóły konta

```bash
python run_wallet.py --name crypto_bro_wallet show Bill_Gates
```

#### Wyświetlenie klucza prywatnego

```bash
python run_wallet.py --name crypto_bro_wallet show-priv Bill_Gates
# Wymaga podania hasła do odszyfrowania
```

#### Usunięcie konta

```bash
python run_wallet.py --name crypto_bro_wallet delete Bill_Gates
```

#### Pomoc

```bash
python run_wallet.py --help
```

### Przykłady użycia

```bash
# 1. Utwórz nowy portfel
python run_wallet.py --name demo init

# 2. Dodaj trzy konta
python run_wallet.py --name demo add Bill_Gates
python run_wallet.py --name demo add Mark_Zuckerberg
python run_wallet.py --name demo add Elon_Musk

# 3. Wyświetl wszystkie konta
python run_wallet.py --name demo list

# 4. Pokaż szczegóły konkretnego konta
python run_wallet.py --name demo show Bill_Gates

# 5. Wyświetl klucz prywatny (wymaga hasła)
python run_wallet.py --name demo show-priv Bill_Gates

# 6. Usuń konto
python run_wallet.py --name demo delete Elon_Musk
```

### Demo

```bash
# Uruchom kompletne demo pokazujące wszystkie funkcje
python wallet/demo_wallet.py
```

### Uwagi

- Klucze prywatne są szyfrowane hasłem
- Format kluczy: ECDSA secp256k1 (bitcoin), eksport PEM (PKCS#8)

trudności problemu logarytmu dyskretnego na krzywych eliptycznych (ECDLP).
Serializacja prywatnego klcuza PEM

---
