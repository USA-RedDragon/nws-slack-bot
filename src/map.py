import io
import pickle

from .config import get_config

from adjustText import adjust_text
from awips.dataaccess import DataAccessLayer
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib
from shapely.ops import unary_union
import numpy as np
import requests

# Server, Data Request Type, and Database Table
DataAccessLayer.changeEDEXHost("edex-cloud.unidata.ucar.edu")

matplotlib.use('Agg')


def _get_alerts_geojson(state):
    url = 'https://api.weather.gov/alerts/active?area={}&status=actual'.format(state)
    response = requests.get(
        url,
        headers={
            'Accept': 'application/geo+json',
            'User-Agent': get_config().get('nws', 'user_agent')
        }
    )
    return response.json()


def _get_alerts(state):
    alertsJSON = _get_alerts_geojson(state)
    if 'type' not in alertsJSON or alertsJSON['type'] != 'FeatureCollection':
        print('Invalid GeoJSON FeatureCollection')
        return []

    if 'features' not in alertsJSON:
        print('No alerts found')
        return []

    alerts = []
    for feature in alertsJSON['features']:
        from .alert import WXAlert
        alerts.append(WXAlert(feature, state))
    return alerts


_nws_reflectivity_colors = matplotlib.colors.ListedColormap([
    "#764fab",  # -30
    "#7c689a",  # -25
    "#86818e",  # -20
    "#aeaea3",  # -15
    "#cccc99",  # -10
    "#9ba1a6",  # -5
    "#77819d",  # 0
    "#5a6c9f",  # 5
    "#405aa0",  # 10
    "#419b96",  # 15
    "#40d38d",  # 20
    "#20af45",  # 25
    "#018d01",  # 30
    "#83b100",  # 35
    "#eed000",  # 40
    "#f6ad00",  # 45
    "#f70000",  # 50
    "#df0000",  # 55
    "#ffc9ff",  # 60
    "#ffabfb",  # 65
    "#ad00ff",  # 70
    "#a200f9",  # 75
    "#00e1ec",  # 80
    "#3333cc",  # 85+
])


def plot_radar(fig, ax, station, envelope=None, add_legend=True):
    # Define request for radar
    request = DataAccessLayer.newDataRequest('radar')
    request.setEnvelope(envelope)

    request.setLocationNames(station)

    request.setParameters("Composite Refl")
    availableLevels = DataAccessLayer.getAvailableLevels(request)
    if availableLevels:
        request.setLevels(availableLevels[0])
    else:
        print("No levels found for " + "Composite Refl")

    times = DataAccessLayer.getAvailableTimes(request)

    if times:
        response = DataAccessLayer.getGridData(request, [times[-1]])
        print("Recs : ", len(response))

        if response:
            grid = response[0]
        else:
            return
        data = grid.getRawData()
        lons, lats = grid.getLatLonCoords()

        print('Time :', str(grid.getDataTime()))
        flat = np.ndarray.flatten(data)
        print('Name :', str(grid.getLocationName()))
        print('Prod :', str(grid.getParameter()))
        print('Range:', np.nanmin(flat), " to ", np.nanmax(flat), " (Unit :", grid.getUnit(), ")")
        print('Size :', str(data.shape))
        print()

        cs = ax.pcolormesh(lons, lats, data, cmap=_nws_reflectivity_colors, zorder=4, alpha=0.8, norm=matplotlib.colors.Normalize(-30, 85))
        if add_legend:
            cbar = fig.colorbar(cs, extend='both', shrink=0.5, orientation='horizontal')
            cbar.set_label(grid.getParameter() + " " + "Valid: " + str(grid.getDataTime().getRefTime()))


def get_boundaries_from_polygon(poly):
    merged_counties = unary_union(poly)
    envelope = merged_counties.buffer(3)

    bounds = merged_counties.bounds
    bbox = [bounds[0]-.25, bounds[2]+.25, bounds[1]-.25, bounds[3]+.25]

    return bbox, envelope


def get_boundaries(state):
    request = DataAccessLayer.newDataRequest('maps')
    request.addIdentifier('table', 'mapdata.county')
    request.setLocationNames(state)
    request.addIdentifier('geomField', 'the_geom')
    # enable location filtering (inLocation)
    request.addIdentifier('inLocation', 'true')
    request.addIdentifier('locationField', 'state')

    # Get response and create dict of county geometries
    response = DataAccessLayer.getGeometryData(request)

    counties = []
    for ob in response:
        counties.append(ob.getGeometry())
    print("Using " + str(len(counties)) + " county MultiPolygons")

    # All WFO counties merged to a single Polygon
    merged_counties = unary_union(counties)
    envelope = merged_counties.buffer(0)

    # Get bounds of this merged Polygon to use as buffered map extent
    bounds = merged_counties.bounds
    bbox = [bounds[0]-.25, bounds[2]+.25, bounds[1]-.25, bounds[3]+.25]

    return bbox, envelope


