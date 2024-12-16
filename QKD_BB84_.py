from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from numpy.random import randint
import numpy as np
from art import text2art
import copy

# ANSI color codes for improved logging
class Color:
    RESET = '\033[0m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'

NUM_QUBITS = 32


def generate_bits(n: int) -> np.ndarray:
    """
    Generate an array of random bits.

    Parameters:
    n (int): The number of bits to generate.

    Returns:
    np.ndarray: An array of random bits.
    """
    return randint(2, size=n)


def encode_message(bits: np.ndarray, basis: np.ndarray) -> list:
    """
    Encode a message using quantum bits.

    Parameters:
    bits (np.ndarray): The bits to encode.
    basis (np.ndarray): The basis to use for encoding.

    Returns:
    list: A list of QuantumCircuit objects representing the encoded message.
    """
    message = []
    for i in range(NUM_QUBITS):
        qc = QuantumCircuit(1, 1)  # 1 qubit and 1 classical bit
        if basis[i] == 0:  # Z-basis
            if bits[i] == 1:
                qc.x(0)  # Apply Pauli-X gate to flip the qubit
        else:  # X-basis
            if bits[i] == 0:
                qc.h(0)  # Apply Hadamard gate
            else:
                qc.x(0)
                qc.h(0)  # Apply Pauli-X followed by Hadamard
        qc.barrier()
        message.append(qc)
    return message


def simulate_quantum_channel(message: list, error_rate: float) -> list:
    """
    Simulate a quantum channel with a given error rate.

    Parameters:
    message (list): The original quantum message to be transmitted.
    error_rate (float): The rate at which errors occur during transmission.

    Returns:
    list: The noisy message after transmission through the quantum channel.
    """
    noisy_message = []
    for qc in message:
        if np.random.random() < error_rate:
            qc.x(0)  # Apply bit-flip error
        noisy_message.append(qc)
    return noisy_message


def measure_message(message: list, basis: np.ndarray) -> list:
    """
    Measure a quantum message using a given basis.

    Parameters:
    message (list): The quantum message to be measured.
    basis (np.ndarray): The basis to use for measurement.

    Returns:
    list: The measurement results.
    """
    backend = AerSimulator()
    measurements = []
    for q in range(NUM_QUBITS):
        if basis[q] == 1:  # X-basis measurement
            message[q].h(0)
        message[q].measure(0, 0)
        result = backend.run(message[q], shots=1, memory=True).result()
        measurements.append(int(result.get_memory()[0]))
    return measurements


def remove_garbage(a_basis: np.ndarray, b_basis: np.ndarray, bits: np.ndarray) -> list:
    """
    Remove bits that were measured in different bases.

    Parameters:
    a_basis (np.ndarray): Alice's basis.
    b_basis (np.ndarray): Bob's basis.
    bits (np.ndarray): The bits to filter.

    Returns:
    list: The filtered bits as standard Python integers.
    """
    matching_positions = [q for q in range(NUM_QUBITS) if a_basis[q] == b_basis[q]]
    print(f"{Color.CYAN}🔍 Matching Basis Positions: {matching_positions}{Color.RESET}")
    return [int(bits[q]) for q in matching_positions]


def check_keys(key1: list, key2: list) -> None:
    """
    Check if two keys are identical.

    Parameters:
    key1 (list): Alice's key.
    key2 (list): Bob's key.

    Returns:
    None
    """
    key1_str = ' '.join(map(str, key1))
    key2_str = ' '.join(map(str, key2))

    print(f"{Color.MAGENTA}🔑 Alice's Key: {key1_str}{Color.RESET}")
    print(f"{Color.MAGENTA}🔑 Bob's Key:   {key2_str}{Color.RESET}")
    if key1 == key2:
        print(f"{Color.GREEN}✅ Keys are the same and secure.{Color.RESET}\n")
    else:
        print(f"{Color.RED}❌ Error: Keys are different.{Color.RESET}\n")


