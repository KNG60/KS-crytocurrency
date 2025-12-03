## Wallet (Portfel)

Portfel umożliwia zarządzanie kontami kryptowalutowymi z kluczami ECDSA secp256k1.

### Wyczyszczenie baz danych

```bash
rm -rf db/*
```

### Dodanie konta

```bash
python ../run_wallet.py add alice
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
# 1. Dodaj konta
python ../run_wallet.py add alice
python ../run_wallet.py add bob

# 2. Wyświetl wszystkie konta
python ../run_wallet.py list

# 3. Pokaż szczegóły konta
python ../run_wallet.py show alice

# 4. Wyświetl klucz prywatny (wymaga hasła)
python ../run_wallet.py show-priv alice

# 5. Utwórz transakcję od Alice do Boba
python ../run_wallet.py create-tx alice bob 25.0
# Wprowadź hasło Alice

# 6. Usuń konto
python ../run_wallet.py delete alice
```

### Uwagi

- Klucze prywatne są szyfrowane hasłem
- Format kluczy: ECDSA secp256k1 (bitcoin), eksport PEM (PKCS#8)
