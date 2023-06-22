import sys
import traceback

from .api import get_wx_watcher_manager


def main():
    get_wx_watcher_manager()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        get_wx_watcher_manager().stop()
    except Exception as e:
        get_wx_watcher_manager().stop()
        print(e)
        traceback.print_exception(*sys.exc_info())
