import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, html, dcc, Input, Output, callback_context
import os, traceback

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "IPL Analytics Pro"

GOLD   = "#F5A623"
TEAL   = "#00D4AA"
PURPLE = "#8B5CF6"
RED    = "#FF4757"
BG     = "#0A0E1A"
CARD   = "#111827"
CARD2  = "#1A2235"
BORDER = "#1E2D45"
TEXT   = "#E8EDF5"
MUTED  = "#6B7A99"

def CL(extra=None):
    """Base chart layout — no axis/legend keys, add per-chart as needed."""
    d = dict(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans, sans-serif', color=TEXT, size=12),
        margin=dict(t=44, b=30, l=10, r=10),
        height=340,
        hoverlabel=dict(bgcolor=CARD2, bordercolor=BORDER, font_color=TEXT),
        legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor=BORDER, font_color=TEXT),
        xaxis=dict(gridcolor=BORDER, linecolor=BORDER, tickcolor=BORDER, color=MUTED),
        yaxis=dict(gridcolor=BORDER, linecolor=BORDER, tickcolor=BORDER, color=MUTED),
    )
    if extra:
        d.update(extra)
    return d

def nav_item(id_, label, icon, active=False):
    return html.Div([
        html.Span(icon, style={'fontSize':'18px','marginRight':'10px'}),
        html.Span(label, style={'fontSize':'13px','fontWeight':'500'})
    ], id=id_, n_clicks=0, style={
        'display':'flex','alignItems':'center','padding':'11px 20px',
        'cursor':'pointer','borderRadius':'8px',
        'color': TEXT if active else MUTED,
        'background': f'linear-gradient(90deg,{GOLD}22,transparent)' if active else 'transparent',
        'borderLeft': f'3px solid {GOLD}' if active else '3px solid transparent',
        'transition':'all .2s','marginBottom':'4px'
    })

def kpi_card(label, value, sub, color=GOLD):
    return html.Div([
        html.Div(str(value), style={
            'fontSize':'30px','fontWeight':'700','color':color,
            'letterSpacing':'-1px','margin':'4px 0','fontFamily':'DM Mono,monospace'
        }),
        html.Div(label, style={'fontSize':'12px','color':TEXT,'fontWeight':'500'}),
        html.Div(sub,   style={'fontSize':'11px','color':MUTED,'marginTop':'2px'}),
    ], style={
        'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px',
        'padding':'18px 20px','flex':'1','minWidth':'150px',
        'borderTop':f'2px solid {color}',
    })

def chart_card(child, flex=1):
    return html.Div(child, style={
        'flex':str(flex),'background':CARD,'border':f'1px solid {BORDER}',
        'borderRadius':'12px','overflow':'hidden','minWidth':'280px'
    })

def row(children):
    return html.Div(children, style={'display':'flex','gap':'16px','flexWrap':'wrap'})

def cfg():
    return {'displayModeBar':True,
            'modeBarButtonsToRemove':['lasso2d','select2d'],
            'displaylogo':False}

