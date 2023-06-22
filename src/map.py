import io

from .config import get_config

from awips.dataaccess import DataAccessLayer
import matplotlib.pyplot as plt
import matplotlib
import cartopy.crs as ccrs
from cartopy.feature import ShapelyFeature, NaturalEarthFeature
from shapely.ops import unary_union
from adjustText import adjust_text
import numpy as np
import requests

# Server, Data Request Type, and Database Table
DataAccessLayer.changeEDEXHost("edex-cloud.unidata.ucar.edu")


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


# Standard map plot
def make_map(bbox, projection=ccrs.PlateCarree()):
    fig, ax = plt.subplots(figsize=(12, 12),
                           subplot_kw=dict(projection=projection))
    ax.set_extent(bbox)
    # ax.coastlines(resolution='50m')
    return fig, ax


def plot_states(ax):
    # Plot political/state boundaries handled by Cartopy
    political_boundaries = NaturalEarthFeature(category='cultural',
                                               name='admin_0_boundary_lines_land',
                                               scale='50m', facecolor='none')
    states = NaturalEarthFeature(category='cultural',
                                 name='admin_1_states_provinces_lines',
                                 scale='50m', facecolor='none')
    ax.add_feature(political_boundaries, linestyle='-', edgecolor='black', zorder=1)
    ax.add_feature(states, linestyle='-', edgecolor='black', linewidth=2, zorder=1)


def plot_counties(ax, state, envelope=None):
    request = DataAccessLayer.newDataRequest('maps')
    request.addIdentifier('table', 'mapdata.county')
    request.setEnvelope(envelope)
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

    # Plot counties
    shape_feature = ShapelyFeature(counties, ccrs.PlateCarree(),
                                   facecolor='none', linestyle="-", edgecolor='#86989B')
    ax.add_feature(shape_feature, zorder=3)


def plot_interstates(ax, envelope=None):
    # Define the request for the interstate query
    request = DataAccessLayer.newDataRequest('maps', envelope=envelope)
    request.addIdentifier('table', 'mapdata.interstate')
    request.addIdentifier('geomField', 'the_geom')
    interstates = DataAccessLayer.getGeometryData(request)
    print("Using " + str(len(interstates)) + " interstate MultiLineStrings")

    # Plot interstates
    for ob in interstates:
        shape_feature = ShapelyFeature(ob.getGeometry(), ccrs.PlateCarree(),
                                       facecolor='none', linestyle="-", edgecolor='#e4a184')
        ax.add_feature(shape_feature, zorder=2)


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


def plot_rivers(ax, envelope=None):
    # Define request for rivers
    request = DataAccessLayer.newDataRequest('maps', envelope=envelope)
    request.addIdentifier('table', 'mapdata.majorrivers')
    request.addIdentifier('geomField', 'the_geom')
    rivers = DataAccessLayer.getGeometryData(request)
    print("Using " + str(len(rivers)) + " river MultiLineStrings")

    # Plot rivers
    shape_feature = ShapelyFeature([river.getGeometry() for river in rivers], ccrs.PlateCarree(),
                                   facecolor='none', linestyle=":", edgecolor='#1e90ff')
    ax.add_feature(shape_feature, zorder=2)


def plot_lakes(ax, envelope=None):
    # Define request for lakes
    request = DataAccessLayer.newDataRequest('maps', envelope=envelope)
    request.addIdentifier('table', 'mapdata.lake')
    request.addIdentifier('geomField', 'the_geom')

    # Get lake geometries
    response = DataAccessLayer.getGeometryData(request)
    print("Using " + str(len(response)) + " lake MultiPolygons")

    # Plot lakes
    shape_feature = ShapelyFeature([lake.getGeometry() for lake in response], ccrs.PlateCarree(),
                                   facecolor='#1e90ff', linestyle="-", edgecolor='#1e90ff')
    ax.add_feature(shape_feature, zorder=2, alpha=0.3)


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
        # Remove any data less than 5dbZ
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
    bbox, envelope = get_boundaries(alert.state)
    fig, ax = make_map(bbox=bbox)
    ax.grid(False)
    plot_states(ax)
    plot_counties(ax, alert.state, envelope)
    plot_interstates(ax, envelope=envelope)
    # plot_cities(ax, envelope=envelope, adjust=True)
    plot_lakes(ax, envelope=envelope)
    plot_rivers(ax, envelope=envelope)
    if alert.should_show_radar():
        plot_radar(fig, ax, get_closest_station(alert.polygon), envelope=envelope)
    alert.plot(ax)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image = buf.getvalue()
    buf.close()
    return image


def plot_radar_from_station(state, station):
    bbox, envelope = get_boundaries(state)
    fig, ax = make_map(bbox=bbox)
    ax.grid(False)
    plot_states(ax)
    plot_counties(ax, state, envelope)
    plot_interstates(ax, envelope=envelope)
    # plot_cities(ax, envelope=envelope, adjust=True)
    plot_lakes(ax, envelope=envelope)
    plot_rivers(ax, envelope=envelope)
    plot_radar(fig, ax, station, envelope=envelope)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image = buf.getvalue()
    buf.close()
    return image


def plot_all_state_alerts(state):
    alerts = _get_alerts(state)
    bbox, envelope = get_boundaries(state)
    fig, ax = make_map(bbox=bbox)
    ax.grid(False)
    plot_states(ax)
    plot_counties(ax, state, envelope)
    plot_interstates(ax, envelope=envelope)
    # plot_cities(ax, envelope=envelope, adjust=True)
    plot_lakes(ax, envelope=envelope)
    plot_rivers(ax, envelope=envelope)
    seen_stations = []
    for alert in alerts:
        if alert.should_show_radar():
            closest_station = get_closest_station(alert.polygon)
            if closest_station not in seen_stations:
                seen_stations.append(closest_station)
                plot_radar(fig, ax, closest_station, envelope=envelope, add_legend=len(seen_stations) == 1)
        alert.plot(ax)
    plt.show()


def plot_all_state_alerts_one_at_a_time(state):
    alerts = _get_alerts(state)
    for alert in alerts:
        print(alert)
        bbox, envelope = get_boundaries(state)
        fig, ax = make_map(bbox=bbox)
        ax.grid(False)
        plot_states(ax)
        plot_counties(ax, state, envelope)
        plot_interstates(ax, envelope=envelope)
        # plot_cities(ax, envelope=envelope, adjust=True)
        plot_lakes(ax, envelope=envelope)
        plot_rivers(ax, envelope=envelope)
        seen_stations = []
        if alert.should_show_radar():
            closest_station = get_closest_station(alert.polygon)
            if closest_station not in seen_stations:
                seen_stations.append(closest_station)
                plot_radar(fig, ax, closest_station, envelope=envelope, add_legend=len(seen_stations) == 1)
        alert.plot(ax)
        plt.show()


def plot_alert_area(alert):
    alert_bbox, alert_envelope = get_boundaries_from_polygon(alert.polygon)
    fig, ax = make_map(bbox=alert_bbox)
    ax.grid(False)
    plot_states(ax)
    plot_counties(ax, alert.state, alert_envelope)
    plot_interstates(ax, envelope=alert_envelope)
    # plot_cities(ax, envelope=envelope, adjust=True)
    plot_lakes(ax, envelope=alert_envelope)
    plot_rivers(ax, envelope=alert_envelope)
    if alert.should_show_radar():
        plot_radar(fig, ax, get_closest_station(alert.polygon), envelope=alert_envelope)
    plt.show()


if __name__ == "__main__":
    plot_all_state_alerts_one_at_a_time('OK')
