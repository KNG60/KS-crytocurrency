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

## 3. run_demo_wallet.py

Skrypt:

- Demonstruje wszystkie operacje portfela
- Dodaje trzy konta: alice, bob, charlie
- Pokazuje obsługę błędów (błędne hasło, nieistniejące konto)
- Usuwa jedno konto i pokazuje stan po usunięciu

### Użycie:

```bash
python run_demo_wallet.py
```


