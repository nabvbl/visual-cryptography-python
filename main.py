import tkinter as tk
from tkinter import filedialog
from PIL import Image
import numpy as np
import os

# Define output directories
OUTPUT_DIR = "output"
INPUT_DIR = "input"

def select_image():
    """
    Allows the user to select an image file using a Tkinter file dialog.
    Returns the selected file path.
    """
    print("[INFO] Opening file dialog to select image...")
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(
        title="Select an Image File",
        filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif")])
    root.destroy()
    return file_path

def preprocess_image(image_path):
    """
    Loads an image, converts it to grayscale, resizes it, and applies a threshold.
    Saves the original image as 'input/sample.png'.
    Returns the preprocessed (black and white) image as a NumPy array.
    """
    print(f"[INFO] Loading image from: {image_path}")
    # Open the image using Pillow
    img = Image.open(image_path)

    # Ensure input directory exists for saving the original image
    os.makedirs(INPUT_DIR, exist_ok=True)
    # Save the user-selected image for reference
    img.save(os.path.join(INPUT_DIR, "sample.png"))
    print(f"[INFO] Original image saved to {os.path.join(INPUT_DIR, "sample.png")}")

    # Convert image to grayscale
    print("[INFO] Converting image to grayscale...")
    img_gray = img.convert("L")  # "L" mode for grayscale

    # Resize image if it's too large (max 150x150)
    max_size = (150, 150)
    if img_gray.width > max_size[0] or img_gray.height > max_size[1]:
        print(f"[INFO] Resizing image to max {max_size[0]}x{max_size[1]}...")
        img_gray.thumbnail(max_size, Image.Resampling.LANCZOS) # Use LANCZOS for high-quality downsampling
    else:
        print("[INFO] Image size is within limits, no resizing needed.")

    # Apply threshold to convert to black and white
    # Pixels with intensity below 120 become black (0), otherwise white (255)
    threshold_value = 120
    print(f"[INFO] Applying threshold ({threshold_value}) to convert to black and white...")
    # Create a NumPy array from the grayscale image
    img_np = np.array(img_gray)
    # Apply threshold: 0 for pixel values <= threshold_value, 255 for pixel values > threshold_value
    img_bw = np.where(img_np <= threshold_value, 0, 255).astype(np.uint8)

    return img_bw

def encrypt_image(image_bw):
    """
    Encrypts a black and white image into two shares using visual cryptography logic.
    Each pixel (black or white) is expanded into a 2x2 block in the shares.
    """
    print("[INFO] Encrypting image into two shares...")
    # Get dimensions of the black and white image
    height, width = image_bw.shape

    # Create empty arrays for the two shares, each 2x larger in dimensions
    share1 = np.zeros((height * 2, width * 2), dtype=np.uint8)
    share2 = np.zeros((height * 2, width * 2), dtype=np.uint8)

    # Define the 2x2 patterns for black and white pixels
    # For a white pixel (255), the patterns are inverses of each other
    # For a black pixel (0), the patterns are identical
    # We use 0 for black and 255 for white in the output shares

    # Patterns for white pixel (e.g., [[255, 0], [0, 255]] and [[0, 255], [255, 0]])
    # These are chosen so that when combined, they result in two white and two black sub-pixels.
    # And when XORed, they produce a pattern with equal black and white pixels.
    white_patterns = [
        np.array([[255, 0], [0, 255]], dtype=np.uint8),
        np.array([[0, 255], [255, 0]], dtype=np.uint8)
    ]

    # Patterns for black pixel (e.g., [[255, 0], [0, 255]] and [[255, 0], [0, 255]])
    # These are chosen so that when combined, they result in two black and two white sub-pixels.
    # And when XORed, they produce a pattern with only black pixels.
    black_patterns = [
        np.array([[255, 0], [0, 255]], dtype=np.uint8),
        np.array([[255, 0], [0, 255]], dtype=np.uint8) # Same as the first pattern
    ]

    # Iterate over each pixel of the original black and white image
    for y in range(height):
        for x in range(width):
            # Get the pixel value (0 for black, 255 for white)
            pixel_value = image_bw[y, x]

            # Randomly choose one of the two pattern sets for white or black
            # This randomness ensures that the individual shares look like noise
            # and reveal no information about the original image.
            choice = np.random.randint(2)

            # Determine which patterns to use based on the pixel value
            if pixel_value == 255:  # White pixel
                pattern1 = white_patterns[choice]
                pattern2 = white_patterns[1 - choice] # Use the inverse pattern
            else:  # Black pixel (0)
                pattern1 = black_patterns[choice]
                pattern2 = black_patterns[choice]  # Use the same pattern

            # Place the 2x2 patterns into the respective shares
            # Each pixel in the original image corresponds to a 2x2 block in the shares
            share1[y*2:(y+1)*2, x*2:(x+1)*2] = pattern1
            share2[y*2:(y+1)*2, x*2:(x+1)*2] = pattern2

    return share1, share2

def decrypt_image(share1, share2):
    """
    Reconstructs the original image by combining (ORing) the two shares.
    In visual cryptography, combining shares typically involves superimposing them.
    For binary images represented by 0 (black) and 255 (white), this can be achieved
    by an OR operation, where 0 OR 0 = 0, 0 OR 255 = 255, 255 OR 0 = 255, 255 OR 255 = 255.
    However, standard NumPy OR will treat 255 as True. A simple addition and clipping
    or a bitwise OR operation after converting to boolean can be used. Since we want
    black (0) and white (255), we can sum and then threshold, or use bitwise OR if values are 0/1.
    Given our shares are 0/255, a direct sum and then clipping to 255 will work for combining
    (if any part is white, the combined part is white). This will effectively be an OR operation.
    """
    print("[INFO] Decrypting (reconstructing) image from shares...")
    # Simply add the two shares. If both are 0, sum is 0. If one or both are 255, sum will be 255 or 510.
    # Since 255 represents white, anything that results in white should stay white.
    # And anything that results in black should stay black.
    # The maximum value should be 255 (white).
    reconstructed_image = np.minimum(share1 + share2, 255).astype(np.uint8)
    return reconstructed_image

def save_images(share1, share2, reconstructed_image):
    """
    Saves the generated share images and the reconstructed image to the output directory.
    """
    print("[INFO] Saving share and reconstructed images...")
    # Create the output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Convert NumPy arrays back to Pillow Image objects for saving
    img_share1 = Image.fromarray(share1)
    img_share2 = Image.fromarray(share2)
    img_reconstructed = Image.fromarray(reconstructed_image)

    # Save images
    img_share1.save(os.path.join(OUTPUT_DIR, "share1.png"))
    print(f"[INFO] Share 1 saved to {os.path.join(OUTPUT_DIR, "share1.png")}")
    img_share2.save(os.path.join(OUTPUT_DIR, "share2.png"))
    print(f"[INFO] Share 2 saved to {os.path.join(OUTPUT_DIR, "share2.png")}")
    img_reconstructed.save(os.path.join(OUTPUT_DIR, "reconstructed.png"))
    print(f"[INFO] Reconstructed image saved to {os.path.join(OUTPUT_DIR, "reconstructed.png")}")

def main():
    # Step 1: Let the user choose an image
    image_path = select_image()
    if not image_path:
        print("[INFO] No image selected. Exiting.")
        return

    # Step 2: Preprocess the image (grayscale, resize, threshold)
    try:
        processed_image_bw = preprocess_image(image_path)
    except Exception as e:
        print(f"[ERROR] Could not preprocess image: {e}")
        return

    # Step 3: Encrypt the image into two shares
    share1, share2 = encrypt_image(processed_image_bw)

    # Step 4: Decrypt (reconstruct) the image
    reconstructed_image = decrypt_image(share1, share2)

    # Step 5: Save the output images
    save_images(share1, share2, reconstructed_image)

    print("[INFO] Visual Cryptography System finished successfully!")

if __name__ == "__main__":
    main() 