app.layout = html.Div([
    html.Link(rel='stylesheet',
        href='https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&family=Bebas+Neue&display=swap'),
    html.Div([
        # Sidebar
        html.Div([
            html.Div([
                html.Div("IPL", style={'fontFamily':'Bebas Neue,sans-serif','fontSize':'32px','color':GOLD,'letterSpacing':'3px'}),
                html.Div("ANALYTICS PRO", style={'fontSize':'8px','color':MUTED,'letterSpacing':'3px','fontWeight':'600'}),
            ], style={'padding':'24px 20px 28px'}),
            html.Div([
                html.Div("SEASON", style={'fontSize':'9px','color':MUTED,'letterSpacing':'2px','fontWeight':'600','marginBottom':'6px','padding':'0 20px'}),
                html.Div(dcc.Dropdown(
                    id='season-filter',
                    options=[{'label':'All Seasons','value':'all'}]+[{'label':str(s),'value':s} for s in range(2008,2021)],
                    value='all', clearable=False,
                    style={'background':CARD2,'color':TEXT}
                ), style={'padding':'0 12px','marginBottom':'24px'}),
            ]),
            html.Div("NAVIGATION", style={'fontSize':'9px','color':MUTED,'letterSpacing':'2px','fontWeight':'600','padding':'0 20px','marginBottom':'8px'}),
            nav_item('nav-overview','Overview','⬡',active=True),
            nav_item('nav-teams',   'Team Analysis','🏏'),
            nav_item('nav-players', 'Player Stats','👤'),
            nav_item('nav-phases',  'Match Phases','📊'),
            html.Div([
                html.Div("816 matches · 13 seasons", style={'fontSize':'11px','color':MUTED,'textAlign':'center'}),
                html.Div("2008 – 2020", style={'fontSize':'10px','color':MUTED,'opacity':'.5','textAlign':'center','marginTop':'2px'}),
            ], style={'position':'absolute','bottom':'24px','width':'100%'}),
        ], style={'width':'220px','minHeight':'100vh','background':CARD,
                  'borderRight':f'1px solid {BORDER}','position':'relative','flexShrink':'0'}),
        # Main
        html.Div([
            html.Div([
                html.Div(id='page-title'),
                html.Div([
                    html.Div(style={'width':'8px','height':'8px','borderRadius':'50%','background':TEAL,'marginRight':'8px'}),
                    html.Span("Data loaded", style={'fontSize':'12px','color':TEAL})
                ], style={'display':'flex','alignItems':'center'})
            ], style={'display':'flex','justifyContent':'space-between','alignItems':'flex-start',
                      'padding':'24px 32px 20px','borderBottom':f'1px solid {BORDER}'}),
            html.Div(id='page-content', style={'padding':'24px 32px','overflowY':'auto'}),
        ], style={'flex':'1','overflowY':'auto'}),
    ], style={'display':'flex','minHeight':'100vh','background':BG,'fontFamily':'DM Sans,sans-serif'}),
], style={'background':BG,'minHeight':'100vh'})


@app.callback(
    Output('page-content','children'),
    Output('page-title','children'),
    Input('season-filter','value'),
    Input('nav-overview','n_clicks'),
    Input('nav-teams','n_clicks'),
    Input('nav-players','n_clicks'),
    Input('nav-phases','n_clicks'),
)
def route(season, *_):
    try:
        ctx = callback_context
        page = 'overview'
        if ctx.triggered:
            tid = ctx.triggered[0]['prop_id'].split('.')[0]
            if   'nav-teams'   in tid: page = 'teams'
            elif 'nav-players' in tid: page = 'players'
            elif 'nav-phases'  in tid: page = 'phases'

        titles = {
            'overview':('Overview','Season at a glance'),
            'teams':   ('Team Analysis','Head-to-head & win rates'),
            'players': ('Player Stats','Batsmen & bowlers'),
            'phases':  ('Match Phases','Powerplay · Middle · Death'),
        }
        t, s = titles[page]
        title_el = [
            html.Div(t, style={'fontFamily':'Bebas Neue','fontSize':'28px','color':TEXT,'letterSpacing':'2px'}),
            html.Div(s, style={'fontSize':'12px','color':MUTED})
        ]
        m = _M.copy() if season=='all' else _M[_M['season']==season].copy()
        d = _D.copy() if season=='all' else _D[_D['season']==season].copy()

        pages = {'overview':overview_page,'teams':teams_page,'players':players_page,'phases':phases_page}
        return pages[page](m,d), title_el

    except Exception:
        err = traceback.format_exc()
        print('ROUTE ERROR:\n', err)
        ec = html.Div([
            html.Div('Callback Error',style={'color':RED,'fontSize':'18px','fontWeight':'700','marginBottom':'12px'}),
            html.Pre(err,style={'color':MUTED,'fontSize':'11px','background':CARD2,'padding':'16px',
                                'borderRadius':'8px','whiteSpace':'pre-wrap','border':f'1px solid {BORDER}'})
        ], style={'padding':'24px'})
        return ec, [html.Div('Error',style={'color':RED,'fontFamily':'Bebas Neue','fontSize':'28px'})]


