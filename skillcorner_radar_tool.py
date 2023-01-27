"""
SkillCorner Radar Tool
Liam Bailey - SkillCorner - 27/01/2023
This class inherits for the skillcorner client & genrates radar visualisations for off ball run data.
"""
from skillcorner.client import SkillcornerClient
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd

# Run types that match names returned by api (column names).
RUN_TYPES = ['cross_receiver_runs',
             'runs_in_behind',
             'runs_ahead_of_the_ball',
             'support_runs',
             'coming_short_runs',
             'dropping_off_runs',
             'pulling_half_space_runs',
             'pulling_wide_runs',
             'overlap_runs',
             'underlap_runs']

# Run types that match names required by api to request data.
REQUEST_RUN_TYPES = ['run_in_behind',
                     'run_ahead_of_the_ball',
                     'support_run',
                     'pulling_wide_run',
                     'coming_short_run',
                     'underlap_run',
                     'overlap_run',
                     'dropping_off_run',
                     'pulling_half_space_run',
                     'cross_receiver_run']


class SkillCornerRadarTool(SkillcornerClient):
    def __init__(self, username, password):
        super().__init__(username, password)
        self.off_ball_run_df = pd.DataFrame()
        self.ranked_position_df = pd.DataFrame()

    # Requests & Sets off ball run data grouped by 'player,competition,team,position'.
    def request_data(self, season_id, competition_ids, minutes, matches):
        for competition_id in competition_ids:
            print('Requesting data for competition_id ' + str(competition_id) + '...')
            api_response = super().get_in_possession_off_ball_runs({'season': season_id,
                                                                    'competition': competition_id,
                                                                    'playing_time__gte': minutes,
                                                                    'count_match__gte': matches,
                                                                    'run_type': ','.join(REQUEST_RUN_TYPES),
                                                                    'group_by': 'player,competition,team,position'})

            api_response = pd.DataFrame(api_response)

            print('Success! ' + str(len(api_response)) + ' players returned for competition_id ' + str(competition_id))

            self.off_ball_run_df = pd.concat([self.off_ball_run_df,
                                              api_response],
                                             ignore_index=True)

    # Returns off_ball_run_df.
    def get_off_ball_run_df(self):
        return self.off_ball_run_df

    # Filter off_ball_run_df by selected positions & calculates P90 values & percentiles for each run type.
    def filter_and_calculate_percentiles(self, position_selection):
        self.ranked_position_df = self.off_ball_run_df[self.off_ball_run_df['position'].isin(position_selection)]
        self.ranked_position_df = self.ranked_position_df.reset_index(drop=True)

        for run in RUN_TYPES:
            # Calculate P90 values for run type.
            self.ranked_position_df.loc[:, 'count_' + run + '_per_90'] = self.ranked_position_df[
                                                                             'count_' + run + '_per_match'] / (
                                                                                 self.ranked_position_df[
                                                                                     'minutes_played_per_match'] / 90)

            # Calculate percentile ranks for run type.
            self.ranked_position_df.loc[:, 'count_' + run + '_per_90_pct'] = self.ranked_position_df[
                                                                                 'count_' + run + '_per_90'].rank(
                pct=True) * 100

    # Returns ranked_position_df.
    def get_ranked_position_df(self):
        return self.ranked_position_df

    # Plots the radar for a given player (team & position required).
    def plot_radar(self, player_name, team_name, position, theme):

        # Retire player values from ranked_position_df.
        player_df = self.ranked_position_df[(self.ranked_position_df['player_name'] == player_name) &
                                            (self.ranked_position_df['team_name'] == team_name) &
                                            (self.ranked_position_df['position'] == position)]

        # If a single player could not be found exit.
        if len(player_df) != 1:
            print(
                player_name + ' (' + team_name + ' - ' + position + ') could not be found. Check your inputs & if the player meets the minutes/match requirements of the initial data request.')
            return None, None

        # Increasing or decreasing will affect all texts on the plot.
        text_multiplier = 1.45

        # Set plot theme.
        if theme == 'Dark':
            primary_colour = '#0C1B37'
            secondary_colour = "white"
        else:
            primary_colour = "white"
            secondary_colour = '#0C1B37'

        # Get the players P90 run counts.
        run_p90_metrics = ['count_' + type + '_per_90' for type in RUN_TYPES]
        values = player_df.iloc[0][run_p90_metrics].astype(float).values.tolist()
        # Get the player's percentile ranks for run counts.
        run_pct_metrics = ['count_' + type + '_per_90_pct' for type in RUN_TYPES]
        values_pct = player_df.iloc[0][run_pct_metrics].astype(float).values.tolist()

        # Set the x position & width for each of the bars.
        width = 6.28319 / len(RUN_TYPES)
        theta = np.linspace(0.0, 2 * np.pi, len(RUN_TYPES), endpoint=False)

        # Plot setup.
        fig = plt.figure(figsize=(10, 10))
        ax = plt.subplot(projection='polar')
        fig.patch.set_facecolor(primary_colour)
        ax.set_facecolor(primary_colour)
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        # Bars for main green section of wedge with alpha=0.95.
        ax.bar(theta,
               values_pct,
               width=width,
               bottom=10,
               color='#80CBA2',
               edgecolor=secondary_colour,
               lw=1.25,
               zorder=3,
               alpha=0.95)

        # Bars for outline of wedge with alpha=1.
        ax.bar(theta,
               values_pct,
               width=width,
               bottom=10,
               fill=False,
               edgecolor=secondary_colour,
               lw=1.25,
               zorder=3)

        ax.set_ylim(0, 120)

        # Adding ytick labels & Adjusting their position on axis.
        ax.set_yticks([35, 60, 85, 110])
        ax.set_yticklabels(['', '', '', ''])

        pos = ax.get_rlabel_position()
        ax.set_rlabel_position(pos + 106.5)

        y_pos = [35, 60, 85]
        labels = ['25', '50', '75']
        for y, l in zip(y_pos, labels):
            ax.text(2.19911,
                    y,
                    l,
                    ha='center',
                    va='center',
                    size=8 * text_multiplier,
                    color=secondary_colour,
                    zorder=8,
                    bbox={'boxstyle': 'round',
                          'facecolor': primary_colour,
                          'edgecolor': secondary_colour,
                          'lw': 1.25})

        ax.text(2.19911,
                110,
                '100th\nPercentile',
                ha='left',
                va='center',
                size=8 * text_multiplier,
                color=secondary_colour,
                zorder=8,
                bbox={'boxstyle': 'round',
                      'color': primary_colour,
                      'lw': 1.25})

        # Setting the x ticks to position of the bars & adding text labels.
        ax.set_xticks(theta)
        ax.set_xticklabels(['Cross receiver run',
                            'Runs in behind',
                            'Run ahead of the ball',
                            'Support',
                            'Coming short',
                            'Dropping off',
                            'Pulling half space',
                            'Pulling wide',
                            'Overlap',
                            'Underlap'],
                           size=12 * text_multiplier,
                           color=secondary_colour)

        # Rotating xtick labels & add highlight for key run types.
        labels = []
        for tick_label, run_type, angle in zip(ax.get_xticklabels(), RUN_TYPES, theta):
            x, y = tick_label.get_position()
            lab = ax.text(x, y, tick_label.get_text(), transform=tick_label.get_transform(),
                          ha=tick_label.get_ha(), va=tick_label.get_va())

            # If the label is on the bottom half rotate to make it readable.
            if (90 >= (angle * 180 / np.pi) >= 0) | (360 >= (angle * 180 / np.pi) >= 270):
                lab.set_rotation(0 - (angle * 180 / np.pi))
            else:
                lab.set_rotation(180 - (angle * 180 / np.pi))

            lab.set_y(0.08)
            lab.set_fontproperties({'weight': 'bold', 'size': 10 * text_multiplier})
            lab.set_horizontalalignment('center')

            # If the median player in the comparison group does at least 1 per 90 highlight the label.
            if self.ranked_position_df['count_' + run_type + '_per_90'].median() >= 1:
                lab.set_bbox({'boxstyle': 'round',
                              'facecolor': secondary_colour}),
                lab.set_color(primary_colour)

            else:
                lab.set_color(secondary_colour)

            labels.append(lab)

        ax.set_xticklabels([])

        # Adding run count per 90 below axis labels.
        for value_pct, value, theta in zip(values_pct, values, theta):
            text = ax.text(theta,
                           105,
                           str(round(value, 1)) + ' Runs P90',
                           ha='center',
                           va='center',
                           fontweight='bold',
                           color=secondary_colour,
                           fontsize=8 * text_multiplier,
                           zorder=5,
                           path_effects=[pe.withStroke(linewidth=3,
                                                       foreground=primary_colour,
                                                       alpha=1)])

            # If the text is on the bottom half rotate to make it readable.
            if (90 >= (theta * 180 / np.pi) >= 0) | (360 >= (theta * 180 / np.pi) >= 270):
                text.set_rotation(0 - (theta * 180 / np.pi))
            else:
                text.set_rotation(180 - (theta * 180 / np.pi))

        # Style axis.
        ax.xaxis.grid(False)
        ax.yaxis.grid(color=secondary_colour, linestyle='--', linewidth=1)
        ax.spines["start"].set_color("none")
        ax.spines["polar"].set_color("none")

        # Adding plot title.
        ax.text(0,
                138,
                'Off-Ball Attacking Run Rankings',
                size=18 * text_multiplier,
                color=secondary_colour,
                fontweight='bold',
                ha='center')

        # Adding plot subtitle with player information.
        ax.text(0,
                128,
                player_df['player_name'].iloc[0] + ' | ' + player_df['team_name'].iloc[0] + ' | ' + player_df['position'].iloc[0],
                size=14 * text_multiplier,
                color=secondary_colour,
                ha='center')

        # Adding plot description information.
        ax.text(3.14159,
                128,
                'Length represents the percentile of run type per 90 minutes',
                ha='center',
                va='center',
                color=secondary_colour,
                fontsize=8 * text_multiplier)

        ax.text(3.14159,
                137,
                'Run type typical for position selection',
                ha='center',
                va='center',
                color=primary_colour,
                fontsize=8 * text_multiplier,
                fontweight='bold',
                bbox={'boxstyle': 'round',
                      'facecolor': secondary_colour})

        plt.tight_layout()

        return fig, ax

    # Runs player ranking & radar generation.
    def rank_players_generate_radar(self, player_name, team_name, player_posisition, position_to_compare, theme):
        self.filter_and_calculate_percentiles(position_to_compare)
        print(str(len(self.get_ranked_position_df())) + ' players in position selection: ' + ','.join(
            position_to_compare))
        return self.plot_radar(player_name, team_name, player_posisition, theme)
    