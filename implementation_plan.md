# Implementation Plan: DIY Backpropagation

## Script 1: XOR Neural Network (`xor_nn.py`)

### Goal
Train a neural network with one hidden layer to learn the XOR function.

### Network Architecture
- Input layer: 2 nodes (x1, x2)
- Hidden layer: configurable number of nodes (variable `h`, e.g. 4)
- Output layer: 1 node (binary classification)

### Weight Representation
- `hidden_weights`: h x (n+1) matrix — each row is weights for one hidden node, first column is bias
- `output_weights`: vector of length h+1 — first element is bias

### Step-by-Step Implementation

#### Step 1: Initialization
- Define XOR training data: 4 points with labels
- Initialize `hidden_weights` as h x 3 matrix of random values in [-1, 1]
- Initialize `output_weights` as vector of length h+1 with random values in [-1, 1]
- Set hyperparameters: `learning_rate`, number of `epochs`, number of hidden nodes `h`

#### Step 2: `sigmoid(x)`
- Return `1 / (1 + exp(-x))`
- Also define `sigmoid_derivative(x)` = `sigmoid(x) * (1 - sigmoid(x))` for use in backprop

#### Step 3: `predict(hidden_weights, output_weights, point)`
- Prepend bias (1) to input point
- Forward pass through hidden layer:
  - For each hidden node i: compute dot product of `hidden_weights[i]` with input, apply sigmoid → `hidden_activations[i]`
- Prepend bias (1) to hidden activations
- Forward pass through output layer:
  - Compute dot product of `output_weights` with hidden activations, apply sigmoid → final output
- Return output value

#### Step 4: `train(hidden_weights, output_weights, point, target_label, learning_rate)`
- **Forward pass** (same as predict, but save intermediate values):
  - Compute hidden layer inputs (`hidden_inputs`) and activations (`hidden_activations`)
  - Compute output layer input and activation (`output`)
- **Backpropagation — output layer**:
  - Compute output error: `error = target_label - output`
  - Compute output delta: `delta_output = error * sigmoid_derivative(output)`
  - Update each output weight: `output_weights[j] += learning_rate * delta_output * hidden_with_bias[j]`
- **Backpropagation — hidden layer**:
  - For each hidden node i:
    - Compute hidden error: `error_hidden[i] = output_weights[i+1] * delta_output` (skip bias weight)
    - Compute hidden delta: `delta_hidden[i] = error_hidden[i] * sigmoid_derivative(hidden_activations[i])`
    - Update weights: `hidden_weights[i][j] += learning_rate * delta_hidden[i] * input_with_bias[j]`
- Return updated weights

#### Step 5: `epoch(hidden_weights, output_weights, training_set, training_labels)`
- Loop over all training points and call `train` on each
- Return updated weights

#### Step 6: `evaluate(hidden_weights, output_weights, testing_set, testing_labels)`
- Loop over test points, call `predict` on each
- Round output to 0 or 1 (threshold at 0.5)
- Return fraction classified correctly

#### Step 7: Main training loop
- Run for N epochs, printing accuracy or error after each
- Print final predictions on all 4 XOR inputs to verify correctness

---

## Script 2: Iris Neural Network (`iris_nn.py`)

### Goal
Train a neural network with 3 output nodes to classify iris flowers (3 classes). Also include a ReLU variation for comparison.

### Network Architecture
- Input layer: 4 nodes (sepal length, sepal width, petal length, petal width)
- Hidden layer: configurable number of nodes (variable `h`, e.g. 8)
- Output layer: 3 nodes (one per class)

### Weight Representation
- `hidden_weights`: h x (4+1) = h x 5 matrix — same structure as Script 1
- `output_weights`: 3 x (h+1) matrix — each row is weights for one output node

### Step-by-Step Implementation

#### Step 1: Data Loading and Preprocessing
- Load `iris.csv` (copied from previous project)
- Encode class labels as one-hot vectors:
  - Iris-setosa    → [1, 0, 0]
  - Iris-versicolor → [0, 1, 0]
  - Iris-virginica  → [0, 0, 1]
- Randomly shuffle dataset, split into:
  - Test set: 30 items (20%)
  - Training set: 120 items (80%)
- Normalize features (optional but helpful for convergence)

#### Step 2: Initialization
- Initialize `hidden_weights`: h x 5 matrix, random values in [-1, 1]
- Initialize `output_weights`: 3 x (h+1) matrix, random values in [-1, 1]
- Set hyperparameters: `learning_rate`, number of `epochs`, `h`

#### Step 3: `sigmoid(x)` (reuse from Script 1)

#### Step 4: `predict(hidden_weights, output_weights, point)`
- Prepend bias to input
- Compute hidden activations (same as Script 1)
- Prepend bias to hidden activations
- For each of 3 output nodes: compute dot product with its row of `output_weights`, apply sigmoid
- Return list of 3 output values
- For classification: choose index of highest output value as predicted class

#### Step 5: `train(hidden_weights, output_weights, point, target_label, learning_rate)`
- `target_label` is a one-hot vector [t1, t2, t3]
- **Forward pass**: compute hidden activations and 3 output values (save intermediates)
- **Backprop — output layer** (for each output node k):
  - `error_k = target_label[k] - output_k`
  - `delta_output_k = error_k * sigmoid_derivative(output_k)`
  - Update `output_weights[k][j] += learning_rate * delta_output_k * hidden_with_bias[j]`
- **Backprop — hidden layer** (for each hidden node i):
  - `error_hidden[i] = sum over k of (output_weights[k][i+1] * delta_output_k)`
  - `delta_hidden[i] = error_hidden[i] * sigmoid_derivative(hidden_activations[i])`
  - Update `hidden_weights[i][j] += learning_rate * delta_hidden[i] * input_with_bias[j]`
- Return updated weights

#### Step 6: `epoch(...)` and `evaluate(...)` 
- Same structure as Script 1, adapted for 3 outputs
- `evaluate`: prediction = index of max output value; compare to true class index

#### Step 7: Track and plot training error
- After each epoch, compute average error across training set:
  - `avg_error = mean of sum((target - output)^2) over all training points`
- Store per-epoch error, plot at end using matplotlib
- Show error decreasing over time

#### Step 8: ReLU Variation
- Define `relu(x)` = `max(0, x)`
- Define `relu_derivative(x)` = `1 if x > 0 else 0`
- Copy sigmoid iris network, replace hidden layer activation with ReLU
- Keep sigmoid at output layer
- Run same training loop, collect per-epoch error
- Plot both sigmoid and ReLU error curves on same graph for comparison
- Add written explanation:
  - Why ReLU is preferred for modern networks (avoids vanishing gradient)
  - What leaky ReLU is (`max(0.01x, x)`) and why it helps (nonzero gradient for negative inputs)

#### Step 9: Final output
- Print test set accuracy for both sigmoid and ReLU models
- Display combined training error plot

---

## File Structure
```
Sprint6/
├── implementation_plan.md
├── xor_nn.py
├── iris_nn.py
└── iris.csv   (copied from previous project)
```