def simulate_eavesdropping_detailed(message: list, eavesdropper_basis: np.ndarray, alice_basis: np.ndarray, error_rate: float):
    """
    Detailed simulation of eavesdropping.

    Parameters:
    message (list): The quantum message.
    eavesdropper_basis (np.ndarray): Eve's basis choices.
    alice_basis (np.ndarray): Alice's basis choices.
    error_rate (float): Probability of Eve introducing an error.

    Returns:
    tuple: Modified message and Eve's measurements.
    """
    backend = AerSimulator()
    eavesdropper_results = []

    for i in range(len(message)):
        qc = copy.deepcopy(message[i])  # Deep copy to avoid modifying the original
        print(f"\n{Color.YELLOW}🕵️ Qubit {i+1} Eavesdropping Analysis:{Color.RESET}")
        print(f"{Color.BLUE}  📡 Alice's Encoding Basis: {'X' if alice_basis[i] == 1 else 'Z'}{Color.RESET}")
        print(f"{Color.RED}  🕯️  Eve's Measurement Basis: {'X' if eavesdropper_basis[i] == 1 else 'Z'}{Color.RESET}")

        # Eve measures the qubit
        if eavesdropper_basis[i] == 1:  # X-basis
            qc.h(0)
            print(f"{Color.RED}  🔬 Eve applies Hadamard gate for X-basis measurement.{Color.RESET}")
        qc.measure(0, 0)
        result = backend.run(qc, shots=1, memory=True).result()
        eve_measurement = int(result.get_memory()[0])
        eavesdropper_results.append(eve_measurement)
        print(f"{Color.RED}  🔢 Eve's Measurement Result: {eve_measurement}{Color.RESET}")

        # Eve re-encodes the qubit based on her measurement
        qc_reencode = QuantumCircuit(1, 1)
        if eavesdropper_basis[i] == 1:  # X-basis
            if eve_measurement == 1:
                qc_reencode.x(0)
            qc_reencode.h(0)
            print(f"{Color.RED}  🔄 Eve re-encodes the qubit in X-basis.{Color.RESET}")
        else:  # Z-basis
            if eve_measurement == 1:
                qc_reencode.x(0)
            print(f"{Color.RED}  🔄 Eve re-encodes the qubit in Z-basis.{Color.RESET}")

        # Eve introduces a bit-flip error with the specified error rate
        if np.random.random() < error_rate:
            qc_reencode.x(0)
            print(f"{Color.RED}  ❗ Eve introduces a bit flip error.{Color.RESET}")

        # Update the message with Eve's re-encoded qubit
        message[i] = qc_reencode

    return message, eavesdropper_results


def simulate_eavesdropping(
    message: list, eavesdropper_basis: np.ndarray, alice_basis: np.ndarray, error_rate: float
) -> tuple:
    """
    Simulate Eve intercepting and measuring the quantum message.

    Parameters:
    message (list): The quantum message.
    eavesdropper_basis (np.ndarray): Eve's basis choices.
    alice_basis (np.ndarray): Alice's basis choices.
    error_rate (float): Probability of Eve introducing an error.

    Returns:
    tuple: Modified message and Eve's measurements.
    """
    print(f"\n{Color.RED}🕵️ --- Eavesdropper (Eve) Interception --- {Color.RESET}")
    message, eavesdropper_results = simulate_eavesdropping_detailed(
        message, eavesdropper_basis, alice_basis, error_rate
    )
    print(f"\n{Color.RED}🕵️ --- End of Eavesdropping --- {Color.RESET}\n")
    return message, eavesdropper_results


def quantum_communication(error_rate: float, num_iterations: int):
    """
    Simulate quantum communication between Alice and Bob.

    Parameters:
    error_rate (float): Probability of errors in the quantum channel.
    num_iterations (int): Number of simulation runs.

    Returns:
    None
    """
    for i in range(1, num_iterations + 1):
        print(f"\n{Color.GREEN}--- Simulation Run {i} ---{Color.RESET}")
        alice_bits = generate_bits(NUM_QUBITS)
        print(f"{Color.BLUE}📤 Alice's Bits:      {' '.join(map(str, alice_bits))}{Color.RESET}")

        alice_basis = generate_bits(NUM_QUBITS)
        print(f"{Color.BLUE}🔬 Alice's Basis:     {' '.join(['X' if b == 1 else 'Z' for b in alice_basis])}{Color.RESET}")

        message = encode_message(alice_bits, alice_basis)
        message = simulate_quantum_channel(message, error_rate)

        bob_basis = generate_bits(NUM_QUBITS)
        print(f"{Color.GREEN}📥 Bob's Basis:       {' '.join(['X' if b == 1 else 'Z' for b in bob_basis])}{Color.RESET}")

        bob_results = measure_message(message, bob_basis)
        print(f"{Color.GREEN}📥 Bob's Measurement: {' '.join(map(str, bob_results))}{Color.RESET}")

        alice_key = remove_garbage(alice_basis, bob_basis, alice_bits)
        bob_key = remove_garbage(alice_basis, bob_basis, bob_results)

        check_keys(alice_key, bob_key)

        print(f"{Color.MAGENTA}🔑 Key Length: Alice = {len(alice_key)}, Bob = {len(bob_key)}{Color.RESET}")
        print("-" * 50)


