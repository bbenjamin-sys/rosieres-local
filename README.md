# Rosières Local

Home Assistant custom integration for **Rosières / Candy / Haier "Simply-Fi" dishwashers**, talking to the
appliance **directly on the LAN** (no cloud, no hOn account).

Developed and tested on a **Rosières RI 6E4L0FB-47**. Other Simply-Fi dishwashers using the same local API
(`/http-read.json`, `/http-write.json`) will probably work, but program codes may differ.

> Experimental. Use at your own risk. Not affiliated with Rosières, Candy or Haier.

*Résumé en français plus bas.*

## ⚠️ Before you start: enable remote control and keep it on

The dishwasher only accepts commands when **remote control (Wi-Fi mode)** is enabled **on the appliance
itself**. This is a safety feature: it cannot be enabled from Home Assistant, from the app or over the network.

| Remote control | What works |
|---|---|
| **On** (`StatoWiFi=1`) | Reading the status **and** commands (Start, Stop) |
| **Off** (`StatoWiFi=0`) | Reading the status only. Every command fails with `{'response': 'READ ONLY'}` |

**How to enable it** (RI 6E4L0FB-47, manual section 16): with the appliance switched on, hold the
**PROGR. 3sec** button for **3 seconds**. LEDs **P3 and P4** light up and stay on.

**It switches off when:**

- the appliance loses power (unplugged, breaker, power cut);
- the appliance is switched off and on with **On/Off** during a cycle (P3 and P4 blink);
- **PROGR. 3sec** or **START/CANCEL** is held for 3 seconds.

Each time, enable it again on the panel. Keep the appliance switched on (standby) to keep remote control
available.

**How to check it in Home Assistant:** the binary sensor **"Connexion Wi-Fi"**
(`binary_sensor.<name>_controle_a_distance`) must be **on**. An automation that notifies you when it turns
off saves a failed start later:

```yaml
alias: Dishwasher remote control off
triggers:
  - trigger: state
    entity_id: binary_sensor.lave_vaisselle_rosieres_controle_a_distance
    to: "off"
    for: "00:05:00"
actions:
  - action: notify.notify
    data:
      message: "Dishwasher remote control is off: hold PROGR. 3sec for 3 s on the appliance."
```

> **Status frozen for days?** If the state never changes (same remaining time for hours), the Wi-Fi module
> is stuck. Unplug the dishwasher for one minute, plug it back in, then enable remote control again.

## Features

| Platform | Entities |
|---|---|
| `sensor` | State, current program, remaining time, delayed start, error code, **water hardness** (read only), raw settings (diagnostic) |
| `binary_sensor` | Door, remote control (Wi-Fi), salt missing, rinse aid missing, Eco, auto door opening, Extra Dry, half load, 3-in-1 |
| `select` | Program used by the next start |
| `switch` | Next-cycle options: Extra Dry, auto door opening, half load, 3-in-1, Eco |
| `number` | Next-cycle delayed start (0-23 h) |
| `button` | Start, Stop (reset) |

Diagnostics can be downloaded from the device page (host and key are redacted).

The program selector and the option switches **do not start anything**: they are only sent when you press
**Start**. Start is refused if the door is open or if remote control is disabled on the appliance.

### Programs

| Program | API code | `w1` | Theoretical duration |
|---|---:|---:|---:|
| Intensive 75 °C | P2 | 1 | 130 min |
| Universal 60 °C | P5 | 2 | 120 min |
| Eco 45 °C | P8 | 3 | 232 min |
| Pre-wash | P12 | 4 | 5 min |
| Total Care 50 °C | P13 | 5 | 100 min |

Only **Pre-wash (P12)** and **Stop (`Reset=1`)** have been validated on the RI 6E4L0FB-47. The other mappings
follow the Simply-Fi table of this family. The **Eco** option (`Eco=1`) is untested: it is only added to the
start command when the switch is on.

Programs offered by the official app (Happy Hour, Party, Turbo Power, Baby Care, etc.) are not mapped: their
codes are unknown. If you run one, the "current program" sensor shows its raw code.

### Water hardness

The water softener level is field **`r7`** of `statusDWash`, from S0 to S5:

| Level | °fH | °dH | Label | Salt |
|---|---|---|---|---|
| S0 | 0-5 | 0-3 | Very soft | no |
| S1 | 6-15 | 4-9 | Soft | yes |
| S2 | 16-30 | 10-16 | Medium hard | yes |
| S3 | 31-45 | 17-25 | Fairly hard (factory default) | yes |
| S4 | 46-60 | 26-33 | Hard | yes |
| S5 | 61-90 | 34-50 | Very hard | yes |

It is exposed as a **read-only** sensor: the appliance ignores remote writes of this setting, both from the
official app and from `/http-write.json`. Set it on the control panel (RI 6E4L0FB-47 manual, section 18):

