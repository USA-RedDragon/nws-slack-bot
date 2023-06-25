import sys

from .spc_common import is_cdt_active, send_outlook_image


def main():
    print("SPC Days 4-8")
    # Get the parameter
    if len(sys.argv) != 2:
        raise ValueError("Invalid number of arguments")
    tz = sys.argv[1]
    if tz not in ["cdt", "cst"]:
        raise ValueError("Invalid timezone")
    # Check if daylight savings time is active in central time
    if tz == "cdt" and not is_cdt_active():
        print("Daylight savings time is not active in central time, exiting")
        return
    if tz == "cst" and is_cdt_active():
        print("Daylight savings time is active in central time, exiting")
        return
    # Run the script
    print("Running script")
    send_outlook_image(day=4, type="prob")
    send_outlook_image(day=5, type="prob")
    send_outlook_image(day=6, type="prob")
    send_outlook_image(day=7, type="prob")
    send_outlook_image(day=8, type="prob")
    print("Done")
    return


if __name__ == "__main__":
    main()
