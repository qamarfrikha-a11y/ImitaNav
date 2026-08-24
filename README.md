# 🚀 Navigation Autonome par Imitation Learning

[![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)](https://docs.ros.org/en/humble/)
[![Gazebo](https://img.shields.io/badge/Gazebo-Classic%2011-green)](https://classic.gazebosim.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-1.10+-orange)](https://pytorch.org/)
[![Python](https://img.shields.io/badge/Python-3.8+-yellow)](https://www.python.org/)

---

## 📖 Présentation du projet

Ce projet implémente un système de **navigation autonome** pour un robot **iRobot Create 3** en utilisant l'**Apprentissage par Imitation (Imitation Learning)**.

Le robot apprend à naviguer dans un environnement simulé sous **ROS 2** et **Gazebo**, à partir de **10 démonstrations initiales par Behavioral Cloning**, affinées ensuite par **5 sessions interactives de HG-DAgger**.

<img src="media/images/robot_create3.png" alt="Robot Create 3" width="280"/>

### 🎯 Objectifs

1. Apprendre une politique de navigation à partir de démonstrations humaines
2. Naviguer de manière autonome dans un couloir en L avec obstacles
3. Atteindre l'objectif avec 100% de réussite
4. Comparer Behavioral Cloning seul vs BC enrichi par HG-DAgger

---

## 🏗️ Pipeline global

```mermaid
flowchart TD
    A["Simulation Gazebo<br/>Robot Create 3 + LiDAR"] -->|"/scan, /odom"| B["Observation (40D)<br/>36×LiDAR + distance/angle objectif + vitesse"]
    B --> C["Policy Network (MLP)<br/>40 → 128 → 64 → 2"]
    C --> D["Filtre de sécurité<br/>détection cône frontal + évitement"]
    D -->|"/cmd_vel"| A

    E["10 démonstrations<br/>Behavioral Cloning"] --> F["Entraînement initial<br/>(6 004 pas)"]
    F --> G["5 sessions HG-DAgger<br/>corrections ciblées"]
    G --> H["Dataset final<br/>15 978 pas"]
    H --> C
```

---

## 📸 Simulation & résultats

<p align="center">
  <img src="media/images/simulation_start.png" alt="Départ" width="45%"/>
  <img src="media/images/simulation_goal.png" alt="Arrivée" width="45%"/>
</p>

<p align="center"><b>📌 Position de départ</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>🎯 Objectif atteint</b></p>

### 📉 Courbe d'apprentissage

<img src="media/images/training_curve.png" alt="Courbe d'entraînement" width="600"/>

### 📊 Comparaison BC seul vs BC + HG-DAgger

<img src="media/images/comparison_bc_dagger.png" alt="Comparaison BC vs DAgger" width="600"/>

---

## 📈 Résultats

| Méthode | Essais | Taux de réussite | Pas d'entraînement | Erreur validation |
|---|---|---|---|---|
| BC seul (modèle instable + bug dataset) | 8 | 0% | 6 004 | 0.0425 |
| **BC + HG-DAgger (final)** | 10 | **100%** | 15 978 | **0.0324** |

**Temps moyen de trajet (version finale)** : 58.8 s (±15.2) — **Longueur moyenne** : 9.85 m (±1.52)

<details>
<summary>📋 Détail des 10 essais finaux</summary>

| Essai | Résultat | Temps (s) | Distance (m) | Contacts | Safety triggers |
|---|---|---|---|---|---|
| 1 | ✅ Réussi | 61.9 | 11.15 | Mineur | 13 |
| 2 | ✅ Réussi | 47.0 | 8.92 | Aucun | 0 |
| 3 | ✅ Réussi | 54.1 | 9.27 | Mineur | 30 |
| 4 | ✅ Réussi | 54.2 | 9.64 | Mineur | 33 |
| 5 | ✅ Réussi | 48.3 | 8.56 | Mineur | 0 |
| 6 | ✅ Réussi | 47.4 | 8.76 | Aucun | 0 |
| 7 | ✅ Réussi | 97.1 | 13.30 | Mineur | 90 |
| 8 | ✅ Réussi | 51.9 | 8.65 | Mineur | 0 |
| 9 | ✅ Réussi | 49.9 | 8.78 | Aucun | 0 |
| 10 | ✅ Réussi | 75.9 | 11.49 | Mineur | 13 |

</details>

---

## 🎬 Vidéo de démonstration
<img src="media/images/videos/demo_navigation.mp4" alt="Vidéo de démonstration" width="400"/>

   ▶️ [**Voir la vidéo complète (47s)**](media/videos/demo_navigation.mp4)
---

## 🏗️ Structure du projet

```
imitation-learning-create3/
├── ros2_ws/src/
│   ├── create3_il/                 # Package ROS 2 : collecte, entraînement, éval
│   └── create3_lidar_description/  # Create 3 + LiDAR (URDF/SDF)
├── config/
│   └── slam_params.yaml
├── data/processed/
│   └── dataset.npz                 # Dataset final fusionné (BC + DAgger)
├── models/
│   └── bc_model.pt                 # Politique entraînée finale
├── results/
│   ├── evaluation.csv              # 10 essais finaux (BC + DAgger)
│   └── evaluation_v1_ancien_critere.csv  # 8 essais BC seul
├── scripts/
│   ├── train_bc.py
│   ├── merge_dagger_data.py
│   └── summarize_evaluation.py
├── media/
│   ├── images/
│   └── videos/
├── .gitignore
└── README.md
```

---

## 🚀 Installation

**Prérequis** : Ubuntu 22.04, ROS 2 Humble, Gazebo Classic 11, Python 3.8+, PyTorch (CPU)

```bash
git clone https://github.com/qamarfrikha-a11y/imitation-learning-create3.git
cd imitation-learning-create3/ros2_ws
colcon build
source install/setup.bash
```

### Entraînement

```bash
python3 scripts/train_bc.py
```

### Évaluation

```bash
ros2 param set /motion_control safety_override full
python3 ros2_ws/src/create3_il/create3_il/eval_trial_node.py <trial_id>
```

---

## Remerciements

Structure de dépôt inspirée de [tomasvr/turtlebot3_drlnav](https://github.com/tomasvr/turtlebot3_drlnav).