1. Start with the appliance off, then switch it on with **On/Off**.
2. Hold **Program selection** and **On/Off** together for **5 s**: a beep, all LEDs blink for 5 s.
3. LEDs P1…P5 show the current level (no LED = S0).
4. Press **Program selection** to step through the levels (P1 = S1, P1+P2 = S2, …).
5. Hold **On/Off** for **3 s** to confirm (the appliance switches off).

## Installation

### HACS (custom repository)

1. HACS → ⋮ → *Custom repositories* → add `https://github.com/bbenjamin-sys/rosieres-local`, category *Integration*.
2. Install **Rosières Local**, then restart Home Assistant.

### Manual

Copy `custom_components/rosieres_local` to `/config/custom_components/rosieres_local`, then restart Home Assistant.

### Configuration

*Settings → Devices & services → Add integration → Rosières Local*, then enter:

- the dishwasher IP address (reserve it in your DHCP server);
- the 16-character XOR key of the appliance;
- a name.

The key is specific to each appliance and is **never** stored in this repository. It is stored in the Home
Assistant config entry only. See the [home-assistant-candy](https://github.com/ofalvai/home-assistant-candy)
project for ways to retrieve it.

## Local API notes

Findings from the RI 6E4L0FB-47, useful for anyone working on Simply-Fi appliances:

- Read: `GET /http-read.json?encrypted=1`. Write: `GET /http-write.json?encrypted=1&data=<hex>`.
  Payloads are XOR-ed with the 16-byte key, then hex-encoded. The decrypted JSON is pretty-printed with
  tabs and newlines.
- The firmware answers `BAD REQUEST` when queried too fast: the integration keeps at least 3 s between
  requests and polls every 15 s.
- `{"response":"SUCCESS"}` **does not mean the command was applied**: the appliance answers SUCCESS even to
  an unknown field. Always read the status back.
- When remote control is disabled (`StatoWiFi=0`), every write gets `{"response":"READ ONLY"}`. Enable it
  on the panel (hold *PROGR. 3sec* for 3 s, P3 and P4 light up). It must be re-enabled after a power cut.
- `r1` = index of the selected program (same as `w1`). `r7` = water hardness (S0-S5). `r2`…`r6`, `r8`,
  `r9`, `r15` are unknown; they are shown by the "raw settings" diagnostic sensor so that changes can be
  spotted in the history.
- The Wi-Fi module can get stuck and keep returning an old status (same `RemTime` for days). Unplugging the
  appliance for one minute fixed it.
- `/http-getStatistics.json` did not answer on this model.

## Debug logs

```yaml
logger:
  logs:
    custom_components.rosieres_local: debug
```

Avoid polling the same appliance with another integration (e.g. `candy`) for a long time: Simply-Fi
firmwares dislike close requests.

---

## Résumé en français

Intégration Home Assistant **100 % locale** pour les lave-vaisselle Rosières / Candy / Haier « Simply-Fi »,
testée sur un **Rosières RI 6E4L0FB-47** : état, programme, temps restant, options du prochain cycle,
démarrer / arrêter, et **dureté de l'eau** (en lecture seule, champ `r7`, niveaux S0 à S5).

### ⚠️ Activer et garder le mode Wi-Fi (contrôle à distance)

Sans le **mode Wi-Fi activé sur la machine**, le lave-vaisselle est en **lecture seule** : Home Assistant
voit l'état, mais toute commande (Démarrer, Arrêter) échoue avec `{'response': 'READ ONLY'}`. C'est une
sécurité : ce mode ne s'active **qu'au bandeau**, jamais à distance.

- **Activer** : machine allumée, maintenir **PROGR. 3sec** pendant **3 secondes**. Les voyants **P3 et P4**
  restent allumés.
- **Il se désactive** après une coupure de courant (débranchement, disjoncteur), un arrêt/redémarrage avec
  *Marche/Arrêt* pendant un cycle (P3 et P4 clignotent), ou un appui de 3 s sur *PROGR. 3sec* ou
  *DÉPART/ANNUL*. Il faut alors le réactiver.
- **Vérifier dans Home Assistant** : le capteur **« Connexion Wi-Fi »** doit être sur *on*. L'automatisation
  d'exemple plus haut prévient quand il passe à *off*.
- **État figé depuis des heures ?** Le module Wi-Fi est bloqué : débrancher la machine 1 minute, la
  rebrancher, puis réactiver le mode Wi-Fi.

La dureté **se règle uniquement au bandeau** : machine éteinte, l'allumer, maintenir *Sélection du
programme* + *Marche/Arrêt* 5 s, appuyer sur *Sélection du programme* jusqu'au niveau voulu (voyants P1…P5),
valider en maintenant *Marche/Arrêt* 3 s. L'appli e-picurien et l'API locale ne l'appliquent pas, même si
la machine répond « SUCCESS ».

Installation : HACS (dépôt personnalisé) ou copie de `custom_components/rosieres_local`, puis
*Paramètres → Appareils et services → Ajouter une intégration → Rosières Local*. La clé XOR de l'appareil
n'est jamais dans ce dépôt : elle reste dans la configuration de Home Assistant.

## License

MIT
