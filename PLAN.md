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
