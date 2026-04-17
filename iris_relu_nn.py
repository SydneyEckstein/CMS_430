import math
import random
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris

# number of hidden nodes
h = 8
learning_rate = 0.1
num_epochs = 500

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def relu(x):
    return max(0, x)

def relu_derivative(x):
    return 1 if x > 0 else 0

def predict(hidden_weights, output_weights, point):
    inputs = [1] + point

    # hidden layer with ReLU
    hidden_activations = []
    for i in range(h):
        total = sum(hidden_weights[i][j] * inputs[j] for j in range(len(inputs)))
        hidden_activations.append(relu(total))

    hidden_with_bias = [1] + hidden_activations

    # output layer with sigmoid
    outputs = []
    for k in range(3):
        total = sum(output_weights[k][j] * hidden_with_bias[j] for j in range(len(hidden_with_bias)))
        outputs.append(sigmoid(total))

    return outputs

def train(hidden_weights, output_weights, point, target_label, learning_rate):
    inputs = [1] + point

    # forward pass - save pre-activation inputs for relu_derivative
    hidden_inputs = []
    hidden_activations = []
    for i in range(h):
        total = sum(hidden_weights[i][j] * inputs[j] for j in range(len(inputs)))
        hidden_inputs.append(total)
        hidden_activations.append(relu(total))

    hidden_with_bias = [1] + hidden_activations

    outputs = []
    for k in range(3):
        total = sum(output_weights[k][j] * hidden_with_bias[j] for j in range(len(hidden_with_bias)))
        outputs.append(sigmoid(total))

    # backprop - output layer (sigmoid)
    delta_outputs = []
    for k in range(3):
        error = target_label[k] - outputs[k]
        delta_outputs.append(error * outputs[k] * (1 - outputs[k]))
        for j in range(len(hidden_with_bias)):
            output_weights[k][j] += learning_rate * delta_outputs[k] * hidden_with_bias[j]

    # backprop - hidden layer (ReLU)
    for i in range(h):
        error_hidden = sum(output_weights[k][i + 1] * delta_outputs[k] for k in range(3))
        delta_hidden = error_hidden * relu_derivative(hidden_inputs[i])
        for j in range(len(inputs)):
            hidden_weights[i][j] += learning_rate * delta_hidden * inputs[j]

    return hidden_weights, output_weights

def epoch(hidden_weights, output_weights, training_set, training_labels):
    for point, label in zip(training_set, training_labels):
        hidden_weights, output_weights = train(hidden_weights, output_weights, point, label, learning_rate)
    return hidden_weights, output_weights

def evaluate(hidden_weights, output_weights, testing_set, testing_labels):
    correct = 0
    for point, label in zip(testing_set, testing_labels):
        outputs = predict(hidden_weights, output_weights, point)
        if outputs.index(max(outputs)) == label.index(max(label)):
            correct += 1
    return correct / len(testing_labels)


# --- Load and prepare data ---
iris = load_iris()
data = [list(row) for row in iris.data]
labels = list(iris.target)

# normalize each feature to [0, 1]
for f in range(4):
    col = [row[f] for row in data]
    col_min, col_max = min(col), max(col)
    for row in data:
        row[f] = (row[f] - col_min) / (col_max - col_min)

one_hot = {0: [1, 0, 0], 1: [0, 1, 0], 2: [0, 0, 1]}
encoded_labels = [one_hot[l] for l in labels]

combined = list(zip(data, encoded_labels))
random.seed(42)
random.shuffle(combined)
data, encoded_labels = zip(*combined)
data, encoded_labels = list(data), list(encoded_labels)

training_set = data[:120]
training_labels = encoded_labels[:120]
testing_set = data[120:]
testing_labels = encoded_labels[120:]

# initialize weights
hidden_weights = [[random.uniform(-1, 1) for _ in range(5)] for _ in range(h)]
output_weights = [[random.uniform(-1, 1) for _ in range(h + 1)] for _ in range(3)]

