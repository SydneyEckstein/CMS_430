import math
import random

# number of hidden nodes
h = 4

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def predict(hidden_weights, output_weights, point):
    # prepend bias to input
    inputs = [1] + point

    # hidden layer: compute activation for each hidden node
    hidden_activations = []
    for i in range(h):
        total = sum(hidden_weights[i][j] * inputs[j] for j in range(len(inputs)))
        hidden_activations.append(sigmoid(total))

    # prepend bias to hidden activations
    hidden_with_bias = [1] + hidden_activations

    # output layer
    output = sum(output_weights[j] * hidden_with_bias[j] for j in range(len(hidden_with_bias)))
    return sigmoid(output)


def train(hidden_weights, output_weights, point, target_label, learning_rate):
    # forward pass - save intermediates for backprop
    inputs = [1] + point

    hidden_inputs = []
    hidden_activations = []
    for i in range(h):
        total = sum(hidden_weights[i][j] * inputs[j] for j in range(len(inputs)))
        hidden_inputs.append(total)
        hidden_activations.append(sigmoid(total))

    hidden_with_bias = [1] + hidden_activations

    output_input = sum(output_weights[j] * hidden_with_bias[j] for j in range(len(hidden_with_bias)))
    output = sigmoid(output_input)

    # backprop - output layer
    error = target_label - output
    delta_output = error * output * (1 - output)
    for j in range(len(output_weights)):
        output_weights[j] += learning_rate * delta_output * hidden_with_bias[j]

    # backprop - hidden layer
    for i in range(h):
        error_hidden = output_weights[i + 1] * delta_output
        delta_hidden = error_hidden * hidden_activations[i] * (1 - hidden_activations[i])
        for j in range(len(inputs)):
            hidden_weights[i][j] += learning_rate * delta_hidden * inputs[j]

    return hidden_weights, output_weights


def epoch(hidden_weights, output_weights, training_set, training_labels):
    for point, label in zip(training_set, training_labels):
        hidden_weights, output_weights = train(hidden_weights, output_weights, point, label, learning_rate=0.1)
    return hidden_weights, output_weights


def evaluate(hidden_weights, output_weights, testing_set, testing_labels):
    correct = 0
    for point, label in zip(testing_set, testing_labels):
        output = predict(hidden_weights, output_weights, point)
        if round(output) == label:
            correct += 1
    return correct / len(testing_labels)


# --- XOR training ---
xor_data = [[0, 0], [0, 1], [1, 0], [1, 1]]
xor_labels = [0, 1, 1, 0]

random.seed(42)
hidden_weights = [[random.uniform(-1, 1) for _ in range(3)] for _ in range(h)]
output_weights = [random.uniform(-1, 1) for _ in range(h + 1)]

for e in range(10000):
    hidden_weights, output_weights = epoch(hidden_weights, output_weights, xor_data, xor_labels)

print("XOR predictions after training:")
for point, label in zip(xor_data, xor_labels):
    output = predict(hidden_weights, output_weights, point)
    print(f"  input={point}  expected={label}  output={output:.4f}  predicted={round(output)}")