# ── Overview ────────────────────────────────────────────────────────────────
def overview_page(m, d):
    sixes = int((d['batsman_runs']==6).sum())
    avg   = round(d['total_runs'].sum()/max(len(m),1), 1)

    kpis = html.Div([
        kpi_card("Total Matches",   f"{len(m):,}",  "IPL 2008–2020", GOLD),
        kpi_card("Total Deliveries",f"{len(d):,}",  "Ball by ball",  TEAL),
        kpi_card("Total Sixes",     f"{sixes:,}",   "All seasons",   PURPLE),
        kpi_card("Avg Runs/Match",  f"{avg}",        "Both innings",  RED),
    ], style={'display':'flex','gap':'16px','marginBottom':'24px','flexWrap':'wrap'})

    # Season trend
    st = d.groupby('season')['total_runs'].sum().reset_index()
    mc = m.groupby('season').size().reset_index(name='cnt')
    st = st.merge(mc, on='season')
    st['avg'] = (st['total_runs']/st['cnt']).round(1)

    fig_trend = make_subplots(specs=[[{"secondary_y":True}]])
    fig_trend.add_trace(go.Bar(
        x=st['season'].tolist(), y=st['total_runs'].tolist(),
        name='Total Runs', marker_color=TEAL, opacity=0.75,
        hovertemplate='<b>%{x}</b><br>Runs: %{y:,}<extra></extra>'
    ), secondary_y=False)
    fig_trend.add_trace(go.Scatter(
        x=st['season'].tolist(), y=st['avg'].tolist(),
        name='Avg/Match', mode='lines+markers',
        line=dict(color=GOLD,width=2.5), marker=dict(size=8,color=GOLD),
        hovertemplate='<b>%{x}</b><br>Avg: %{y}<extra></extra>'
    ), secondary_y=True)
    fig_trend.update_layout(
        title='Scoring Trends by Season',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans,sans-serif',color=TEXT,size=12),
        margin=dict(t=44,b=30,l=10,r=10), height=340,
        legend=dict(bgcolor='rgba(0,0,0,0)',orientation='h',y=1.1,x=0),
        xaxis=dict(gridcolor=BORDER,linecolor=BORDER,tickcolor=BORDER,color=MUTED),
    )
    fig_trend.update_yaxes(gridcolor=BORDER, color=MUTED, secondary_y=False)
    fig_trend.update_yaxes(gridcolor='rgba(0,0,0,0)', color=GOLD, secondary_y=True)

    # Toss donut
    m2 = m.copy()
    m2['twm'] = m2['toss_winner']==m2['winner']
    won  = int(m2['twm'].sum())
    lost = len(m2)-won
    pct  = round(won/max(len(m2),1)*100)
    fig_toss = go.Figure(go.Pie(
        labels=['Toss winner won','Toss winner lost'],
        values=[won,lost], hole=0.65,
        marker_colors=[GOLD,CARD2],
        hovertemplate='%{label}<br>%{value} matches (%{percent})<extra></extra>'
    ))
    fig_toss.update_layout(
        title='Toss → Match Win',
        annotations=[dict(text=f'{pct}%',font_size=22,showarrow=False,font_color=GOLD)],
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans,sans-serif',color=TEXT,size=12),
        margin=dict(t=44,b=30,l=10,r=10), height=340,
        legend=dict(bgcolor='rgba(0,0,0,0)',orientation='h',y=-0.1),
        showlegend=True,
    )

    # Field vs bat
    by_dec = m2.groupby('toss_decision')['twm'].mean().reset_index()
    by_dec['win_pct'] = (by_dec['twm']*100).round(1)
    fig_dec = go.Figure(go.Bar(
        x=by_dec['toss_decision'].tolist(),
        y=by_dec['win_pct'].tolist(),
        marker_color=[TEAL,PURPLE],
        text=by_dec['win_pct'].apply(lambda x:f'{x}%').tolist(),
        textposition='outside',
        textfont=dict(color=TEXT,size=14,family='DM Mono'),
        hovertemplate='<b>%{x}</b><br>Win rate: %{y:.1f}%<extra></extra>'
    ))
    fig_dec.update_layout(
        title='Win Rate by Decision',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans,sans-serif',color=TEXT,size=12),
        margin=dict(t=44,b=30,l=10,r=10), height=340,
        yaxis=dict(range=[0,75],gridcolor=BORDER,color=MUTED),
        xaxis=dict(gridcolor=BORDER,color=MUTED),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
    )

    return html.Div([
        kpis,
        row([chart_card(dcc.Graph(figure=fig_trend,config=cfg()),flex=2)]),
        html.Div(style={'height':'16px'}),
        row([chart_card(dcc.Graph(figure=fig_toss,config=cfg())),
             chart_card(dcc.Graph(figure=fig_dec, config=cfg()))]),
    ])


