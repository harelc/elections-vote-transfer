#### Written by Harel Cain, September 2019
#### Thanks to Itamar Mushkin for inspiration and a code piece

import cvxpy as cvx
import numpy as np
import plotly.graph_objects as go
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
from scipy.optimize import nnls
import streamlit as st


DESTINATION_PARTY_COLORS = [
    'rgba(31, 119, 180, 0.4)',
    'rgba(255, 127, 14, 0.4)',
    'rgba(44, 160, 44, 0.4)',
    'rgba(214, 39, 40, 0.4)',
    'rgba(148, 103, 189, 0.4)',
    'rgba(140, 86, 75, 0.4)',
    'rgba(227, 119, 194, 0.4)',
    'rgba(255, 235, 135, 0.4)',
    'rgba(188, 189, 34, 0.4)',
    'rgba(23, 190, 207, 0.4)',
    'rgba(201, 201, 255, 0.4)',
    'rgba(255, 189, 189, 0.4)',
    'rgba(181, 234, 215, 0.4)',
    'rgba(0, 0 ,0 , 0.4)']

def adapt_df(df, parties, include_no_vote=False, ballot_number_field_name=None):
    print(f'{len(df)} ballots analyzed')
    df = df[df['סמל ישוב'] != 9999]
    print(f'{len(df)} ballots after throwing out 9999')

    df['ballot_id'] = df['סמל ישוב'].astype(str) + '__' + \
                      df[ballot_number_field_name].astype(str).copy()
    # df['ballot_id_sup'] = df['סמל ישוב'].astype(str) + '__' + \
    #                   df[ballot_number_field_name].astype(str).apply(lambda x: '.'.join(x.split('.')[:-1])).copy()
    df = df.set_index('ballot_id')
    eligible_voters = df['בזב']
    total_voters = df['מצביעים']
    df = df[parties][total_voters<750]
    print(df.sum(axis=1).sum(axis=0))
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

def sankey(vote_movements, before_labels, after_labels, n_ballots):
    import time
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
Vote transfer analysis between elections for the 23rd and 24th Knesset<br>Based on {} voting stations with same serial number that appeared in both<br>Created by Harel Cain on {}
    """.format(n_ballots, time.strftime('%d.%m.%Y %H%:%M'), title_font_size=13, font_size=14))
    fig.show()

if __name__ == '__main__':
    b21 = pd.read_csv('ballot23final.csv', encoding='iso8859_8')
    b22 = pd.read_csv('ballot24.csv', encoding='iso8859_8')
    parties21 = 'פה מחל ודעם שס ל ג טב אמת'.split()
    parties22 = 'פה מחל ודעם שס ל ג ט אמת ב מרצ עם כן ת'.split()

    b21 = adapt_df(b21, parties21, include_no_vote=True, ballot_number_field_name= 'קלפי')
    b22 = adapt_df(b22, parties22, include_no_vote=True, ballot_number_field_name='קלפי')

    u = pd.merge(b21, b22, how='inner', left_index=True, right_index=True)

    print('Analyzing {} ballots common to both elections. Largest ballot has {} votes.'.format(
        len(u),
        u.sum(axis=1).max()
    ))
    v21 = b21.loc[u.index].values
    v22 = b22.loc[u.index].values
    print(v21[:,:-1].sum(), v22[:,:-1].sum())

    # normalize each ballot - it helps with the regression, but can be removed
    # v21 = np.divide(v21, v21.sum(axis=1)[:, np.newaxis])
    # v22 = np.divide(v22, v22.sum(axis=1)[:, np.newaxis])

    #### method 1: closed-form solution with no non-negative constraint
    #M = v22.T @ v21 @ np.linalg.pinv(v21.T @ v21)

    ### method 2: non-negative least square solution
    # M = np.zeros((v22.shape[1], v21.shape[1]))
    # for i in range(v22.shape[1]):
    #     sol, r2 = nnls(v21, v22[:, i])
    #     M[i,:] = sol
    #     pred = v21 @ sol
    #     res = pred - v22[:, i]
    #     print(b22.columns[i])
    #     # print MSE, MAE, sum of error
    #     print(r2, np.mean(np.abs(res)), res.sum())

    ### method 3: use convex solver with constraints
    M = solve_transfer_coefficients(v21, v22, True).T

    wrongly_explained = np.abs(b21.loc[u.index].values @ M.T - b22.loc[u.index].values)
    l2_error = np.linalg.norm(b21.loc[u.index].values @ M.T - b22.loc[u.index].values, axis=1)
    most_suspicious = np.argsort(-l2_error)[:50]
    #print(l2_error[most_suspicious])

    total_22 = b22.loc[u.index].values.sum()

    print('{:.4f}% of votes correctly explained'.format(100 * (1. - (wrongly_explained.sum() / total_22))))
    print(M.sum(axis=0))
    print(M.sum(axis=1))

    #wedf = pd.DataFrame(wrongly_explained.sum(axis=0), index=b22.columns.values)
    #print(wedf)

    vote_movements = M * b21.sum(axis=0).values
    vote_movements[vote_movements < 5000] = 0.

    sankey(vote_movements, b21.columns.values, b22.columns.values, n_ballots=len(u))
    Mdf = pd.DataFrame(M.T, index=b21.columns.values, columns=b22.columns.values)


