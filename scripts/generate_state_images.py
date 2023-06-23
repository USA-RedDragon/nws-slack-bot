# This script shall generate pickled matplotlib figures of the 50 states containing rivers, lakes, highways, county borders, and state borders.

import argparse
import os
import pickle

from awips.dataaccess import DataAccessLayer
import cartopy.crs as ccrs
from cartopy.feature import ShapelyFeature, COASTLINE, OCEAN, LAKES, RIVERS, STATES
import matplotlib
import matplotlib.pyplot as plt
from shapely.ops import unary_union

DataAccessLayer.changeEDEXHost("edex-cloud.unidata.ucar.edu")

states = [
    "AL",
    "AK",
    "AS",
    "AR",
    "AZ",
    "CA",
    "CO",
    "CT",
    "DE",
    "DC",
    "FL",
    "GA",
    "GU",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "PR",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VI",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
    "MP",
    "PW",
    "FM",
    "MH",
]


def main():
    parser = argparse.ArgumentParser(description='Generate state base images')
    parser.add_argument('--state', type=str, help='State to generate')
    parser.add_argument("--all", action="store_true", help="Generate all states")
    parser.add_argument("--load-and-view", action="store_true", help="Load and view the generated state")
    parser.add_argument("--output", type=str, help="Output directory")
    args = parser.parse_args()

    if not args.output:
        raise ValueError("Output directory not specified")

    if not args.load_and_view:
        matplotlib.use('Agg')
    else:
        if not args.state:
            raise ValueError("State not specified")
        with open(f"{args.output}/{args.state}.pickle", "rb") as f:
            pickle.load(f)
        plt.show()
        return

    if not os.path.exists(args.output):
        os.mkdir(args.output)
    elif not os.path.isdir(args.output):
        raise ValueError("Output is not a directory")

    if args.all and not args.state:
        generate_country(args.output)
        plt.close()
        for state in states:
            generate_state(state, args.output)
            plt.close()
    elif args.state:
        if args.state not in states:
            raise ValueError("Invalid state")
        state = args.state.upper()
        generate_state(state, args.output)
        plt.close()


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


def generate_state(state, output_dir):
    request = DataAccessLayer.newDataRequest('maps')
    request.addIdentifier('table', 'mapdata.county')
    request.setLocationNames(state)
    request.addIdentifier('geomField', 'the_geom')
    # enable location filtering (inLocation)
    request.addIdentifier('inLocation', 'true')
    request.addIdentifier('locationField', 'state')

    response = DataAccessLayer.getGeometryData(request)

    counties = []
    for ob in response:
        counties.append(ob.getGeometry())
    print("Using " + str(len(counties)) + " county MultiPolygons")

    # All WFO counties merged to a single Polygon
    merged_counties = unary_union(counties)
    envelope = merged_counties.buffer(0)
    # Plot the merged Polygon
    shape_feature = ShapelyFeature(merged_counties, ccrs.PlateCarree(),
                                   facecolor='none', linestyle="-", linewidth=1.5, edgecolor='black')

    # Get bounds of this merged Polygon to use as buffered map extent
    bounds = merged_counties.bounds
    bbox = [bounds[0]-.25, bounds[2]+.25, bounds[1]-.25, bounds[3]+.25]

    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(projection=ccrs.PlateCarree()))
    ax.set_extent(bbox)
    ax.grid(False)
    ax.add_feature(shape_feature, zorder=1)
    shape_feature = ShapelyFeature(counties, ccrs.PlateCarree(),
                                   facecolor='none', linestyle="-", edgecolor='#86989B')
    ax.add_feature(shape_feature, zorder=3)
    plot_interstates(ax, envelope=envelope)
    plot_lakes(ax, envelope=envelope)
    plot_rivers(ax, envelope=envelope)

    with open(os.path.join(output_dir, state + ".pickle"), "wb") as outfile:
        pickle.dump(fig, outfile)


def plot_country(ax):
    # Plot political/state boundaries handled by Cartopy
    # political_boundaries = NaturalEarthFeature(category='cultural',
    #                                            name='admin_0_boundary_lines_land',
    #                                            scale='50m', facecolor='none')
    # ax.add_feature(political_boundaries, linestyle='-', edgecolor='black', linewidth=1, zorder=1)
    ax.add_feature(STATES, linestyle='-', edgecolor='black', linewidth=1, zorder=1)
    ax.add_feature(COASTLINE, linestyle='-', edgecolor='black', linewidth=1, zorder=1)
    ax.add_feature(OCEAN, linestyle='-', facecolor='#1e90ff', edgecolor='#1e90ff', zorder=1, alpha=0.4)
    ax.add_feature(LAKES, linestyle='-', facecolor='#1e90ff', edgecolor='#1e90ff', zorder=1, alpha=0.4)
    ax.add_feature(RIVERS, linestyle='-', facecolor='#1e90ff', edgecolor='#1e90ff', zorder=1, alpha=0.4)


def generate_country(output_dir):
    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(projection=ccrs.PlateCarree()))
    ax.grid(False)
    bounds = [-125, -66.5, 20, 50]
    ax.set_extent(bounds)

    class Bounds:
        bounds = [-125, -66.5, 20, 50]

        def __init__(self, bounds):
            self.bounds = bounds

    class Anon:
        envelope = Bounds(bounds)

    plot_interstates(ax, envelope=Anon())
    plot_country(ax)
    with open(os.path.join(output_dir, "US.pickle"), "wb") as outfile:
        pickle.dump(fig, outfile)


if __name__ == "__main__":
    main()