# ── Teams ────────────────────────────────────────────────────────────────────
def teams_page(m, d):
    played = pd.concat([m['team1'],m['team2']]).value_counts().reset_index()
    played.columns=['team','played']
    wins = m['winner'].value_counts().reset_index()
    wins.columns=['team','wins']
    ts = played.merge(wins,on='team')
    ts['win_pct']  = (ts['wins']/ts['played']*100).round(1)
    ts['loss_pct'] = (100-ts['win_pct']).round(1)
    ts = ts.sort_values('win_pct',ascending=True)

    fig_win = go.Figure()
    fig_win.add_trace(go.Bar(y=ts['team'].tolist(),x=ts['win_pct'].tolist(),
        name='Win %',orientation='h',marker_color=GOLD,
        text=ts['win_pct'].apply(lambda x:f'{x}%').tolist(),
        textposition='outside',textfont=dict(color=GOLD,size=11),
        hovertemplate='<b>%{y}</b><br>Win: %{x:.1f}%<extra></extra>'))
    fig_win.add_trace(go.Bar(y=ts['team'].tolist(),x=ts['loss_pct'].tolist(),
        name='Loss %',orientation='h',marker_color=CARD2,
        hovertemplate='<b>%{y}</b><br>Loss: %{x:.1f}%<extra></extra>'))
    fig_win.update_layout(
        title='Win vs Loss % by Team', barmode='stack',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans,sans-serif',color=TEXT,size=12),
        margin=dict(t=44,b=30,l=10,r=10), height=480,
        xaxis=dict(range=[0,115],gridcolor=BORDER,color=MUTED),
        yaxis=dict(gridcolor=BORDER,color=MUTED),
        legend=dict(bgcolor='rgba(0,0,0,0)',orientation='h',y=1.05),
    )

    venue = m.groupby('venue').size().reset_index(name='matches')
    venue = venue.sort_values('matches',ascending=False).head(10)
    fig_venue = go.Figure(go.Bar(
        x=venue['matches'].tolist(), y=venue['venue'].tolist(),
        orientation='h', marker_color=TEAL, opacity=0.8,
        hovertemplate='<b>%{y}</b><br>Matches: %{x}<extra></extra>'
    ))
    fig_venue.update_layout(
        title='Top 10 Venues by Matches',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans,sans-serif',color=TEXT,size=12),
        margin=dict(t=44,b=30,l=10,r=10), height=380,
        xaxis=dict(gridcolor=BORDER,color=MUTED),
        yaxis=dict(gridcolor=BORDER,color=MUTED),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
    )

    m2 = m.copy()
    m2['twm'] = m2['toss_winner']==m2['winner']
    tt = m2.groupby('toss_winner').agg(tw=('twm','sum'),tot=('twm','count')).reset_index()
    tt['rate'] = (tt['tw']/tt['tot']*100).round(1)
    tt = tt.sort_values('rate',ascending=False).head(10)
    fig_tt = go.Figure(go.Bar(
        x=tt['toss_winner'].tolist(), y=tt['rate'].tolist(),
        marker_color=PURPLE, opacity=0.85,
        text=tt['rate'].apply(lambda x:f'{x}%').tolist(), textposition='outside',
        hovertemplate='<b>%{x}</b><br>Rate: %{y:.1f}%<extra></extra>'
    ))
    fig_tt.update_layout(
        title='Toss→Win Rate by Team (top 10)',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans,sans-serif',color=TEXT,size=12),
        margin=dict(t=44,b=30,l=10,r=10), height=380,
        yaxis=dict(range=[0,85],gridcolor=BORDER,color=MUTED),
        xaxis=dict(gridcolor=BORDER,color=MUTED,tickangle=-30),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
    )

    return html.Div([
        row([chart_card(dcc.Graph(figure=fig_win,config=cfg()),flex=1)]),
        html.Div(style={'height':'16px'}),
        row([chart_card(dcc.Graph(figure=fig_venue,config=cfg())),
             chart_card(dcc.Graph(figure=fig_tt,  config=cfg()))]),
    ])


