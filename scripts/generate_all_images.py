import argparse
import os
import sys
import subprocess
import multiprocessing

from ._generate_base_image import states
GENERATE_BASE_IMAGE = os.path.join(os.path.dirname(__file__), "_generate_base_image.py")

if __name__ == "__main__":
    num_jobs = multiprocessing.cpu_count()

    parser = argparse.ArgumentParser(description='Generate state base images')
    parser.add_argument("--output", type=str, help="Output directory")
    parser.add_argument("-j", "--jobs", type=int, default=num_jobs, help="Number of processes to use")
    args = parser.parse_args()
    print("Number of processes: {}".format(args.jobs))

    if not args.output:
        raise ValueError("Output directory not specified")
    if not os.path.exists(args.output):
        os.mkdir(args.output)
    elif not os.path.isdir(args.output):
        raise ValueError("Output is not a directory")

    # Do the US first, this also helps us cache the interstates, borders, lakes, rivers, etc.
    process = subprocess.Popen(
        [
            sys.executable,
            GENERATE_BASE_IMAGE,
            "--image",
            "US",
            "--output",
            args.output,
        ]
    )
    process.wait()
    if process.returncode != 0:
        raise ValueError("Process returned non-zero return code: {}".format(process.returncode))

    # Grab states in batches of jobs
    for i in range(0, len(states), args.jobs):
        chunks = states[i:i + args.jobs]
        processes = []
        for chunk in chunks:
            print("Spawning process for chunk: {}".format(chunk))
            processes.append(subprocess.Popen(
                [
                    sys.executable,
                    GENERATE_BASE_IMAGE,
                    "--image",
                    chunk,
                    "--output",
                    args.output,
                ]
            ))
        # Wait for all processes to finish
        for process in processes:
            process.wait()
            # Check return code
            if process.returncode != 0:
                raise ValueError("Process returned non-zero return code: {}".format(process.returncode))
