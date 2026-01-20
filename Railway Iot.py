import random
import numpy as np

try:
    import wandb
    WANDB = True
except ImportError:
    WANDB = False

# --- COSTANTI DI SISTEMA ---
TIME_STEPS = 50

STABLE_A = 0.0 # Rappresenta lo stato di riposo "binario" A

TRANSITION = 0.5 # Rappresenta lo scambio "in movimento"

STABLE_B = 1.0 # Rappresenta lo stato di riposo "binario" B

V_NOMINAL = 10 # Associata all'azione Pragmatica (maintain). È la velocità di crociera. 
               # Si usa quando l'agente è sicuro che lo stato sia stabile (A o B).

V_SLOW = 4 # Associata all'azione Epistemica (epistemic_slow). Il treno rallenta, riduce il rischio
           # È il "costo" che l'agente paga per ottenere sicurezza.

V_STOP = 0 # Associata all'azione di Sicurezza Massima (pragmatic_stop)

# Parametri Bayesiani
SENSOR_NOISE = 0.05
ANOMALY_THRESHOLD = 0.3  # Soglia oltre la quale l'agente sospetta un attacco

# --- AMBIENTE FISICO (GROUND TRUTH) ---
class Switch: 
    def __init__(self):
        self.state = STABLE_A

    def update(self, t):
        if 20 <= t <= 30:
            self.state = TRANSITION
        elif t > 30:
            self.state = STABLE_B
        else:
            self.state = STABLE_A

class SwitchSensor:
    def read(self, true_state, attack=False):
        if attack:
            # FDIA: Forza la lettura a STABLE_A nonostante la realtà sia diversa
            return STABLE_A
        
        noise = random.uniform(-SENSOR_NOISE, SENSOR_NOISE)
        return max(0.0, min(1.0, true_state + noise))

# --- AGENTE DI ACTIVE INFERENCE (LIVELLO EPISTEMICO) ---
class BeliefEstimator:
    """
    Rappresenta il Modello Generativo dell'agente.
    Confronta le osservazioni (sensore) con le aspettative (modello interno).
    """
    def __init__(self):
        self.estimate = STABLE_A
        self.uncertainty = 0.1
        self.anomaly_detected = False

    def predict_expected_state(self, t):
        """Modello interno: cosa si aspetta l'agente in base al tempo."""
        if 20 <= t <= 30: return TRANSITION
        if t > 30: return STABLE_B
        return STABLE_A

    def update(self, sensor_value, t):
        # 1. Previsione basata sul modello interno
        expected_state = self.predict_expected_state(t)
        
        # 2. Calcolo dell'Errore di Predizione (Surprise)
        prediction_error = abs(sensor_value - expected_state)
        
        # 3. Logica di Resilienza: se l'errore è troppo alto, il sensore è inaffidabile
        if prediction_error > ANOMALY_THRESHOLD:
            self.anomaly_detected = True
            # L'incertezza schizza al massimo perché i dati non sono coerenti
            self.uncertainty = 1.0 
            # In caso di anomalia, l'agente si fida più del modello interno che del sensore
            self.estimate = expected_state 
        else:
            self.anomaly_detected = False
            self.estimate = sensor_value
            # L'incertezza naturale aumenta durante la transizione (stato instabile)
            self.uncertainty = 1.0 - abs(self.estimate - TRANSITION) * 2
            self.uncertainty = max(0.1, min(1.0, self.uncertainty))

# --- DINAMICA DEL TRENO ---
class Train:
    def __init__(self):
        self.velocity = V_NOMINAL

    def apply_action(self, action):
        if action == "maintain": self.velocity = V_NOMINAL
        elif action == "epistemic_slow": self.velocity = V_SLOW
        elif action == "pragmatic_stop": self.velocity = V_STOP

# --- SELEZIONE DELL'AZIONE TRAMITE EFE ---
def expected_free_energy(belief, action):
    """
    G = Rischio + Costo - Valore Epistemico
    """
    # Rischio: basato sulla stima dello stato e sull'incertezza
    # Se lo stato è di transizione o l'incertezza è alta, il rischio aumenta
    risk = (1.0 - abs(belief.estimate - TRANSITION) * 2) + (belief.uncertainty * 0.5)
    risk = max(0.0, min(1.5, risk))

    # Costi operativi (Prior Preference)
    costs = {"maintain": 0.1, "epistemic_slow": 0.4, "pragmatic_stop": 0.8}
    cost = costs[action]

    # Valore Epistemico: quanto l'azione riduce l'incertezza
    # L'azione 'slow' permette di raccogliere dati più precisi (simbolicamente)
    epistemic_value = belief.uncertainty if action == "epistemic_slow" else 0.0

    return risk + cost - epistemic_value

class Controller:
    def decide(self, belief):
        actions = ["maintain", "epistemic_slow", "pragmatic_stop"]
        efe_values = {a: expected_free_energy(belief, a) for a in actions}
        best_action = min(efe_values, key=efe_values.get)
        return best_action, efe_values

# --- SIMULAZIONE ---
def simulate():
    if WANDB:
        wandb.init(project="railway-active-inference", name="resilient-interlocking")

    switch = Switch()
    sensor = SwitchSensor()
    belief = BeliefEstimator()
    train = Train()
    controller = Controller()

    for t in range(TIME_STEPS):
        # Evoluzione fisica
        switch.update(t)
        
        # Attacco FDIA attivo tra t=22 e t=28
        attack_active = 22 <= t <= 28
        sensor_value = sensor.read(switch.state, attack_active)

        # Inferenza (Belief Update)
        belief.update(sensor_value, t)

        # Azione basata su Active Inference
        action, efe_vals = controller.decide(belief)
        train.apply_action(action)

        log = {
            "time": t,
            "switch_real": switch.state,
            "switch_measured": sensor_value,
            "belief_estimate": belief.estimate,
            "uncertainty": belief.uncertainty,
            "anomaly": int(belief.anomaly_detected),
            "velocity": train.velocity,
            "action": action
        }

        if WANDB: wandb.log(log)
        
        status = "⚠️ ATTACK!" if attack_active else "  SAFE   "
        anomaly = "❗ANOMALY DETECTED" if belief.anomaly_detected else ""
        print(f"[t={t}] {status} Real:{switch.state} Sensor:{sensor_value:.2f} "
              f"Est:{belief.estimate:.2f} Unc:{belief.uncertainty:.2f} "
              f"Act:{action} {anomaly}")

    if WANDB: wandb.finish()

if __name__ == "__main__":
    simulate()