# ── Players ──────────────────────────────────────────────────────────────────
def players_page(m, d):
    bat = d.groupby('batsman').agg(
        runs=('batsman_runs','sum'), balls=('ball','count'),
        fours=('batsman_runs',lambda x:(x==4).sum()),
        sixes=('batsman_runs',lambda x:(x==6).sum()),
    ).reset_index()
    bat['sr'] = (bat['runs']/bat['balls'].replace(0,1)*100).round(1)
    top_bat = bat.sort_values('runs',ascending=False).head(15)

    fig_bat = go.Figure(go.Bar(
        y=top_bat['batsman'][::-1].tolist(),
        x=top_bat['runs'][::-1].tolist(),
        orientation='h', marker_color=GOLD, opacity=0.85,
        text=top_bat['runs'][::-1].tolist(),
        textposition='outside', textfont=dict(color=MUTED,size=10),
        customdata=top_bat['sr'][::-1].tolist(),
        hovertemplate='<b>%{y}</b><br>Runs: %{x:,}<br>SR: %{customdata}<extra></extra>'
    ))
    fig_bat.update_layout(
        title='Top 15 Run Scorers',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans,sans-serif',color=TEXT,size=12),
        margin=dict(t=44,b=30,l=10,r=10), height=460,
        xaxis=dict(range=[0,top_bat['runs'].max()+600],gridcolor=BORDER,color=MUTED),
        yaxis=dict(gridcolor=BORDER,color=MUTED),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
    )

    bowl = d.groupby('bowler').agg(
        runs=('total_runs','sum'), balls=('ball','count'),
        wkts=('is_wicket','sum')
    ).reset_index()
    bowl['overs']   = bowl['balls']/6
    bowl['economy'] = (bowl['runs']/bowl['overs'].replace(0,1)).round(2)
    qual = bowl[bowl['overs']>=50].sort_values('economy').head(12)
    avg_eco = bowl[bowl['overs']>=50]['economy'].mean()
    cbowl = [TEAL if e<avg_eco else f'{TEAL}66' for e in qual['economy']]

    fig_bowl = go.Figure(go.Bar(
        y=qual['bowler'][::-1].tolist(), x=qual['economy'][::-1].tolist(),
        orientation='h', marker_color=cbowl[::-1],
        text=qual['economy'][::-1].tolist(), textposition='outside',
        textfont=dict(color=MUTED,size=10),
        hovertemplate='<b>%{y}</b><br>Economy: %{x}<extra></extra>'
    ))
    fig_bowl.add_vline(x=avg_eco,line_dash='dash',line_color=RED,
        annotation_text=f'Avg {avg_eco:.2f}',annotation_font_color=RED)
    fig_bowl.update_layout(
        title='Most Economic Bowlers (min 50 overs)',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans,sans-serif',color=TEXT,size=12),
        margin=dict(t=44,b=30,l=10,r=10), height=420,
        xaxis=dict(range=[0,10],gridcolor=BORDER,color=MUTED),
        yaxis=dict(gridcolor=BORDER,color=MUTED),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
    )

    top_sc = bat[bat['balls']>=200].sort_values('runs',ascending=False).head(30).copy()
    top_sc['sixes_plot'] = top_sc['sixes'].add(1)
    fig_sr = px.scatter(top_sc, x='runs', y='sr', size='sixes_plot',
        hover_name='batsman', color='sr',
        color_continuous_scale=[[0,PURPLE],[0.5,TEAL],[1,GOLD]],
        title='Runs vs Strike Rate (bubble=sixes, min 200 balls)',
        labels={'runs':'Total Runs','sr':'Strike Rate'})
    fig_sr.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans,sans-serif',color=TEXT,size=12),
        margin=dict(t=44,b=30,l=10,r=10), height=380,
        xaxis=dict(gridcolor=BORDER,color=MUTED),
        yaxis=dict(gridcolor=BORDER,color=MUTED),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
    )
    fig_sr.update_coloraxes(showscale=False)

    return html.Div([
        row([chart_card(dcc.Graph(figure=fig_bat, config=cfg())),
             chart_card(dcc.Graph(figure=fig_bowl,config=cfg()))]),
        html.Div(style={'height':'16px'}),
        row([chart_card(dcc.Graph(figure=fig_sr,config=cfg()),flex=1)]),
    ])


