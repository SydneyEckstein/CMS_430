# Phased Implementation Plan: DIY Backpropagation

---

## Phase 1: Core Functions (`xor_nn.py`)

Build the foundational building blocks shared by all scripts.

- Implement `sigmoid(x)`: return `1 / (1 + exp(-x))`
- Implement `predict(hidden_weights, output_weights, point)`:
  - Prepend bias to input
  - Forward pass through hidden layer: dot product + sigmoid for each hidden node
  - Prepend bias to hidden activations
  - Forward pass through output layer: dot product + sigmoid → final output
  - Return output value

**Checkpoint:** Manually verify predict returns a value between 0 and 1 with random weights.

---

## Phase 2: Backpropagation — XOR (`xor_nn.py`)

Implement training and verify on the XOR problem.

- Implement `train(hidden_weights, output_weights, point, target_label, learning_rate)`:
  - Forward pass (save hidden inputs, hidden activations, output)
  - Backprop output layer: compute `delta_output`, update `output_weights`
  - Backprop hidden layer: compute `delta_hidden` per node, update `hidden_weights`
- Implement `epoch(hidden_weights, output_weights, training_set, training_labels)`:
  - Loop over all points, call `train` on each
- Implement `evaluate(hidden_weights, output_weights, testing_set, testing_labels)`:
  - Predict each point, threshold at 0.5, return accuracy fraction
- Set up XOR data (4 points), initialize random weights in [-1, 1]
- Run training loop for N epochs, print predictions on all 4 XOR inputs

**Checkpoint:** Network converges and correctly classifies all 4 XOR cases.

---

## Phase 3: Multi-Class Extension — Iris Sigmoid (`iris_nn.py`)

Extend the network to 3 output nodes and train on real data.

- Load `iris.csv`, encode labels as one-hot vectors:
  - Iris-setosa → [1, 0, 0], Iris-versicolor → [0, 1, 0], Iris-virginica → [0, 0, 1]
- Shuffle and split: 30 test (20%), 120 train (80%)
- Initialize `hidden_weights`: h x 5 matrix; `output_weights`: 3 x (h+1) matrix — both random in [-1, 1]
- Adapt `predict`: compute dot product with each row of `output_weights`, return list of 3 outputs; classify by argmax
- Adapt `train`:
  - Backprop output layer: compute `delta_output_k` for each of 3 output nodes
  - Backprop hidden layer: `error_hidden[i] = sum over k of (output_weights[k][i+1] * delta_output_k)`
- Track average training error per epoch: `mean of sum((target - output)^2)`
- Plot error curve with matplotlib showing error decreasing over time
- Print final test set accuracy

**Checkpoint:** Training error decreases across epochs; test accuracy is meaningfully above random (33%).

---

## Phase 4: ReLU Variation — Iris ReLU (`iris_relu_nn.py`)

Swap hidden layer activation to ReLU and compare to sigmoid.

- Define `relu(x)` = `max(0, x)` and `relu_derivative(x)` = `1 if x > 0 else 0`
- Copy iris sigmoid structure; replace hidden layer sigmoid with ReLU in both forward pass and backprop
  - Use pre-activation hidden input (not post-activation) when applying `relu_derivative`
  - Keep sigmoid at output layer (unchanged)
- Use same train/test split as Phase 3 for a fair comparison
- Collect per-epoch training error
- Plot sigmoid vs ReLU error curves on the same axes
- Print test accuracy for this model
- Add written explanation in comments:
  - Why ReLU avoids the vanishing gradient problem that affects sigmoid
  - What leaky ReLU (`max(0.01x, x)`) is and why it prevents dead neurons

**Checkpoint:** Combined plot shows both curves; ReLU curve behavior is visibly different from sigmoid.

---

## File Structure
```
Sprint6/
├── implementation_plan.md
├── phased_implementation_plan.md
├── xor_nn.py           (Phases 1 & 2)
├── iris_nn.py          (Phase 3)
├── iris_relu_nn.py     (Phase 4)
└── iris.csv
```
