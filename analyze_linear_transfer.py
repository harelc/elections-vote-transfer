#### Written by Harel Cain, September 2019
#### Thanks to Itamar Mushkin for inspiration and a code piece

import cvxpy as cvx
import numpy as np
import plotly.graph_objects as go

import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
from scipy.optimize import nnls

DESTINATION_PARTY_COLORS = [
    'rgba(31, 119, 180, 0.4)',
    'rgba(255, 127, 14, 0.4)',
    'rgba(44, 160, 44, 0.4)',
    'rgba(214, 39, 40, 0.4)',
    'rgba(148, 103, 189, 0.4)',
    'rgba(140, 86, 75, 0.4)',
    'rgba(227, 119, 194, 0.4)',
    'rgba(205, 155, 105, 0.4)',
    'rgba(188, 189, 34, 0.4)',
    'rgba(23, 190, 207, 0.4)',
    'rgba(201, 201, 255, 0.4)',
    'rgba(255, 189, 189, 0.4)',
    'rgba(181, 234, 215, 0.4)',
#    'rgba(177, 117, 189, 0.4)',
    'rgba(50, 50 ,50 , 0.4)']

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
    df = df[parties]
    print(df.sum(axis=1).sum(axis=0))
    df = df.reindex(sorted(df.columns), axis=1)
    if include_no_vote:
        df['לא הצביע'] = eligible_voters - total_voters
    return df

def solve_transfer_coefficients(x_data, y_data, verbose):
    M = cvx.Variable((x_data.shape[1], y_data.shape[1]))
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
    before_labels = [x + '_24' for x in before_labels]
    after_labels = [x + '_25' for x in after_labels]
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


    fig.update_layout(title_text=f"""
Analysis of vote transfer between the elections for the 24th and the 25th Knessets.
<br>Based on analysis of {n_ballots} ballots whose serial number appeared in both. 
<br>Created by Harel Cain on {time.strftime('%d.%m.%Y %H%:%M')}. All rights reserved.
<br>Source code: https://github.com/harelc/elections-vote-transfer/
<br>
<br>""", title_font_size=16, font_size=14)
    fig.write_html("index.html")
    fig.show()


if __name__ == '__main__':
    method = "convex solver"
    ballot_previous = pd.read_csv('ballot23final.csv', encoding='iso8859_8')
    ballot_current = pd.read_csv('ballot24.csv', encoding='iso8859_8')
    parties_previous = 'פה מחל ודעם שס ל ג טב אמת'.split()
    parties_current = 'פה מחל ודעם שס ל ג ט אמת ב מרצ עם כן ת'.split()

    ballot_previous = adapt_df(ballot_previous, parties_previous, include_no_vote=True, ballot_number_field_name='קלפי')
    ballot_current = adapt_df(ballot_current, parties_current, include_no_vote=True, ballot_number_field_name='קלפי')

    u = pd.merge(ballot_previous, ballot_current, how='inner', left_index=True, right_index=True)

    print('Analyzing {} ballots common to both elections. Largest ballot has {} votes.'.format(
        len(u),
        u.sum(axis=1).max()
    ))
    values_previous = ballot_previous.loc[u.index].values
    values_current = ballot_current.loc[u.index].values

    if method == "closed form":
        #### method 1: closed-form solution with no non-negative constraint
        M = values_current.T @ values_previous @ np.linalg.pinv(values_previous.T @ values_previous)

    elif method == "nnls":
        ### method 2: non-negative least square solution
        M = np.zeros((values_current.shape[1], values_previous.shape[1]))
        for i in range(values_current.shape[1]):
            sol, r2 = nnls(values_previous, values_current[:, i])
            M[i,:] = sol
            pred = values_previous @ sol
            res = pred - values_current[:, i]
            # print MSE, MAE, sum of error
            # print(r2, np.mean(np.abs(res)), res.sum())

    elif method == "convex solver":
        ## method 3: use convex solver with constraints
        M = solve_transfer_coefficients(values_previous, values_current, verbose=True).T

    y_bar = values_current.mean(axis=0)
    ss_tot = ((values_current - y_bar) ** 2).sum()
    ss_res = ((values_current - values_previous @ M.T) ** 2).sum()
    print('R^2 is {:3.3f}'.format(1. - ss_res/ss_tot))
    print(M.sum(axis=0))
    print(M.sum(axis=1))

    vote_movements = M * ballot_previous.sum(axis=0).values
    print('Removing vote movements smaller than 5000')
    vote_movements[vote_movements < 5000] = 0.

    sankey(vote_movements, ballot_previous.columns.values, ballot_current.columns.values, n_ballots=len(u))