def get_closest_station(poly):
    # Get the center of the polygon
    center = poly.centroid

    response = requests.get(
                'https://api.weather.gov/points/{},{}'.format(center.y, center.x),
                headers={
                    'Accept': 'application/geo+json',
                    'User-Agent': get_config().get('nws', 'user_agent')
                })
    if response.status_code != 200:
        print("Error getting station")
        return
    if 'properties' not in response.json():
        print("Error getting station")
        return
    station = response.json()['properties']['radarStation']
    print("Station: ", station)
    return station.lower()


def plot_alert_on_state(alert):
    _, envelope = get_boundaries(alert.state)
    with open(f".states/{alert.state}.pickle", "rb") as f:
        fig = pickle.load(f)
    ax = fig.axes[0]
    if alert.should_show_radar():
        plot_radar(fig, ax, get_closest_station(alert.polygon), envelope=envelope)
    alert.plot(ax)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    image = buf.getvalue()
    buf.close()
    plt.close()
    return image


def plot_radar_from_station(state, station):
    _, envelope = get_boundaries(state)
    with open(f".states/{state}.pickle", "rb") as f:
        fig = pickle.load(f)
    ax = fig.axes[0]
    plot_radar(fig, ax, station, envelope=envelope)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    image = buf.getvalue()
    buf.close()
    plt.close()
    return image


def plot_all_state_alerts(state):
    alerts = _get_alerts(state)
    _, envelope = get_boundaries(state)
    with open(f".states/{state}.pickle", "rb") as f:
        fig = pickle.load(f)
    ax = fig.axes[0]
    seen_stations = []
    for alert in alerts:
        if alert.should_show_radar():
            closest_station = get_closest_station(alert.polygon)
            if closest_station not in seen_stations:
                seen_stations.append(closest_station)
                plot_radar(fig, ax, closest_station, envelope=envelope, add_legend=len(seen_stations) == 1)
            else:
                print("Skipping duplicate station: ", closest_station)
        alert.plot(ax)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    image = buf.getvalue()
    buf.close()
    plt.close()
    return image


def plot_all_state_alerts_one_at_a_time(state):
    alerts = _get_alerts(state)
    for alert in alerts:
        print(alert)
        with open(f".states/{state}.pickle", "rb") as f:
            fig = pickle.load(f)
        ax = fig.axes[0]
        _, envelope = get_boundaries(state)
        seen_stations = []
        if alert.should_show_radar():
            closest_station = get_closest_station(alert.polygon)
            if closest_station not in seen_stations:
                seen_stations.append(closest_station)
                plot_radar(fig, ax, closest_station, envelope=envelope, add_legend=len(seen_stations) == 1)
        alert.plot(ax)
        plt.show()


def plot_alert_area(alert):
    with open(f".states/{alert.state}.pickle", "rb") as f:
        fig = pickle.load(f)
    ax = fig.axes[0]
    _, alert_envelope = get_boundaries_from_polygon(alert.polygon)
    if alert.should_show_radar():
        plot_radar(fig, ax, get_closest_station(alert.polygon), envelope=alert_envelope)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    image = buf.getvalue()
    buf.close()
    plt.close()
    return image


def plot_cities(ax, envelope=None, adjust=False):
    # Define the request for the city query
    request = DataAccessLayer.newDataRequest('maps', envelope=envelope)
    request.addIdentifier('table', 'mapdata.city')
    request.addIdentifier('geomField', 'the_geom')
    request.setParameters('name', 'population', 'prog_disc')
    cities = DataAccessLayer.getGeometryData(request)
    print("Queried " + str(len(cities)) + " total cities")

    # Set aside two arrays - one for the geometry of the cities and one for their names
    citylist = []
    cityname = []
    # For OUN, progressive disclosure values above 50 and pop above 5000 looks good
    for ob in cities:
        if ob.getString("population") != 'None':
            if ob.getNumber("prog_disc") > 2000 and int(ob.getString("population")) > 10000:
                citylist.append(ob.getGeometry())
                cityname.append(ob.getString("name"))
    print("Plotting " + str(len(cityname)) + " cities")

    # Plot city markers
    ax.scatter([point.x for point in citylist],
               [point.y for point in citylist],
               transform=ccrs.PlateCarree(), marker="+", facecolor='black', zorder=3)
    # Plot city names
    texts = []
    for i, txt in enumerate(cityname):
        texts.append(
            ax.text(citylist[i].x, citylist[i].y, txt, ha='center', va='center', transform=ccrs.PlateCarree(), zorder=3)
        )
    if adjust:
        adjust_text(texts, ax=ax, time_lim=1)
