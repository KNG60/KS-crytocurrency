# Prosty wezeł *Wallet*
Prosy wezeł *wallet*. Z możliwością tworzenia i przechowywania rachunków, wykonywania, podpisywaniem transakcji.

Zarządzania tożsamościami i kluczami kryptograficznymi użytkownika w zdecentralizowanym systemie.

Nie kopie bloków ani nie utrzymuje blockchaina

## Założenia
### Zarządzanie kontami
- Tworzenie nowego konta
- Zapis kluczy w lokalnej bazie SQLite
- Szyfrowanie klucza prywatnego hasłem użytkownika.
- Nadawanie kontu etykiety
- Listowanie wszystkich kont zapisanych lokalnie.
- Eksport publicznego klucza

### Podpisy kryptograficzne
- Podpisuje transakcje
- Weryfikacja podpisu przy pomocy klucza publicznego

### Tworzenie i wysyłanie transakcji
- stworzenie i wysłanie transakcji
- Python skrypt tworzący instancje *Wallet*
- API HTTP do odpytywania

### TODO
- wszystko