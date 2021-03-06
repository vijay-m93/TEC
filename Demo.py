from gluonts.evaluation.backtest import make_evaluation_predictions
from gluonts.dataset.repository.datasets import get_dataset
from gluonts.model import simple_feedforward
from gluonts.evaluation import Evaluator
from gluonts.dataset.util import to_pandas
from gluonts.model import deepar
from gluonts.dataset import common
from gluonts.trainer import Trainer

import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt


def build_ff_model():
    # get the csv file as a dataframe
    raw_data_act = pd.read_excel('TEC_Data.xls', index_col=False)

    raw_data_timestamp = pd.DataFrame(
        {'hours': pd.date_range('2018-01-10', '2018-01-27', freq='1H', closed='left')}
    )

    raw_data = pd.concat([raw_data_timestamp, raw_data_act], axis= 1)
    raw_data = raw_data.set_index('hours')


    # convert the raw data into an object recognised by GluonTS
    # start: the starting index of the dataframe
    # target: the actual time-series data that we want to model
    # freq: the frequency with which the data is collected

    metadata = {'prediction_length': 24,
                'freq': "1H",
                'start': raw_data.index[0]  # or 'start': pd.Timestamp("2015-12-31 23:00:00", freq='15min')
                }

    #
    # train_data = common.ListDataset(
    #     [{"start": raw_data.index[0], "target": raw_data.TEC[:"2018-01-10 00:00:00"]}], freq="1H")

    train_data = common.ListDataset([
        {"start": metadata['start'],
         "target": raw_data.TEC[:-metadata['prediction_length']].tolist(),  # or wrap with np.array()
         }],
        freq=metadata['freq'])



    # create an Estimator with simple feed forward model
    # an object of Trainer() class is used to customize Estimator
    estimator = simple_feedforward.SimpleFeedForwardEstimator(
                                    freq="1H",
                                    prediction_length=24,
                                    trainer=Trainer(
                                                    ctx="cpu",
                                                    epochs=1,
                                                    learning_rate=1e-3
                                                    ))

    # create a Predictor by training the Estimator with training dataset
    predictor = estimator.train(training_data=train_data)

    # get predictions for the whole forecast horizon
    for model_train_data, predictions in zip(train_data, predictor.predict(train_data)):
        # plot only the last 100 timestamps of the training dataset
        to_pandas(model_train_data)[-100:].plot()
        # plot the forecasts from the model
        predictions.plot(output_file='ff-model.png', color='r')


def build_deepar_model():
    # get the financial data "exchange_rate"
    gluon_data = get_dataset("exchange_rate", regenerate=True)
    train_data = next(iter(gluon_data.train))
    test_data = next(iter(gluon_data.test))
    meta_data = gluon_data.metadata

    # data set visualisation
    fig, ax = plt.subplots(1, 1, figsize=(11, 8))
    to_pandas(train_data).plot(ax=ax)
    ax.grid(which="both")
    ax.legend(["train data"], loc="upper left")
    plt.savefig("dataset.png")

    # visualize various members of the 'gluon_data.*'
    print(train_data.keys())
    print(test_data.keys())
    print(meta_data)

    # convert dataset into an object recognised by GluonTS
    training_data = common.ListDataset(gluon_data.train, freq=meta_data.freq)
    testing_data = common.ListDataset(gluon_data.test, freq=meta_data.freq)

    # create an Estimator with DeepAR
    # an object of Trainer() class is used to customize Estimator
    estimator = deepar.DeepAREstimator(
                                    freq=meta_data.freq,
                                    prediction_length=meta_data.prediction_length,
                                    trainer=Trainer(
                                                    ctx="cpu",
                                                    epochs=1,
                                                    learning_rate=1e-4
                                                    ))

    # create a Predictor by training the Estimator with training dataset
    predictor = estimator.train(training_data=training_data)

    # make predictions
    forecasts, test_series = make_evaluation_predictions(dataset=testing_data, predictor=predictor, num_samples=10)

    # visualise forecasts
    prediction_intervals = (50.0, 90.0)
    legend = ["actual data", "median forecast"] + [f"{k}% forecast interval" for k in prediction_intervals][::-1]
    fig, ax = plt.subplots(1, 1, figsize=(11, 8))
    list(test_series)[0][-150:].plot(ax=ax)  # plot the time series
    list(forecasts)[0].plot(prediction_intervals=prediction_intervals, color='r')
    plt.grid(which="both")
    plt.legend(legend, loc="upper left")
    plt.savefig("deepar-model.png")


if __name__ == "__main__":

    # Example 1: build a simple Feed Forward model using an external dataset
    build_ff_model()

    # Example 2: build a DeepAR model using an in-build dataset
    build_deepar_model()