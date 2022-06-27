import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def get_data():
    raw_data_act = pd.read_csv('data/Data.csv', delimiter=',', header=0)
    raw_data_act = raw_data_act.drop(['Date', 'HR','Kp', 'SSN', 'Ap', 'F'], axis=1)

    raw_data_timestamp = pd.DataFrame(
        {'hours': pd.to_datetime(pd.date_range('2018-01-10', '2018-01-27', freq='1H', closed='left'))}
    )
    raw_data_all_features = pd.concat([raw_data_timestamp, raw_data_act], axis=1)
    raw_data_all_features = raw_data_all_features.set_index('hours')
    return raw_data_all_features


def read_forecasts():
    forecast_gp = pd.read_csv('results_4_paper/metrics/forecast_gp.csv', header=None)
    forecast_ffnn = pd.read_csv('results_4_paper/metrics/forecast_ffnn.csv', header=None)
    forecast_deepar = pd.read_csv('results_4_paper/metrics/forecast_deepar.csv', header=None)

    forecast_gp.set_index(1, inplace=True)
    forecast_gp.rename(columns={0: "gp"}, inplace=True)

    forecast_ffnn.set_index(1, inplace=True)
    forecast_ffnn.rename(columns={0: "ffnn"}, inplace=True)

    forecast_deepar.set_index(1, inplace=True)
    forecast_deepar.rename(columns={0: "deepar"}, inplace=True)

    # concat actual tec data
    raw_data_all_features = get_data()
    data = pd.concat([forecast_gp, forecast_ffnn, forecast_deepar], axis=1)
    data['actual'] = raw_data_all_features.TEC[-96:]

    # concat irt data
    irt_data_raw = pd.read_csv('data/irt_data.csv', delimiter=',', header=0)
    irt_data_raw = irt_data_raw.drop(['Time'], axis=1)
    irt_data = irt_data_raw.T.stack().reset_index(name='irt')
    irt_data.set_index(data.index, inplace=True)
    data['irt'] = irt_data.irt

    # data.set_index(pd.date_range('2018-01-23', '2018-01-27', freq='1H', closed='left'), inplace=True)

    return data


def create_comparative_plot(data):
    legend = ["GP", "FFNN", "DeepAR", 'Actual', "IRI 2016"]
    fig, ax = plt.subplots(1, 1, sharex=True, sharey=True, figsize=(10, 7))
    plt.plot(pd.to_datetime(data.index), data.gp)
    plt.plot(pd.to_datetime(data.index), data.ffnn)
    plt.plot(pd.to_datetime(data.index), data.deepar)
    plt.plot(pd.to_datetime(data.index), data.actual)
    plt.plot(pd.to_datetime(data.index), data.irt)

    # plt.plot(pd.to_datetime(data.index), data.gp)
    # plt.plot(pd.to_datetime(data.index), data.ffnn)
    # plt.plot(pd.to_datetime(data.index), data.deepar)
    # plt.plot(pd.to_datetime(data.index), data.actual)
    # plt.plot(pd.to_datetime(data.index), data.irt)
    plt.grid(which="both")

    # ref: https://matplotlib.org/3.1.0/gallery/ticks_and_spines/date_concise_formatter.html
    # ref: https://matplotlib.org/3.1.1/api/dates_api.html#matplotlib.dates.DayLocator
    locator = mdates.DayLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

    plt.ticklabel_format(axis='y', style='plain')
    plt.legend(legend, loc="upper right")
    plt.xlabel('Days')
    plt.ylabel('TEC')
    plt.savefig("results_4_paper/plots/forecast_comparison.png")


if __name__ == "__main__":
    data= read_forecasts()
    create_comparative_plot(data)
