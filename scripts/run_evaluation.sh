#!/bin/bash
# Automatise N essais d'evaluation quantitative du modele BC, pour un goal donne.
# Usage : ./run_evaluation.sh [nombre_essais] [nom_goal]
# nom_goal parmi : G1 G2 G3 G4 G5 (defaut G1)

set -e

N_TRIALS="${1:-15}"
GOAL_NAME="${2:-G1}"
WS_DIR="$HOME/stage_imitation_learning/ros2_ws"

declare -A GOAL_X_MAP=( [G1]=5.5 [G2]=6.5 [G3]=1.0 [G4]=6.0 [G5]=0.5 )
declare -A GOAL_Y_MAP=( [G1]=1.5 [G2]=-2.0 [G3]=2.0 [G4]=0.0 [G5]=-2.0 )

if [[ -z "${GOAL_X_MAP[$GOAL_NAME]}" ]]; then
    echo "Goal inconnu: $GOAL_NAME (attendu: G1 G2 G3 G4 G5)"
    exit 1
fi

export EVAL_GOAL_X="${GOAL_X_MAP[$GOAL_NAME]}"
export EVAL_GOAL_Y="${GOAL_Y_MAP[$GOAL_NAME]}"
export EVAL_RESULTS_CSV="$HOME/stage_imitation_learning/results/evaluation_${GOAL_NAME}.csv"

source /opt/ros/humble/setup.bash
source "$WS_DIR/install/setup.bash"
export LIBGL_ALWAYS_SOFTWARE=1

mkdir -p "$(dirname "$EVAL_RESULTS_CSV")"
rm -f "$EVAL_RESULTS_CSV"

echo "=== Evaluation quantitative : $N_TRIALS essais sur $GOAL_NAME ($EVAL_GOAL_X, $EVAL_GOAL_Y) ==="

for i in $(seq 1 "$N_TRIALS"); do
    echo ""
    echo ">>> Essai $i / $N_TRIALS ($GOAL_NAME)"

    killall -9 gzserver gzclient gazebo 2>/dev/null || true
    sleep 2

    ros2 launch create3_lidar_description create3_lidar_full.launch.py \
        use_rviz:=false > /tmp/eval_sim_log_$i.txt 2>&1 &
    SIM_PID=$!
    echo "Attente du controller_manager..."
    for attempt in $(seq 1 40); do
        if ros2 service list 2>/dev/null | grep -q "/controller_manager/list_controllers"; then
            echo "controller_manager pret."
            break
        fi
        sleep 2
    done

    echo "Attente du diffdrive_controller..."
    for attempt in $(seq 1 20); do
        if ros2 topic list 2>/dev/null | grep -q "/diffdrive_controller/cmd_vel_unstamped"; then
            echo "diffdrive_controller pret."
            break
        fi
        sleep 1
    done
    sleep 3

    ros2 param set /motion_control safety_override full > /dev/null 2>&1 || true
    python3 "$WS_DIR/src/create3_il/create3_il/eval_trial_node.py" "$i" \
        > /tmp/eval_trial_log_$i.txt 2>&1 || true

    kill -9 "$SIM_PID" 2>/dev/null || true
    pkill -9 -f "gzserver" 2>/dev/null || true
    pkill -9 -f "gzclient" 2>/dev/null || true
    pkill -9 -f "ros2 launch" 2>/dev/null || true
    pkill -9 -f "spawner" 2>/dev/null || true
    pkill -9 -f "robot_state_publisher" 2>/dev/null || true
    pkill -9 -f "motion_control" 2>/dev/null || true
    sleep 4

    if ros2 node list 2>/dev/null | grep -q "create3\|motion_control"; then
        echo "ATTENTION: des noeuds residuels sont encore actifs, pause supplementaire"
        sleep 5
    fi
done

echo ""
echo "=== Termine. Resultats dans $EVAL_RESULTS_CSV ==="
echo "Lance maintenant : python3 ~/stage_imitation_learning/scripts/summarize_evaluation.py $EVAL_RESULTS_CSV"
