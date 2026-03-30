import numpy as np
import matplotlib.pyplot as plt

# Function to plot averaged spectra

def plot_averaged_spectra(spectra):
    """
    Plots the average of a collection of spectra.

    Parameters:
    spectra (list of np.ndarray): A list where each element is a spectrum array.
    """
    # Calculate average spectrum
    average_spectrum = np.mean(spectra, axis=0)

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(average_spectrum, color='blue', label='Averaged Spectrum')
    plt.title('Averaged Spectra Plot')
    plt.xlabel('Frequency')
    plt.ylabel('Amplitude')
    plt.legend()
    plt.grid(True)
    plt.show()