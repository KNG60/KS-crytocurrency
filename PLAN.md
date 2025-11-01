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


---

W tym etapie dodano:
- Struktury `node.blockchain.Block` i `node.blockchain.Blockchain` (Proof of Work, walidacja, blok genezy).
- Przechowywanie bloków w SQLite: `node.storage.ChainStorage`.
- Endpointy HTTP:
	- `GET /blocks` – zwraca cały łańcuch,
	- `POST /blocks` – przyjmuje nowy blok i waliduje go,
	- `POST /mine` – (tylko rola miner) wydobywa nowy blok.
- Nowe parametry uruchomienia: `--role full|miner`, `--difficulty <int>`.

Uruchomienie węzłów:

```bash
# Pełny węzeł
py run_node.py --port 5000 --role full

# Węzeł górnik z trudnością 4 (4 zera hex na początku hash)
py run_node.py --port 5001 --role miner --difficulty 4 --seeds 127.0.0.1:5000
```

Kopalnia i podgląd:

```bash
# Ręczne wydobycie bloku na minerze
curl -X POST http://127.0.0.1:5001/mine

# Podgląd łańcucha na pełnym węźle
curl http://127.0.0.1:5000/blocks
```

#### Proof of Work (PoW)

Użyty algorytm: prosty SHA-256 na nagłówku bloku z licznikiem `nonce`.
Warunek: hash w zapisie heksadecymalnym ma D wiodących zer (D = difficulty).

Matematycznie: wymagamy, by $H(\text{header} \Vert \text{nonce}) < \text{Target}_D$.
Prawdopodobieństwo trafienia: $16^{-D} = 2^{-4D}$, więc oczekiwana liczba prób: $16^{D} = 2^{4D}$.

Dlaczego: deterministyczny, prosty w implementacji i weryfikacji, parametryzowalny trudnością, wystarczający edukacyjnie dla tego etapu.


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
