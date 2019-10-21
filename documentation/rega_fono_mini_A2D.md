# Rega Fono mini A2D

## Interface
  1) RCA stereo input connector, kobles til kilde

  2) RCA stereo  output connector, kobles til ut-enhet

  3) USB A Connector, Kobles til datamaskin som kjører denne applikasjonen

  4) Volumjustering. Setter forsterkningen til inngangssignalet

## Virkemåte
  Den svarte boksen har en TI/Burr Brown PCM2900C Audio integrert krets med USB interface.
  Denne IC kretsen har en komplett analog frontend for å omforme et analogt single ended signal til et 16 bit PCM (Pulskodemodulasjon).

  Default samplingsrate og Kvantiseringsmetode er hardkodet. Etter at denne applikasjonen har fått kontakt med den svarte boksen står man fritt til å konfigurere samplingsraten og Kvantiseringsmetoden som benyttes av PCM2900C.

  Boksen er satt opp til å streame rådata ut av boksen og til verten som kobler seg til USB porten.
  Verten kan sette opp registrene i chipen.

  ## Konfigurering av PCM2900C
   
