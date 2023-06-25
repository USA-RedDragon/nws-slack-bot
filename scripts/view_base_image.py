import argparse
import pickle

import matplotlib.pyplot as plt

from ._generate_base_image import states


def main():
    parser = argparse.ArgumentParser(description='Generate state base images')
    parser.add_argument('--image', type=str, help='Image to generate')
    parser.add_argument('--image-dir', type=str, help='Directory containing images')
    args = parser.parse_args()

    if not args.image:
        raise ValueError("Image not specified")
    if not args.image_dir:
        raise ValueError("Image directory not specified")
    if args.image not in states and args.image != "US":
        raise ValueError("Invalid state")

    with open(f"{args.image_dir}/{args.image}.pickle", "rb") as f:
        pickle.load(f)
    plt.show()
    return


if __name__ == "__main__":
    main()
