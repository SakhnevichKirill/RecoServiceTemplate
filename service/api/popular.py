import pandas as pd


def get_df(path: str):
    return pd.read_csv(path, parse_dates=["last_watch_dt"])


class PopularRecommender:
    def __init__(self, max_K: int = 10, days: int = 30, item_column: str = "item_id", dt_column: str = "date"):
        self.max_K = max_K
        self.days = days
        self.item_column = item_column
        self.dt_column = dt_column
        self.recommendations: list = []

    def fit(
        self,
        df: pd.DataFrame,
    ):
        min_date = df[self.dt_column].max().normalize() - pd.DateOffset(days=self.days)
        self.recommendations = (
            df.loc[df[self.dt_column] > min_date, self.item_column].value_counts().head(self.max_K).index.values
        )

    def recommend(self, N: int = 10):
        recs = self.recommendations[:N]
        return recs
