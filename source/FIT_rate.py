"""
Code to load in the FIT payment data as an excel file and collate information
relating to photovoltaics into one place.

- First authored: 2020-01-20
- Owen Huxley <othuxley1@sheffield.ac.uk>
"""

import pandas as pd
import numpy as np
import seaborn as sns; sns.set()
import matplotlib.pyplot as plt

class FITExcelFile:
    """A class to extract information on the decline of the FIT rate."""

    def __init__(self, plot=False, verbose=False):
        self.FIT_excel_file = "../data/2019_rpi_adjusted_tariff_table_publication.xlsx"
        self.xlsx = pd.ExcelFile(self.FIT_excel_file)
        self.plot = plot
        self.verbose = verbose
        self.sheet_dfs = None
        self.data = []
        self.data_group_install_capacity = []
        self.data_group_date = None

    def run(self):
        self.load_excel_data()
        self.collate_data()

    def load_excel_data(self):
        dfs = []
        sheets = self.xlsx.sheet_names
        for sheet in sheets[2:11]:
            pv_fit_df = self.load_excel_sheet(sheet)
            pv_fit_df["Sheet Name"] = sheet
            dfs.append(pv_fit_df)
            if self.plot: self.plot_heat_map(pv_fit_df, sheet)
        self.sheet_dfs = dfs
        return dfs

    def load_excel_sheet(self, sheet):
        column_types = {
            "Solar PV Installation  Type" : str,
            "Maximum Capacity (kW)" : np.float32,
            "Tariff" : np.float32,
            "Technology Type" : str,
        }
        date_cols = [-1, -2]
        df = pd.read_excel(self.xlsx, sheet, dtype=column_types, parse_dates=date_cols)
        pv =  df.loc[df["Technology Type"] == "Photovoltaic"]
        pv = pv[["Solar PV Installation  Type",
                 "Maximum Capacity (kW)", "Tariff",
                 "Technology Type", "Tariff Start Date",
                 "Tariff End Date"]]

        pv = pv[~pv["Tariff"].isnull().values]
        return pv

    def plot_heat_map(self, df, sheet):
        grouped = df.groupby(["Solar PV Installation  Type",
                              "Maximum Capacity (kW)"]).max()[["Tariff"]]
        piv_grouped = grouped.unstack()
        piv_grouped["Tariff"]
        f, ax = plt.subplots(figsize=(9, 6))
        ax = sns.heatmap(piv_grouped["Tariff"], vmin=0, vmax=45, annot=True, fmt=".1f", linewidths=.5, square=False,linecolor="white", ax=ax)

        # fix for bug in matplotlib that cuts off top and bottom of axis
        bottom, top = ax.get_ylim()
        ax.set_ylim(bottom + 0.5, top - 0.5)
        ax.set_title(sheet)
        #===============================================================

    def collate_data(self):

        for df in self.sheet_dfs:
            df["Tariff Start Date"] = df["Tariff Start Date"].dt.strftime("%Y-%m-%d")
            df["Tariff End Date"] = df["Tariff End Date"].dt.strftime("%Y-%m-%d")
            if df["Tariff End Date"].isnull().sum() >0:
                raise


            grouped = df.groupby(["Solar PV Installation  Type",
                                  "Maximum Capacity (kW)"]).max()

            data_max = [[i, j, *v] for (i,j), v in zip(grouped.index,
                                                       grouped.values)]
            self.data_group_install_capacity += data_max


            data_full = df.values.tolist()
            self.data += data_full

        column_headers = df.columns.values.tolist()

        def list_to_df(data, header):
            df = pd.DataFrame(data, columns=header)
            df["Tariff Start Date"] = pd.to_datetime(df["Tariff Start Date"])
            df["Tariff End Date"] = pd.to_datetime(df["Tariff End Date"])
            return df

        self.data_group_install_capacity = list_to_df(self.data_group_install_capacity, column_headers)
        self.data = list_to_df(self.data, column_headers)

        self.data_group_date = self.data.groupby(["Tariff End Date"]).mean()

    def plot_graphs(self):
        df = self.data_group_install_capacity
        f = sns.FacetGrid(df, col="Solar PV Installation  Type", hue="Maximum Capacity (kW)", height=5, aspect=1, col_wrap=2)
        f.map(plt.step, "Tariff End Date", "Tariff")
        f.add_legend()
        f.savefig("../graphs/grid_lineplot.png", dpi=300)
        plt.show()

        df = self.data_group_date
        df.reset_index(inplace=True)
        g = plt.figure()
        sns.lineplot(x="Tariff End Date", y="Tariff", data=df, drawstyle='steps-pre')
        g.savefig("../graphs/mean_lineplot.png", dpi=300)
        plt.show()

    def save_data(self):
        self.data.to_csv("../data/FIT_payment_rate.csv")
        self.data_group_date.to_csv("../data/FIT_payment_rate_group_by_date.csv")
        self.data_group_install_capacity.to_csv("../data/FIT_payment_rate_group_by_installation_and_capacity.csv")

class FITRate:
    """A class to calculate the FIT rate on a given date."""

    def __init__(self):
        self.fit_rate_file = "../data/FIT_payment_rate_group_by_date.csv"
        self.data = pd.read_csv(self.fit_rate_file)
        self.data["Tariff End Date"] = pd.to_datetime(self.data["Tariff End Date"])
        self.max_fit = self.data.Tariff.max()
        self.min_fit = self.data.Tariff.min()

    def get_fit_rate(self, _date):
        if self.data[self.data["Tariff End Date"] >= _date].empty:
            return 0
        else:
            return self.data[self.data["Tariff End Date"] >= _date].iloc[0, -1]

if __name__ == "__main__":
    fit_excel_file_instance = FITExcelFile(plot=False, verbose=False)
    fit_excel_file_instance.run()
    fit_excel_file_instance.plot_graphs()
    fit_excel_file_instance.save_data()


    fit_rate_instance = FITRate()
    data = fit_rate_instance.data