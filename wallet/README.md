## Wallet (Portfel)

Portfel umożliwia zarządzanie kontami kryptowalutowymi z kluczami ECDSA secp256k1.

### Wyczyszczenie bazy danych

```bash
rm -rf db/*
```

### Tworzenie portfela

```bash
python ../run_wallet.py init
```

### Dodanie konta

```bash
python ../run_wallet.py add Bill_Gates
# Zostaniesz poproszony o hasło do zaszyfrowania klucza prywatnego
```

### Lista wszystkich kont

```bash
python ../run_wallet.py list
```

### Szczegóły konta

```bash
python ../run_wallet.py show Bill_Gates
```

### Wyświetlenie klucza prywatnego

```bash
python ../run_wallet.py show-priv Bill_Gates
# Wymaga podania hasła do odszyfrowania
```

### Usunięcie konta

```bash
python ../run_wallet.py delete Bill_Gates
```

### Tworzenie podpisanej transakcji

```bash
python ../run_wallet.py create-tx alice bob 25.0
# Wymaga podania hasła do podpisania transakcji
```

### Pomoc

```bash
python ../run_wallet.py --help
```

### Przykład użycia

```bash
# 1. Utwórz nowy portfel
python ../run_wallet.py init

# 2. Dodaj konta
python ../run_wallet.py add alice
python ../run_wallet.py add bob

# 3. Wyświetl wszystkie konta
python ../run_wallet.py list

# 4. Pokaż szczegóły konta
python ../run_wallet.py show alice

# 5. Wyświetl klucz prywatny (wymaga hasła)
python ../run_wallet.py show-priv alice

# 6. Utwórz transakcję od Alice do Boba
python ../run_wallet.py create-tx alice bob 25.0
# Wprowadź hasło Alice

# 7. Usuń konto
python ../run_wallet.py delete alice
```

### Uwagi

- Klucze prywatne są szyfrowane hasłem
- Format kluczy: ECDSA secp256k1 (bitcoin), eksport PEM (PKCS#8)
