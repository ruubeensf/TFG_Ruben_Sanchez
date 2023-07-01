# TFG Rubén Sánchez Fernández
# Aplicació de Time Tracking via API de Teamwork

Aquest projecte és una aplicació de Time Tracking que utilitza l'API de Teamwork per a la gestió de tasques i projectes.

## Manual d'instalació amb Docker

Per a executar el projecte, cal descarregar tots els arxius del repositori i tenir instal·lat Docker.

Després de descarregar els arxius, s'ha de modificar la línia 10 del fitxer main.py. A aquesta línia s'ha d'introduir la clau d'accés a l'API de Teamwork, per assignar-la a la variable API_KEY. Per a obtenir la clau d'accés, cal seguir els següents passos:

1. Entrar a Teamwork
2. Anar al perfil d'usuari
3. Clicar a "Edit my profile"
4. Clicar a "API & Mobile"
5. Clicar a "Show your token"
6. Copiar la clau d'accés

Un cop copiada la clau d'accés, s'ha de modificar la línia 10 del fitxer main.py i posar la clau d'accés entre cometes simples.

Ara ja es pot executar el projecte. Per a fer-ho, cal obrir una terminal, situar-se a la carpeta on s’ha descarregat el projecte i executar les següents comandes:

```
make build

make run
```

Aquestes comandes crearan una imatge de Docker amb Python i tots els requeriments instal·lats, i executaran el projecte. Un cop executada, es pot accedir a l'aplicació a través de la següent URL:

```
http://localhost:5000
```
