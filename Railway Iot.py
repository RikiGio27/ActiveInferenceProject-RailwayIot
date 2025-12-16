import random

try:
    import wandb
    WANDB = True
except ImportError:
    WANDB = False

TIME_STEPS = 50

# Stati dello scambio
STABLE_A = 0.0
TRANSITION = 0.5
STABLE_B = 1.0

# Velocità del treno
V_NOMINAL = 10
V_SLOW = 4
V_STOP = 0

# Incertezza
UNCERTAINTY_THRESHOLD = 0.4
SENSOR_NOISE = 0.1

# SWITCH (STATO FISICO REALE)

class Switch: 
    # Scambio ferroviario (stato reale non osservabile direttamente)
    def __init__(self):
        self.state = STABLE_A

    def update(self, t):
        # Lo scambio entra in transizione per un certo intervallo
        if 20 <= t <= 30:
            self.state = TRANSITION
        else:
            self.state = STABLE_B


# SENSORE IIoT + SPOOFING (FDIA)

class SwitchSensor:
    #Sensore IIoT vulnerabile a spoofing.
    def read(self, true_state, attack=False):
        noise = random.uniform(-SENSOR_NOISE, SENSOR_NOISE)
        measured = true_state + noise

        # Attacco FDIA: maschera la transizione come stato stabile
        if attack:
            measured = STABLE_A

        return max(0.0, min(1.0, measured))


# BELIEF ESTIMATOR (LIVELLO EPISTEMICO)

class BeliefEstimator:
    #Stima lo stato dello scambio e l'incertezza associata.
    def __init__(self):
        self.estimate = STABLE_A
        self.uncertainty = 0.2

    def update(self, sensor_value):
        self.estimate = sensor_value
        # Incertezza massima vicino allo stato di transizione
        self.uncertainty = min(1.0, abs(sensor_value - 0.5) * 2)


# TRENO

class Train:
    # Dinamica del treno 
    def __init__(self):
        self.velocity = V_NOMINAL

    def apply_action(self, action):
        if action == "maintain":
            self.velocity = V_NOMINAL
        elif action == "epistemic_slow":
            self.velocity = V_SLOW
        elif action == "pragmatic_stop":
            self.velocity = V_STOP


# EXPECTED FREE ENERGY
def expected_free_energy(belief, action):

    # EFE = Rischio + Costo - Valore Epistemico
   
    # Rischio: alto se stimato vicino alla transizione
    risk = 1.0 - abs(belief.estimate - TRANSITION) * 2
    risk = max(0.0, min(1.0, risk))

    # Costo dell'azione
    if action == "maintain":
        cost = 0.1
    elif action == "epistemic_slow":
        cost = 0.3
    else:
        cost = 0.6

    # Valore epistemico: solo l'azione epistemica riduce incertezza
    epistemic_value = belief.uncertainty if action == "epistemic_slow" else 0.0

    efe = risk + cost - epistemic_value
    return efe

# CONTROLLER (ACTIVE INFERENCE)

class Controller:
    # Seleziona l'azione che minimizza l'Expected Free Energy.
  
    def decide(self, belief):
        actions = ["maintain", "epistemic_slow", "pragmatic_stop"]
        efe_values = {a: expected_free_energy(belief, a) for a in actions}
        best_action = min(efe_values, key=efe_values.get)
        return best_action, efe_values

# SIMULAZIONE

def simulate():

    if WANDB:
        wandb.init(
            project="railway-iot-active-inference",
            name="interlocking_spoofing",
            config={"scenario": "Railway IoT - FDIA"}
        )

    switch = Switch()
    sensor = SwitchSensor()
    belief = BeliefEstimator()
    train = Train()
    controller = Controller()

    for t in range(TIME_STEPS):

        switch.update(t)

        attack_active = 22 <= t <= 28
        sensor_value = sensor.read(switch.state, attack_active)

        belief.update(sensor_value)

        action, efe_vals = controller.decide(belief)
        train.apply_action(action)

        log = {
            "time": t,
            "switch_real": switch.state,
            "switch_estimated": belief.estimate,
            "uncertainty": belief.uncertainty,
            "attack_active": attack_active,
            "action": action,
            "efe_maintain": efe_vals["maintain"],
            "efe_epistemic": efe_vals["epistemic_slow"],
            "efe_pragmatic": efe_vals["pragmatic_stop"],
            "train_velocity": train.velocity
        }

        if WANDB:
            wandb.log(log)

        print(f"[t={t}] real={switch.state} est={belief.estimate:.2f} "
              f"unc={belief.uncertainty:.2f} attack={attack_active} "
              f"action={action} v={train.velocity}")

    if WANDB:
        wandb.finish()

if __name__ == "__main__":
    simulate()
