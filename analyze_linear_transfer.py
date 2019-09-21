#### Written by Harel Cain, September 2019
#### Thanks to Itamar Mushkin for inspiration and a code piece

import cvxpy as cvx
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from scipy.optimize import nnls

DESTINATION_PARTY_COLORS = [
    'rgba(31, 119, 180, 0.4)',
    'rgba(255, 127, 14, 0.4)',
    'rgba(44, 160, 44, 0.4)',
    'rgba(214, 39, 40, 0.4)',
    'rgba(148, 103, 189, 0.4)',
    'rgba(140, 86, 75, 0.4)',
    'rgba(227, 119, 194, 0.4)',
    'rgba(127, 127, 127, 0.4)',
    'rgba(188, 189, 34, 0.4)',
    'rgba(23, 190, 207, 0.4)',
    'rgba(0, 0 ,0 ,0.4)']

def adapt_df(df, parties, include_no_vote=False, ballot_number_field_name=None):
    df['ballot_id'] = df['סמל ישוב'].astype(str) + '__' + df[ballot_number_field_name].astype(str)
    df = df.set_index('ballot_id')
    eligible_voters = df['בזב']
    total_voters = df['מצביעים']
    df = df[parties]
    df = df.reindex(sorted(df.columns), axis=1)
    if include_no_vote:
        df['לא הצביע'] = eligible_voters - total_voters
    return df

def solve_transfer_coefficients(x_data, y_data, verbose):
    M = cvx.Variable([x_data.shape[1], y_data.shape[1]])
    constraints = [0 <= M, M <= 1, cvx.sum(M, axis=1) == 1]
    objective = cvx.Minimize(cvx.norm((x_data @ M) - y_data, 'fro'))
    prob = cvx.Problem(objective, constraints)
    prob.solve(solver='SCS', verbose=True)
    M = M.value

    if verbose:
        print(M.min())  # should be close to 0
        print(M.max())  # should be close to 1
        print(M.sum(axis=1).min())  # should be close to 1
        print(M.sum(axis=1).max())  # should be close to 1
    return M

def sankey(vote_movements, before_labels, after_labels):
    source, target = np.meshgrid(np.arange(0, len(before_labels)),
                                 np.arange(len(before_labels), len(before_labels) + len(after_labels)))
    source = source.flatten()
    target = target.flatten()

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=12,
            thickness=8,
            label=list(before_labels) + list(after_labels),
            color=['gray'] * len(before_labels) + DESTINATION_PARTY_COLORS
        ),
        link=dict(
            source=source,  # indices correspond to labels, eg A1, A2, A2, B1, ...
            target=target,
            value=vote_movements.flatten(),
            color=[DESTINATION_PARTY_COLORS[x - len(before_labels)] for x in target],
        ))])

    fig.update_layout(title_text="""
    ניתוח נדידת הקולות בין מערכות הבחירות לכנסת ה-21 וה-22
    """,

                      font_size=16)
    fig.show()

if __name__ == '__main__':
    b21 = pd.read_csv('ballot21.csv', encoding='iso8859_8')
    b22 = pd.read_csv('ballot22.csv', encoding='iso8859_8')
    parties21 = 'מחל פה שס ג ום אמת ל טב מרצ כ דעם נ ז נר'.split()
    parties22 = 'פה מחל ודעם שס ל ג טב אמת מרצ כף'.split()

    b21 = adapt_df(b21, parties21, include_no_vote=False, ballot_number_field_name='מספר קלפי')
    b22 = adapt_df(b22, parties22, include_no_vote=False, ballot_number_field_name='קלפי')

    u = pd.merge(b21, b22, how='inner', left_index=True, right_index=True)
    v21 = b21.loc[u.index].values
    v22 = b22.loc[u.index].values

    # normalize each ballot - it helps with the regression, but can be removed
    # v21 = np.divide(v21, v21.sum(axis=1)[:, np.newaxis])
    # v22 = np.divide(v22, v22.sum(axis=1)[:, np.newaxis])

    #### method 1: closed-form solution with no non-negative constraint
    # M = v22.T @ v21 @ np.linalg.pinv(v21.T @ v21)

    ### method 2: non-negative least square solution
    # M = np.zeros((v22.shape[1], v21.shape[1]))
    # for i in range(v22.shape[1]):
    #     sol, r2 = nnls(v21, v22[:, i])
    #     M[i,:] = sol
    #     pred = v21 @ sol
    #     res = pred - v22[:, i]
    #     print(b22.columns[i])
    #     # print MSE, MAE, sum of error
    #     print(r2, np.mean(np.abs(res)), res.sum())sum

    ### method 3: use convex solver with constraints
    M = solve_transfer_coefficients(v21, v22, True).T

    wrongly_explained = np.sum(np.abs(b21.loc[u.index].values @ M.T - b22.loc[u.index].values))
    total_22 = b22.loc[u.index].values.sum()
    print('{:.4f}% of votes correctly explained'.format(100* (1. - (wrongly_explained / total_22))))

    print(M.sum(axis=0))
    print(M.sum(axis=1))

    M[M<0.01] = 0.

    vote_movements = M * b21.sum(axis=0).values
    sankey(vote_movements, b21.columns.values, b22.columns.values)