# ── Phases ───────────────────────────────────────────────────────────────────
def phases_page(m, d):
    def ph(o):
        if o<=5:    return 'Powerplay'
        elif o<=14: return 'Middle'
        else:       return 'Death'
    d2 = d.copy()
    d2['phase'] = d2['over'].apply(ph)
    agg = d2.groupby('phase').agg(
        runs=('total_runs','sum'), balls=('ball','count'),
        wkts=('is_wicket','sum'),
        fours=('batsman_runs',lambda x:(x==4).sum()),
        sixes=('batsman_runs',lambda x:(x==6).sum()),
    ).reset_index()
    agg['rr']  = (agg['runs']/agg['balls']*6).round(2)
    agg['wpo'] = (agg['wkts']/agg['balls']*6).round(3)
    agg = agg.set_index('phase').loc[['Powerplay','Middle','Death']].reset_index()
    pc = [TEAL, PURPLE, RED]

    fig_rr = go.Figure(go.Bar(
        x=agg['phase'].tolist(), y=agg['rr'].tolist(), marker_color=pc,
        text=agg['rr'].tolist(), textposition='outside',
        textfont=dict(size=15,family='DM Mono',color=TEXT),
        hovertemplate='<b>%{x}</b><br>Run rate: %{y}<extra></extra>'
    ))
    fig_rr.update_layout(
        title='Run Rate by Phase',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans,sans-serif',color=TEXT,size=12),
        margin=dict(t=44,b=30,l=10,r=10), height=340,
        yaxis=dict(range=[0,13],gridcolor=BORDER,color=MUTED),
        xaxis=dict(gridcolor=BORDER,color=MUTED),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
    )

    fig_wr = go.Figure(go.Bar(
        x=agg['phase'].tolist(), y=agg['wpo'].tolist(), marker_color=pc,
        text=agg['wpo'].tolist(), textposition='outside',
        textfont=dict(size=15,family='DM Mono',color=TEXT),
        hovertemplate='<b>%{x}</b><br>Wickets/over: %{y}<extra></extra>'
    ))
    fig_wr.update_layout(
        title='Wicket Rate by Phase',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans,sans-serif',color=TEXT,size=12),
        margin=dict(t=44,b=30,l=10,r=10), height=340,
        yaxis=dict(gridcolor=BORDER,color=MUTED),
        xaxis=dict(gridcolor=BORDER,color=MUTED),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
    )

    fig_radar = go.Figure()
    for i, r in agg.iterrows():
        fig_radar.add_trace(go.Scatterpolar(
            r=[r['rr'], r['wpo']*10, r['fours']/r['balls']*6, r['sixes']/r['balls']*6, r['rr']],
            theta=['Run Rate','Wicket×10','Fours/Over','Sixes/Over','Run Rate'],
            fill='toself', name=r['phase'], line_color=pc[i],
            fillcolor=pc[i], opacity=0.3
        ))
    fig_radar.update_layout(
        title='Phase Radar',
        polar=dict(bgcolor='rgba(0,0,0,0)',
                   radialaxis=dict(gridcolor=BORDER,color=MUTED),
                   angularaxis=dict(gridcolor=BORDER,color=TEXT)),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans,sans-serif',color=TEXT,size=12),
        margin=dict(t=44,b=30,l=10,r=10), height=380,
        legend=dict(bgcolor='rgba(0,0,0,0)',orientation='h',y=1.1),
        showlegend=True,
    )

    over_s = d2.groupby(['inning','over']).agg(
        runs=('total_runs','sum'), balls=('ball','count')
    ).reset_index()
    over_s['rr'] = (over_s['runs']/over_s['balls']*6).round(2)
    pivot = over_s.pivot(index='inning',columns='over',values='rr').fillna(0)
    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values.tolist(),
        x=[f'Over {int(o)+1}' for o in pivot.columns],
        y=[f'Innings {int(i)}' for i in pivot.index],
        colorscale=[[0,CARD2],[0.4,PURPLE],[0.7,GOLD],[1,RED]],
        hovertemplate='%{x}<br>%{y}<br>RR: %{z:.2f}<extra></extra>',
    ))
    fig_heat.update_layout(
        title='Run Rate Heatmap — Innings × Over',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans,sans-serif',color=TEXT,size=12),
        margin=dict(t=44,b=60,l=80,r=10), height=220,
        xaxis=dict(color=MUTED), yaxis=dict(color=MUTED),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
    )

    return html.Div([
        row([chart_card(dcc.Graph(figure=fig_rr,   config=cfg())),
             chart_card(dcc.Graph(figure=fig_wr,   config=cfg())),
             chart_card(dcc.Graph(figure=fig_radar,config=cfg()))]),
        html.Div(style={'height':'16px'}),
        row([chart_card(dcc.Graph(figure=fig_heat,config=cfg()),flex=1)]),
    ])


# ── Load data ────────────────────────────────────────────────────────────────
base = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else '.'
_M = pd.read_csv(os.path.join(base,'data','IPL Matches.csv'))
_D = pd.read_csv(os.path.join(base,'data','IPL Ball-by-Ball.csv'))
_M['date']   = pd.to_datetime(_M['date'])
_M['season'] = _M['date'].dt.year
_D = _D.merge(_M[['id','season']], on='id')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run(debug=False, host='0.0.0.0', port=port) 