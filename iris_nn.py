import math
import random
from sklearn.datasets import load_iris

# number of hidden nodes
h = 8
learning_rate = 0.1
num_epochs = 500

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def predict(hidden_weights, output_weights, point):
    inputs = [1] + point

    # hidden layer
    hidden_activations = []
    for i in range(h):
        total = sum(hidden_weights[i][j] * inputs[j] for j in range(len(inputs)))
        hidden_activations.append(sigmoid(total))

    hidden_with_bias = [1] + hidden_activations

    # output layer - 3 nodes
    outputs = []
    for k in range(3):
        total = sum(output_weights[k][j] * hidden_with_bias[j] for j in range(len(hidden_with_bias)))
        outputs.append(sigmoid(total))

    return outputs

def train(hidden_weights, output_weights, point, target_label, learning_rate):
    inputs = [1] + point

    # forward pass
    hidden_activations = []
    for i in range(h):
        total = sum(hidden_weights[i][j] * inputs[j] for j in range(len(inputs)))
        hidden_activations.append(sigmoid(total))

    hidden_with_bias = [1] + hidden_activations

    outputs = []
    for k in range(3):
        total = sum(output_weights[k][j] * hidden_with_bias[j] for j in range(len(hidden_with_bias)))
        outputs.append(sigmoid(total))

    # backprop - output layer
    delta_outputs = []
    for k in range(3):
        error = target_label[k] - outputs[k]
        delta_outputs.append(error * outputs[k] * (1 - outputs[k]))
        for j in range(len(hidden_with_bias)):
            output_weights[k][j] += learning_rate * delta_outputs[k] * hidden_with_bias[j]

    # backprop - hidden layer
    for i in range(h):
        error_hidden = sum(output_weights[k][i + 1] * delta_outputs[k] for k in range(3))
        delta_hidden = error_hidden * hidden_activations[i] * (1 - hidden_activations[i])
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

# one-hot encode labels
one_hot = {0: [1, 0, 0], 1: [0, 1, 0], 2: [0, 0, 1]}
encoded_labels = [one_hot[l] for l in labels]

# shuffle and split 80/20
combined = list(zip(data, encoded_labels))
random.seed(42)
random.shuffle(combined)
data, encoded_labels = zip(*combined)
data, encoded_labels = list(data), list(encoded_labels)

split = 120
training_set = data[:split]
training_labels = encoded_labels[:split]
testing_set = data[split:]
testing_labels = encoded_labels[split:]

# initialize weights
hidden_weights = [[random.uniform(-1, 1) for _ in range(5)] for _ in range(h)]
output_weights = [[random.uniform(-1, 1) for _ in range(h + 1)] for _ in range(3)]

# training loop
epoch_errors = []
for e in range(num_epochs):
    hidden_weights, output_weights = epoch(hidden_weights, output_weights, training_set, training_labels)

    # compute average error across training set
    total_error = 0
    for point, label in zip(training_set, training_labels):
        outputs = predict(hidden_weights, output_weights, point)
        total_error += sum((label[k] - outputs[k]) ** 2 for k in range(3))
    epoch_errors.append(total_error / len(training_set))

    if (e + 1) % 100 == 0:
        print(f"Epoch {e + 1}/{num_epochs}  avg error: {epoch_errors[-1]:.4f}")

print(f"\nTest accuracy: {evaluate(hidden_weights, output_weights, testing_set, testing_labels):.2%}")

# plot training error
import matplotlib.pyplot as plt
plt.plot(epoch_errors)
plt.xlabel("Epoch")
plt.ylabel("Average Error")
plt.title("Iris Sigmoid - Training Error")
plt.tight_layout()
plt.savefig("iris_sigmoid_error.png")
plt.show()
print("Plot saved to iris_sigmoid_error.png")
