## Wallet (Portfel)

Portfel umożliwia zarządzanie kontami kryptowalutowymi z kluczami ECDSA secp256k1.

### Tworzenie portfela

```bash
python ../run_wallet.py --name crypto_bro_wallet init
```

### Dodanie konta

```bash
python ../run_wallet.py --name crypto_bro_wallet add Bill_Gates
# Zostaniesz poproszony o hasło do zaszyfrowania klucza prywatnego
```

#### Lista wszystkich kont

```bash
python ../run_wallet.py --name crypto_bro_wallet list
```

#### Szczegóły konta

```bash
python ../run_wallet.py --name crypto_bro_wallet show Bill_Gates
```

#### Wyświetlenie klucza prywatnego

```bash
python ../run_wallet.py --name crypto_bro_wallet show-priv Bill_Gates
# Wymaga podania hasła do odszyfrowania
```

#### Usunięcie konta

```bash
python ../run_wallet.py --name crypto_bro_wallet delete Bill_Gates
```

#### Pomoc

```bash
python ../run_wallet.py --help
```

### Przykłady użycia

```bash
# 1. Utwórz nowy portfel
python ../run_wallet.py --name demo init

# 2. Dodaj trzy konta
python ../run_wallet.py --name demo add Bill_Gates
python ../run_wallet.py --name demo add Mark_Zuckerberg
python ../run_wallet.py --name demo add Elon_Musk

# 3. Wyświetl wszystkie konta
python ../run_wallet.py --name demo list

# 4. Pokaż szczegóły konkretnego konta
python ../run_wallet.py --name demo show Bill_Gates

# 5. Wyświetl klucz prywatny (wymaga hasła)
python ../run_wallet.py --name demo show-priv Bill_Gates

# 6. Usuń konto
python ../run_wallet.py --name demo delete Elon_Musk
```

### Uwagi

- Klucze prywatne są szyfrowane hasłem
- Format kluczy: ECDSA secp256k1 (bitcoin), eksport PEM (PKCS#8)

trudności problemu logarytmu dyskretnego na krzywych eliptycznych (ECDLP).
Serializacja prywatnego klcuza PEM

---