def main():
    """
    Main function to run the BB84 QKD simulation.

    Provides a menu for different simulation options.

    Returns:
    None
    """

    print("-" * 50 + "\n")
    print(text2art("BB84", font="small"))
    print("-" * 50)
    print("-" * 50 + "\n\n")

    num_iterations = 1  # Number of simulation runs per choice
    while True:
        print("Choose an option:")
        print("[1] Simulate with 0% error")
        print("[2] Simulate with 7.5% error rate")
        print("[3] Simulate with 20% error rate")
        print("[4] Simulate eavesdropping attempt")
        print("[5] Exit")
        choice = input("Enter your choice (1/2/3/4/5): ")

        if choice == "1":
            print(f"\n{Color.GREEN}--- Simulating with 0% Error Rate ---{Color.RESET}")
            quantum_communication(0.0, num_iterations)
            print()

        elif choice == "2":
            print(f"\n{Color.YELLOW}--- Simulating with 7.5% Error Rate ---{Color.RESET}")
            quantum_communication(0.075, num_iterations)
            print()

        elif choice == "3":
            print(f"\n{Color.RED}--- Simulating with 20% Error Rate ---{Color.RESET}")
            quantum_communication(0.2, num_iterations)
            print()

        elif choice == "4":
            print(f"\n{Color.RED}--- Simulating Eavesdropping Attempt ---{Color.RESET}")
            for i in range(1, num_iterations + 1):
                print(f"\n{Color.GREEN}--- Simulation Run {i} ---{Color.RESET}")
                alice_bits = generate_bits(NUM_QUBITS)
                print(f"{Color.BLUE}📤 Alice's Bits:     {' '.join(map(str, alice_bits))}{Color.RESET}")

                alice_basis = generate_bits(NUM_QUBITS)
                print(f"{Color.BLUE}🔬 Alice's Basis:    {' '.join(['X' if b == 1 else 'Z' for b in alice_basis])}{Color.RESET}")

                message = encode_message(alice_bits, alice_basis)

                eavesdropper_basis = generate_bits(NUM_QUBITS)
                print(f"{Color.RED}🕵️ Eve's Basis:       {' '.join(['X' if b == 1 else 'Z' for b in eavesdropper_basis])}{Color.RESET}")

                # Simulate eavesdropping with 10% error rate
                message, eve_measurements = simulate_eavesdropping(message, eavesdropper_basis, alice_basis, 0.1)

                print(f"{Color.BLUE}📤 Alice's Bits:      {' '.join(map(str, alice_bits))}{Color.RESET}")
                print(f"{Color.BLUE}🔬 Alice's Basis:     {' '.join(['X' if b == 1 else 'Z' for b in alice_basis])}{Color.RESET}")
                print(f"{Color.RED}🕵️ Eve's Basis:        {' '.join(['X' if b == 1 else 'Z' for b in eavesdropper_basis])}{Color.RESET}")

                print(f"{Color.RED}🕵️ Eve's Measurements: {' '.join(map(str, eve_measurements))}{Color.RESET}")

                bob_basis = generate_bits(NUM_QUBITS)
                print(f"{Color.GREEN}📥 Bob's Basis:       {' '.join(['X' if b == 1 else 'Z' for b in bob_basis])}{Color.RESET}")

                bob_results = measure_message(message, bob_basis)
                print(f"{Color.GREEN}📥 Bob's Measurement: {' '.join(map(str, bob_results))}{Color.RESET}")

                alice_key = remove_garbage(alice_basis, bob_basis, alice_bits)
                bob_key = remove_garbage(alice_basis, bob_basis, bob_results)

                check_keys(alice_key, bob_key)

                print(f"{Color.MAGENTA}🔑 Key Length: Alice = {len(alice_key)}, Bob = {len(bob_key)}{Color.RESET}")
                print("-" * 50)
            print()

        elif choice == "5":
            print("\nExiting the simulation. Goodbye!")
            break
        else:
            print("\n❗ Invalid choice. Please enter a valid option.\n")


if __name__ == "__main__":
    main()