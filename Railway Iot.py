import random
import numpy as np

try:
    import wandb
    WANDB = True
except ImportError:
    WANDB = False

TIME_STEPS = 50
STABLE_A, TRANSITION, STABLE_B = 0.0, 0.5, 1.0
V_NOMINAL, V_SLOW, V_STOP = 10, 4, 0
SENSOR_NOISE = 0.05
ANOMALY_THRESHOLD = 0.3 

#MODULO DI PERCEZIONE
class BeliefEstimator:
    def __init__(self):
        self.estimate = STABLE_A
        self.uncertainty = 0.1
        self.detected = False

    def update(self, sensor_value, t):
        expected = TRANSITION if 20 <= t <= 30 else (STABLE_B if t > 30 else STABLE_A)
        prediction_error = abs(sensor_value - expected)
        
        if prediction_error > ANOMALY_THRESHOLD:
            self.detected = True
            self.uncertainty = 1.0 
            self.estimate = expected
        else:
            self.uncertainty = min(0.9, prediction_error * 2.5 + 0.1)
            weight = 0.6  # Quanto l'agente si fida del sensore (0.6 = 60%)
            self.estimate = (weight * sensor_value) + ((1 - weight) * expected)

#MODULO DECISIONALE
class Controller:
    def __init__(self):
        self.costs = {"maintain": 0.1, "epistemic_slow": 0.4, "pragmatic_stop": 0.8}

    def expected_free_energy(self, belief, action):
        physical_danger = (1.0 - abs(belief.estimate - TRANSITION) * 2)
        risk = physical_danger * belief.uncertainty * 2.0 
        
        if action == "pragmatic_stop":
            return self.costs[action] 
        elif action == "epistemic_slow":
            return (risk * 0.5) + self.costs[action] - (belief.uncertainty * 0.5)
        else:
            return risk + self.costs[action]

    def decide(self, belief, scenario):
        if belief.detected and scenario == "attacco":
            return "pragmatic_stop"
        
        actions = ["maintain", "epistemic_slow", "pragmatic_stop"]
        scores = {a: self.expected_free_energy(belief, a) for a in actions}
        return min(scores, key=scores.get)

#L'ATTUATORE 
class Train:
    def __init__(self):
        self.velocity = V_NOMINAL

    def actuate(self, action):
        """Esegue la decisione modificando i parametri operativi (velocità)."""
        if action == "maintain":
            self.velocity = V_NOMINAL
        elif action == "epistemic_slow":
            self.velocity = V_SLOW
        else:
            self.velocity = V_STOP

#CICLO DI SIMULAZIONE
def simulate(scenario="degradato"): # Scrivere lo scenario che si desidera testare (in corrispondenza del main)
    if WANDB:
        wandb.init(project="digitalInterlocking-activeInference", name=f"scenario-{scenario}")

    belief_module = BeliefEstimator()
    controller_module = Controller()
    train_module = Train() 
    
    for t in range(TIME_STEPS):
        switchReal = TRANSITION if 20 <= t <= 30 else (STABLE_B if t > 30 else STABLE_A)
        
        # Generazione Misura (Ambiente)
        switchSensor = switchReal + random.uniform(-SENSOR_NOISE, SENSOR_NOISE)
        if scenario == "attacco" and 22 <= t <= 28:
            switchSensor = STABLE_A 
        elif scenario == "degradato" and 15 <= t <= 35:
            switchSensor = switchReal + random.uniform(-0.25, 0.25)
        
        # Fasi del ciclo:
        belief_module.update(switchSensor, t)                      # 1. Percezione
        action = controller_module.decide(belief_module, scenario) # 2. Decisione
        train_module.actuate(action)                               # 3. Attuazione 
            
        if WANDB:
            wandb.log({
                "switch_real": switchReal, "switch_measured": switchSensor,
                "belief_estimate": belief_module.estimate, "uncertainty": belief_module.uncertainty,
                "velocity": train_module.velocity
            })
        
        print(f"[t={t}] Unc:{belief_module.uncertainty:.2f} | Act:{action:15} | Vel:{train_module.velocity}")

    if WANDB: wandb.finish()

if __name__ == "__main__":
    simulate(scenario="degradato") # Scrivere lo scenario che si desidera testare (in corrispondenza del ciclo di simulazione)
