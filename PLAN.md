## Plan Projektu

### **Etap 1: Sieć i bezpieczny portfel**

- [x] **Wallet:** Generowanie i przechowywanie pary kluczy kryptograficznych
- [x] **Node:** Możliwość komunikacji z innymi węzłami w sieci
- [x] **Node:** Rejestracja i przechowywanie informacji o innych węzłach w sieci

### **Etap 2: Prosty łańcuch bloków**

- [x] **Node:** Utworzenie pierwszego bloku (bloku genezy)
- [x] **Node:** Generowanie haszy bloków w celu zapewnienia integralności
- [x] **Node:** Sprawdzanie poprawności i spójności łańcucha bloków
- [x] **Node:** Rozgłaszanie nowych bloków do innych węzłów i odbieranie ich od sieci

### **Etap 3: Transakcje i konsensus**

- [x] **Wallet:** Tworzenie i podpisywanie transakcji między użytkownikami
- [x] **Node:** Gromadzenie oczekujących transakcji w sieci
- [x] **Node:** Mechanizm kopania bloków i ustalania konsensusu (Proof-of-Work)
- [x] **Node:** Dodawanie nagród dla górników (transakcje coinbase)
- [x] **Node:** Weryfikacja transakcji (poprawność podpisu, wystarczające saldo, ochrona przed podwójnym wydatkowaniem)
- [x] **Node:** Obliczanie sald użytkowników na podstawie historii transakcji

### **Etap 4: Kopanie asynchroniczne i obsługa forków**

- [ ] **Node:** Zasada „najdłuższego łańcucha” w przypadku konfliktów między węzłami
- [ ] **Node:** Synchronizacja i zastępowanie lokalnego łańcucha, jeśli pojawi się dłuższy
- [ ] **Node:** Symulacja działania złośliwego węzła tworzącego konkurencyjny łańcuch

### **Etap 5: Sprawozdanie końcowe**

- [ ] **Wallet:** Wyjaśnienie zastosowanej kryptografii i podpisów cyfrowych
- [ ] **Node:** Opis architektury systemu i sposobu działania węzłów
- [ ] **Node:** Podsumowanie wyników testów, bezpieczeństwa i symulacji działania sieci