# training loop
epoch_errors = []
for e in range(num_epochs):
    hidden_weights, output_weights = epoch(hidden_weights, output_weights, training_set, training_labels)

    total_error = 0
    for point, label in zip(training_set, training_labels):
        outputs = predict(hidden_weights, output_weights, point)
        total_error += sum((label[k] - outputs[k]) ** 2 for k in range(3))
    epoch_errors.append(total_error / len(training_set))

    if (e + 1) % 100 == 0:
        print(f"Epoch {e + 1}/{num_epochs}  avg error: {epoch_errors[-1]:.4f}")

print(f"\nTest accuracy: {evaluate(hidden_weights, output_weights, testing_set, testing_labels):.2%}")

# --- Load sigmoid errors for comparison ---
# re-run sigmoid version to get its error curve
import importlib.util, sys

def run_sigmoid_errors():
    import iris_nn
    importlib.reload(iris_nn)

# instead, just re-run inline for comparison plot
def sigmoid_only(x):
    return 1 / (1 + math.exp(-x))

def predict_sig(hw, ow, point):
    inputs = [1] + point
    ha = []
    for i in range(h):
        total = sum(hw[i][j] * inputs[j] for j in range(len(inputs)))
        ha.append(sigmoid_only(total))
    hwb = [1] + ha
    outputs = []
    for k in range(3):
        total = sum(ow[k][j] * hwb[j] for j in range(len(hwb)))
        outputs.append(sigmoid_only(total))
    return outputs

def train_sig(hw, ow, point, label, lr):
    inputs = [1] + point
    ha = []
    for i in range(h):
        total = sum(hw[i][j] * inputs[j] for j in range(len(inputs)))
        ha.append(sigmoid_only(total))
    hwb = [1] + ha
    outputs = []
    for k in range(3):
        total = sum(ow[k][j] * hwb[j] for j in range(len(hwb)))
        outputs.append(sigmoid_only(total))
    delta_outputs = []
    for k in range(3):
        err = label[k] - outputs[k]
        delta_outputs.append(err * outputs[k] * (1 - outputs[k]))
        for j in range(len(hwb)):
            ow[k][j] += lr * delta_outputs[k] * hwb[j]
    for i in range(h):
        eh = sum(ow[k][i+1] * delta_outputs[k] for k in range(3))
        dh = eh * ha[i] * (1 - ha[i])
        for j in range(len(inputs)):
            hw[i][j] += lr * dh * inputs[j]
    return hw, ow

random.seed(42)
hw_s = [[random.uniform(-1,1) for _ in range(5)] for _ in range(h)]
ow_s = [[random.uniform(-1,1) for _ in range(h+1)] for _ in range(3)]
sigmoid_errors = []
for _ in range(num_epochs):
    for point, label in zip(training_set, training_labels):
        hw_s, ow_s = train_sig(hw_s, ow_s, point, label, learning_rate)
    total_error = 0
    for point, label in zip(training_set, training_labels):
        outputs = predict_sig(hw_s, ow_s, point)
        total_error += sum((label[k] - outputs[k]) ** 2 for k in range(3))
    sigmoid_errors.append(total_error / len(training_set))

# plot comparison
plt.plot(sigmoid_errors, label="Sigmoid")
plt.plot(epoch_errors, label="ReLU")
plt.xlabel("Epoch")
plt.ylabel("Average Error")
plt.title("Iris Training Error: Sigmoid vs ReLU")
plt.legend()
plt.tight_layout()
plt.savefig("iris_comparison_error.png")
plt.show()
print("Plot saved to iris_comparison_error.png")

# --- Written explanation ---
"""
Why ReLU is preferred for modern networks:
  The sigmoid function saturates at 0 and 1 for large or small inputs, making its
  gradient nearly zero. During backpropagation this causes the vanishing gradient
  problem -- weight updates become extremely small and the network stops learning.
  ReLU avoids this because its gradient is always either 0 or 1, keeping updates
  meaningful regardless of the input magnitude.

What leaky ReLU is and why it helps:
  Leaky ReLU is defined as max(0.01x, x). For negative inputs, standard ReLU
  outputs 0 and has zero gradient, which can cause "dead neurons" that never
  activate and stop learning entirely. Leaky ReLU allows a small nonzero gradient
  for negative inputs (slope of 0.01), keeping those neurons alive and able to
  recover during training.
"""
