from .spc_common import send_outlook_image


def main():
    print("SPC Day 1")
    print("Running script")
    send_outlook_image(day=1, type="cat")
    send_outlook_image(day=1, type="hail")
    send_outlook_image(day=1, type="torn")
    send_outlook_image(day=1, type="wind")
    print("Done")
    return


if __name__ == "__main__":
    main()
