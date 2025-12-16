Questo repository contiene una simulazione semplificata di un sistema **Railway IoT** per la gestione della sicurezza in presenza di **spoofing cyber-physical attacks** su sistemi di **interlocking digitale ferroviario**.

Il progetto ha il fine di studiare come un approccio ispirato all’**Active Inference** e alla minimizzazione dell'**Expected Free Energy** possa migliorare la resilienza dei sistemi Railway IoT contro spoofing cyber-physical attacks, 
preservando l'omeostasi (e migliorando le performance) del sistema tramite un bilanciamento tra sicurezza immediata (azioni pragmatiche) e riduzione dell’incertezza (azioni epistemiche).
## Scenario

**Railway IoT – gestione contro spoofing cyber-physical attacks**

Un treno percorre una linea controllata da un sistema di interlocking digitale e da sensori IIoT.  
Il controller non osserva direttamente lo stato reale dello scambio, ma riceve misure rumorose e potenzialmente manipolate da un attaccante.

Il modello include i seguenti elementi:

- **Scambio ferroviario (Switch)**  
  Stato fisico reale non direttamente osservabile, che può trovarsi in una fase di transizione pericolosa.

- **Sensori IIoT**  
  Forniscono osservazioni rumorose e vulnerabili a spoofing (FDIA).

- **Stima epistemica (Belief)**  
  Il sistema mantiene una stima dello stato dello scambio e un livello di incertezza associato.

- **Azioni pragmatiche**  
  Azioni orientate alla sicurezza immediata (es. arresto del treno).

- **Azioni epistemiche**  
  Azioni che riducono l’incertezza a costo di una temporanea perdita di performance (es. rallentamento).

- **Expected Free Energy (EFE)**  
  Il controller seleziona l’azione che minimizza una versione semplificata dell’EFE, composta da:
  - rischio,
  - costo dell’azione,
  - valore epistemico.

## Obiettivo

L’obiettivo della simulazione è mostrare come:
- l’incertezza giochi un ruolo centrale nelle decisioni,
- le azioni epistemiche possano essere interpretate come un investimento per il futuro,
- la minimizzazione dell’Expected Free Energy consenta di preservare l’omeostasi del sistema anche in presenza di attacchi cyber-physical.
