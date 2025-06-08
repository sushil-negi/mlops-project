#!/bin/bash

# Log training run to MLflow using curl

MLFLOW_URL="http://localhost:5001"
EXPERIMENT_ID="1"

echo "🚀 Logging training run to MLflow..."

# Create a new run
RUN_RESPONSE=$(curl -s -X POST "$MLFLOW_URL/api/2.0/mlflow/runs/create" \
  -H "Content-Type: application/json" \
  -d "{
    \"experiment_id\": \"$EXPERIMENT_ID\",
    \"start_time\": $(date +%s)000,
    \"tags\": [
      {\"key\": \"model.name\", \"value\": \"demo-llm\"},
      {\"key\": \"model.version\", \"value\": \"1.1.0\"},
      {\"key\": \"dataset\", \"value\": \"tech-docs-1240\"},
      {\"key\": \"framework\", \"value\": \"pytorch\"}
    ]
  }")

# Extract run ID
RUN_ID=$(echo $RUN_RESPONSE | python3 -c "import json,sys; print(json.load(sys.stdin)['run']['info']['run_id'])")

echo "✅ Created run: $RUN_ID"

# Log parameters
echo ""
echo "📝 Logging parameters..."

params=(
  "learning_rate:0.001"
  "batch_size:16"
  "epochs:5"
  "hidden_size:384"
  "num_layers:6"
  "num_heads:6"
  "training_examples:1240"
)

for param in "${params[@]}"; do
  IFS=':' read -r key value <<< "$param"
  curl -s -X POST "$MLFLOW_URL/api/2.0/mlflow/runs/log-parameter" \
    -H "Content-Type: application/json" \
    -d "{\"run_id\": \"$RUN_ID\", \"key\": \"$key\", \"value\": \"$value\"}" > /dev/null
  echo "  ✓ $key: $value"
done

# Log metrics
echo ""
echo "📊 Logging metrics..."

# Epoch metrics
epochs=(
  "1:4.545:0.600"
  "2:4.045:0.680"
  "3:3.545:0.760"
  "4:3.045:0.840"
  "5:2.545:0.920"
)

for epoch_data in "${epochs[@]}"; do
  IFS=':' read -r epoch loss acc <<< "$epoch_data"
  step=$((epoch - 1))
  
  # Log loss
  curl -s -X POST "$MLFLOW_URL/api/2.0/mlflow/runs/log-metric" \
    -H "Content-Type: application/json" \
    -d "{
      \"run_id\": \"$RUN_ID\",
      \"key\": \"train_loss\",
      \"value\": $loss,
      \"step\": $step
    }" > /dev/null
  
  # Log accuracy
  curl -s -X POST "$MLFLOW_URL/api/2.0/mlflow/runs/log-metric" \
    -H "Content-Type: application/json" \
    -d "{
      \"run_id\": \"$RUN_ID\",
      \"key\": \"accuracy\",
      \"value\": $acc,
      \"step\": $step
    }" > /dev/null
  
  echo "  ✓ Epoch $epoch: loss=$loss, accuracy=$acc"
done

# Log final metrics
echo ""
echo "📈 Logging final metrics..."

curl -s -X POST "$MLFLOW_URL/api/2.0/mlflow/runs/log-metric" \
  -H "Content-Type: application/json" \
  -d "{\"run_id\": \"$RUN_ID\", \"key\": \"final_loss\", \"value\": 2.545}" > /dev/null

curl -s -X POST "$MLFLOW_URL/api/2.0/mlflow/runs/log-metric" \
  -H "Content-Type: application/json" \
  -d "{\"run_id\": \"$RUN_ID\", \"key\": \"final_accuracy\", \"value\": 0.920}" > /dev/null

echo "  ✓ Final loss: 2.545"
echo "  ✓ Final accuracy: 0.920"

# Update run status
curl -s -X POST "$MLFLOW_URL/api/2.0/mlflow/runs/update" \
  -H "Content-Type: application/json" \
  -d "{
    \"run_id\": \"$RUN_ID\",
    \"status\": \"FINISHED\",
    \"end_time\": $(date +%s)000
  }" > /dev/null

echo ""
echo "✅ Training run successfully logged to MLflow!"
echo ""
echo "🔗 View your run at:"
echo "   http://localhost:5001/#/experiments/1/runs/$RUN_ID"
echo ""
echo "📊 Or view all runs at:"
echo "   http://localhost:5001/#/experiments/1"