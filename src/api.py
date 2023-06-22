import sys
from threading import Thread
import traceback
import time

from .config import get_config
from .orm import ActiveAlerts, Installation

import requests

_wx_watcher_manager = None


def get_wx_watcher_manager():
    global _wx_watcher_manager
    if _wx_watcher_manager is None:
        _wx_watcher_manager = WXWatcherManager()
    return _wx_watcher_manager


class WXWatcherManager():
    def __init__(self):
        self._watchers = []
        for installation in Installation.bot_started_index.query(True):
            print(f"Adding watcher for {installation.state}")
            self.add_and_start_watcher(WXWatcher(installation.state))

    def add_and_start_watcher(self, watcher):
        for w in self._watchers:
            if w.state == watcher.state:
                print(f"Watcher for {watcher.state} already exists")
                return
        self._watchers.append(watcher)
        self._watchers[-1].watch()

    def stop(self):
        for watcher in self._watchers:
            watcher.stop()


class WXWatcher():
    def __init__(self, state):
        self._thread = Thread(target=self._watch_loop)
        self.state = state

    def _get_alerts_geojson(self):
        url = 'https://api.weather.gov/alerts/active?area={}&status=actual'.format(self.state)
        response = requests.get(
            url,
            headers={
                'Accept': 'application/geo+json',
                'User-Agent': get_config().get('nws', 'user_agent')
            }
        )
        return response.json()

    def _seen_alert(self, alert_id):
        # Query for state and ID in ActiveAlerts
        res = None
        for res_ in ActiveAlerts.query(alert_id):
            res = res_
            break
        if res is None:
            # Add to ActiveAlerts
            ActiveAlerts(
                id=alert_id,
                state=self.state
            ).save()
            return False
        else:
            return True

    def _process_alerts(self):
        alertsJSON = self._get_alerts_geojson()
        if 'type' not in alertsJSON or alertsJSON['type'] != 'FeatureCollection':
            print('Invalid GeoJSON FeatureCollection')
            return []

        if 'features' not in alertsJSON:
            print('No alerts found')
            return []

        # Check the db for all alerts with the same state. If alerts in the db aren't in the
        # API response, they have expired and should be removed from the db.
        # Get all the alerts for the state
        state_alerts = ActiveAlerts.state_index.query(self.state)
        # Get the IDs of the alerts in the API response
        api_alert_ids = [feature['properties']['id'] for feature in alertsJSON['features']]
        # Get the IDs of the alerts in the db
        db_alert_ids = [alert.id for alert in state_alerts]
        # Get the IDs of the alerts that are in the db but not in the API response
        expired_alert_ids = [alert_id for alert_id in db_alert_ids if alert_id not in api_alert_ids]
        # Delete the expired alerts from the db
        for alert_id in expired_alert_ids:
            print('Removing expired alert: {}'.format(alert_id))
            for alert in ActiveAlerts.query(alert_id):
                alert.delete()

        for feature in alertsJSON['features']:
            from .alert import WXAlert
            if not self._seen_alert(feature['properties']['id']):
                alert = WXAlert(feature, self.state)
                print('New alert: {}'.format(alert.id))
                from .alert import send_alert
                send_alert(alert)
            else:
                print('Already seen alert: {}'.format(feature['properties']['id']))

    def _get_alerts(self):
        alertsJSON = self._get_alerts_geojson()
        if 'type' not in alertsJSON or alertsJSON['type'] != 'FeatureCollection':
            print('Invalid GeoJSON FeatureCollection')
            return []

        if 'features' not in alertsJSON:
            print('No alerts found')
            return []

        # Check the db for all alerts with the same state. If alerts in the db aren't in the
        # API response, they have expired and should be removed from the db.
        # Get all the alerts for the state
        state_alerts = ActiveAlerts.state_index.query(self.state)
        # Get the IDs of the alerts in the API response
        api_alert_ids = [feature['properties']['id'] for feature in alertsJSON['features']]
        # Get the IDs of the alerts in the db
        db_alert_ids = [alert.id for alert in state_alerts]
        # Get the IDs of the alerts that are in the db but not in the API response
        expired_alert_ids = [alert_id for alert_id in db_alert_ids if alert_id not in api_alert_ids]
        # Delete the expired alerts from the db
        for alert_id in expired_alert_ids:
            print('Removing expired alert: {}'.format(alert_id))
            for alert in ActiveAlerts.query(alert_id):
                alert.delete()

        alerts = []
        for feature in alertsJSON['features']:
            from .alert import WXAlert
            if not self._seen_alert(feature['properties']['id']):
                alert = WXAlert(feature, self.state)
                print('New alert: {}'.format(alert.id))
                alerts.append(alert)
            else:
                print('Already seen alert: {}'.format(feature['properties']['id']))
        return alerts

    def _watch_loop(self):
        try:
            while True:
                time_start = time.time()
                self._process_alerts()
                time.sleep(max(0, 30 - (time.time() - time_start)))
        except Exception as e:
            print(e)
            traceback.print_exception(*sys.exc_info())
            self._watch_loop()

    def watch(self):
        if self._thread is not None and self._thread.is_alive():
            print('WXWatcher already running')
            return
        if self._thread is None:
            self._thread = Thread(target=self._watch_loop)
        self._thread.start()

    def stop(self):
        if self._thread is None or not self._thread.is_alive():
            print('WXWatcher not running')
            return
        self._thread.join(timeout=1)
        self._thread = None
