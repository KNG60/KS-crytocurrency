# Demo Scripts

## 1. run_demo.py

Demonstracja wszystkich funkcji portfela i transakcji

### Użycie:

```bash
python run_demo.py
```

## 2. run_random_network.py

Skrypt:

- Tworzy losową liczbę węzłów
- Pierwszy węzeł jest węzłem bootstrapowym (bez seedów)
- Każdy kolejny węzeł otrzymuje losową liczbę seedów (1-5) z już uruchomionych węzłów
- Wszystkie węzły używają portów od 5000 wzwyż

### Użycie:

```bash
python run_random_network.py
```

## 3. run_two_networks.py

Skrypt (dwie izolowane sieci):

- Buduje dwie oddzielne sieci
- Rejestruje węzły w menedżerze grafu, uruchamia koparki
- Łączy obie sieci po naciśnięciu Enter 

### Użycie:

```bash
python run_two_networks.py
```

Po starcie skrypt wypisze adres UI oraz zapyta o parę portów do połączenia. Naciśnij Enter, aby użyć domyślnej pary (pierwsze węzły obu sieci) albo podaj dwie wartości, np. „5201 5302”.

## 4. run_demo_wallet.py

Skrypt:

- Demonstruje wszystkie operacje portfela
- Dodaje trzy konta: alice, bob, charlie
- Pokazuje obsługę błędów (błędne hasło, nieistniejące konto)
- Usuwa jedno konto i pokazuje stan po usunięciu

### Użycie:

```bash
python run_demo_wallet.py
```


