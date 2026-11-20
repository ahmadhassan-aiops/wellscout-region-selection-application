# WellScout: oil region selection application

**Live app:** [wellscout-region-selection-application.streamlit.app](https://wellscout-region-selection-application.streamlit.app/) · **Notebook and project folder:** [AIOPS-Portfolio-Projects](https://github.com/ahmadhassan-aiops/AIOPS-Portfolio-Projects/tree/main/2.%20Machine%20Learning%20Projects/optimal%20oil%20well%20location%20selection%20using%20ML)

Which region should OilyGiant develop? WellScout, by **Ahmad Hassan** (AI Engineer), answers the brief: in the chosen
region 500 points are surveyed, a model ranks them, the best 200 become wells on a $100 million budget, and only
regions with a **risk of a loss under 2.5%** qualify; among them the highest mean profit wins. Profit and risk come from
**10,000 simulated surveys** of points the models never trained on, and the answer depends on the model:

| Model | Region chosen | Mean profit | Risk of a loss |
|---|---|---|---|
| Linear regression (the brief) | 1 | $4.8 million | 0.9% |
| Linear regression with squared terms | 2 | $5.3 million | 2.3% |
| LightGBM | 2 | $6.6 million | 0.8% |

Region 1's reserves take 12 values that follow one feature almost exactly, so every model ranks its points nearly
perfectly. Region 2's reserves grow with the square of `f0` and `f1`; a straight-line model cannot see that bowl,
squared terms (still a linear regression) can, and gradient-boosted trees see it best.

- **Decision**: choose the model and the economics (budget, wells, points surveyed, price, risk limit); the decision,
  each region's mean profit, 95% range and risk, the profit distributions, and all three models side by side.
- **Survey**: one survey of 500 points up close: what the model predicted against what each point holds, the 200
  developed, the ledger, and the result against perfect hindsight and a random choice.
- **Site check**: enter a point's three measurements (or load a held-out point); each model's prediction against
  break-even and the cut-off for the best 200 of a typical survey.
- **Regions**: the data, region 1's twelve steps, region 2's bowl.
- **Method**: accuracy of every model in every region, the decision table, data, economics and limits.

## The model

The project notebook was audited and rebuilt before the app. The first version's conclusion mislabelled the regions
and recommended "region 2" for profit while the brief's rule selected region 1; its bootstrap was unseeded and used
1,000 draws; and it missed 18 point ids measured twice with different values. Details are in the notebook.

| RMSE (thousand barrels), validation points | Region 0 | Region 1 | Region 2 |
|---|---|---|---|
| Linear regression | 37.76 | 0.89 | 40.13 |
| Linear regression with squared terms | 37.76 | 0.89 | 38.93 |
| LightGBM (300 trees) | 37.19 | 1.58 | 37.78 |

## Why this stack

| Need | Choice |
|---|---|
| The brief's model and an honest check beyond it | **scikit-learn** linear regression, the same with polynomial terms, and **LightGBM** |
| Profit and risk of a 500-point survey | A vectorised **bootstrap**, 10,000 surveys with a fixed seed, the same surveys for every model |
| Valid inputs | **pydantic**: economics (wells within points surveyed, positive budget and price) and site measurements |
| Trust that the shipped files are the evaluated models | **pytest** + GitHub Actions: saved predictions and RMSE, the bootstrap and the choice per model, the profit rule, every page |

`wellscout/` has no Streamlit dependency, so the same economics and models can sit behind an API.

## Run it

```
pip install -r requirements.txt
python train.py        # optional: rebuilds model/ and data/validation.parquet (about 30 s)
streamlit run app.py
pip install -r requirements-dev.txt && pytest
```

Data: synthetic exploration data, 100,000 points in each of three regions (OilyGiant training case). WellScout is a
portfolio demonstration, not investment advice.
